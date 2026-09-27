"""
Módulo del Simulador Biofísico del Gemelo Digital Agronómico
Definición de clase limpia y desacoplada para serialización y ejecución modular.
"""

import numpy as np

class AgronomicDigitalTwinSimulator:
    """
    Simulador biofísico de balance hídrico, asimilación por radiación y dinámica de nitrógeno
    basado en principios mecanicistas tipo APSIM / DSSAT / FAO AquaCrop.
    """
    def __init__(self, rue=1.56, kc_max=0.80, hi_base=0.47, leach_factor=0.18):
        self.rue = rue                 # Eficiencia en el Uso de la Radiación (g/MJ)
        self.kc_max = kc_max           # Coeficiente máximo de cultivo para transpiración
        self.hi_base = hi_base         # Índice de cosecha potencial base
        self.leach_factor = leach_factor # Coeficiente de partición de lixiviación por exceso de percolación

    def simulate_plot(self, rain_mm, irrig_mm, n_applied_kg, temp_mean_c, rad_mean_mj, clay_pct, om_pct):
        # 1. Balance Hídrico Estacional (Precipitación acumulada de ciclo completo ~ 3.5x lluvia mensual)
        water_input_mm = rain_mm * 3.5 + irrig_mm
        # Capacidad de retención de agua disponible en función de arcilla y materia orgánica
        awc_mm = (0.15 + 0.002 * clay_pct + 0.015 * om_pct) * 800.0  # Capacidad en zona radicular (80 cm)
        
        # Evapotranspiración potencial estimada estacional (ciclo 120 días)
        et0_est = max(380.0, 15.0 * temp_mean_c + 12.0 * rad_mean_mj)
        etc_pot = et0_est * self.kc_max
        
        # Agua transpirada / evapotranspirada real
        water_avail_ratio = min(1.3, water_input_mm / (etc_pot + 1e-3))
        water_stress = np.clip(water_avail_ratio, 0.25, 1.0)
        
        # Uso consuntivo de agua (m³/ha): 1 mm = 10 m³/ha
        water_use_m3 = min(water_input_mm, etc_pot * 1.1) * 10.0
        
        # Exceso de agua percolable más allá de la capacidad de campo
        drainage_mm = max(0.0, water_input_mm - awc_mm - etc_pot * 0.7)

        # 2. Factor de Temperatura (Óptimo maíz 24-28 °C)
        t_stress = np.exp(-0.5 * ((temp_mean_c - 25.5) / 6.0)**2)
        
        # 3. Factor de Nitrógeno
        # Mineralización estimada del suelo a partir de materia orgánica
        n_mineralized = om_pct * 25.0
        n_total_avail = n_applied_kg + n_mineralized
        # Demanda de N para rendimiento potencial de maíz
        n_stress = 1.0 - np.exp(-n_total_avail / 120.0)

        # 4. Acumulación de Biomasa Aérea (ton/ha)
        # PAR acumulada ~ 0.5 * Radiación total estacional (120 días de ciclo)
        par_cum_mj = 0.5 * rad_mean_mj * 120.0
        biomass_pot = (par_cum_mj * self.rue) / 100.0 # g/m² a ton/ha (/100)
        biomass_sim = biomass_pot * water_stress * t_stress * n_stress
        biomass_sim = np.clip(biomass_sim, 2.0, 32.0)

        # 5. Índice de Cosecha y Rendimiento de Grano (ton/ha)
        # El estrés hídrico durante floración/llenado deprime el HI
        hi_actual = self.hi_base * (0.65 + 0.35 * water_stress) * (0.8 + 0.2 * n_stress)
        hi_actual = np.clip(hi_actual, 0.15, 0.55)
        yield_sim = biomass_sim * hi_actual

        # 6. Lixiviación de Nitrógeno (kg N/ha)
        n_residual = max(0.0, n_total_avail - biomass_sim * 12.0)
        n_leached = (drainage_mm / (drainage_mm + 100.0)) * n_residual * self.leach_factor + 0.05 * n_applied_kg * (water_input_mm / 600.0)
        n_leached = np.clip(n_leached, 0.5, 95.0)

        return yield_sim, water_use_m3, biomass_sim, n_leached

    def simulate_dataset(self, df):
        n = len(df)
        y_sim = np.zeros(n)
        w_sim = np.zeros(n)
        b_sim = np.zeros(n)
        nl_sim = np.zeros(n)

        rain = df['rainfall_mm'].fillna(df['rainfall_mm'].median()).values
        irrig = df['irrigation_mm'].fillna(0.0).values
        n_app = df['nitrogen_kg_ha'].fillna(df['nitrogen_kg_ha'].median()).values
        temp = df['temperature_mean_c'].fillna(df['temperature_mean_c'].median()).values
        rad = df['radiation_mean'].fillna(df['radiation_mean'].median()).values
        clay = df['clay_pct'].fillna(df['clay_pct'].median()).values
        om = df['soil_organic_matter_pct'].fillna(df['soil_organic_matter_pct'].median()).values

        for i in range(n):
            y_s, w_s, b_s, nl_s = self.simulate_plot(
                rain[i], irrig[i], n_app[i], temp[i], rad[i], clay[i], om[i]
            )
            y_sim[i] = y_s
            w_sim[i] = w_s
            b_sim[i] = b_s
            nl_sim[i] = nl_s

        return y_sim, w_sim, b_sim, nl_sim
