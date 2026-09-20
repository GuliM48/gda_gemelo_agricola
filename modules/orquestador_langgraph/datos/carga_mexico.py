"""
Generación de datos CY-Bench sintéticos para las 3 regiones de México.
Crea datos de rendimiento, clima, suelo y coordenadas para validación.
"""
import numpy as np
import pandas as pd
import os

np.random.seed(42)

ESTADOS_REGIONES = {
    "NOROESTE": {
        "estados": [
            {"nombre": "Sinaloa", "codigo": "MX25", "lat": 24.8, "lon": -107.3},
            {"nombre": "Sonora", "codigo": "MX26", "lat": 29.0, "lon": -111.0},
        ]
    },
    "CENTRO-OCCIDENTE": {
        "estados": [
            {"nombre": "Jalisco", "codigo": "MX14", "lat": 20.7, "lon": -103.3},
            {"nombre": "Guanajuato", "codigo": "MX11", "lat": 20.6, "lon": -101.5},
        ]
    },
    "SURESTE": {
        "estados": [
            {"nombre": "Chiapas", "codigo": "MX07", "lat": 16.7, "lon": -92.6},
            {"nombre": "Tabasco", "codigo": "MX27", "lat": 17.8, "lon": -92.0},
        ]
    },
}

ANIOS_SIMULADOS = list(range(2015, 2024))


def generar_datos_maiz() -> dict:
    """Genera DataFrames sintéticos CY-Bench para las 3 regiones."""
    datos = {}
    for region, info in ESTADOS_REGIONES.items():
        rendimientos = []
        meteo = []
        suelo = []
        ubicaciones = []
        lut = []

        params_suelo = {
            "NOROESTE": {"awc": 0.32, "densidad": 1.45, "textura": "franco-arcilloso", "N_disponible": 180, "pH": 6.8},
            "CENTRO-OCCIDENTE": {"awc": 0.28, "densidad": 1.50, "textura": "franco", "N_disponible": 150, "pH": 6.5},
            "SURESTE": {"awc": 0.22, "densidad": 1.55, "textura": "arcilloso", "N_disponible": 100, "pH": 5.5},
        }

        rendimiento_base = {"NOROESTE": 8.5, "CENTRO-OCCIDENTE": 6.2, "SURESTE": 4.1}
        precip_base = {"NOROESTE": 350, "CENTRO-OCCIDENTE": 750, "SURESTE": 1500}

        for estado in info["estados"]:
            for anio in ANIOS_SIMULADOS:
                ancho = 2
                rend_base = rendimiento_base[region] + np.random.normal(0, 0.8)
                rend = max(1.0, rend_base + np.random.normal(0, 0.5) * (anio - 2015) * 0.08)
                rendimientos.append({
                    "Area": estado["nombre"],
                    "Item": "Maize",
                    "Year": anio,
                    "hg/ha_yield": round(rend * 1000, 1),
                    "average_rain_fall_mm_per_year": max(50, precip_base[region] + np.random.normal(0, 50)),
                    "avg_temp": round(22 + np.random.normal(0, 1.5) if region == "SURESTE" else 24 + np.random.normal(0, 2), 2),
                })

                for mes in range(1, 13):
                    meteo.append({
                        "Area": estado["nombre"],
                        "Year": anio,
                        "Month": mes,
                        "precip_mm": max(0, np.random.normal(
                            precip_base[region] / 12,
                            precip_base[region] / 12 * 0.5
                        )),
                        "tmax_c": round(28 + np.random.normal(0, 4) - (5 if mes in [12, 1, 2] else 0), 1),
                        "tmin_c": round(14 + np.random.normal(0, 3) - (3 if mes in [12, 1, 2] else 0), 1),
                        "radiacion_mj_m2": round(18 + np.random.normal(0, 3), 1),
                    })

                for anio_y in ANIOS_SIMULADOS:
                    suelo.append({
                        "Area": estado["nombre"],
                        "Year": anio_y,
                        "awc": params_suelo[region]["awc"],
                        "densidad_bulk": params_suelo[region]["densidad"],
                        "textura": params_suelo[region]["textura"],
                        "N_disponible": params_suelo[region]["N_disponible"],
                        "pH": params_suelo[region]["pH"],
                    })

                ubicaciones.append({
                    "Area": estado["nombre"],
                    "Code": estado["codigo"],
                    "Latitude": estado["lat"],
                    "Longitude": estado["lon"],
                })

                lut.append({
                    "Code": estado["codigo"],
                    "Name": estado["nombre"],
                    "Region": region,
                })

        datos[region] = {
            "yield_maize": pd.DataFrame(rendimientos),
            "meteo": pd.DataFrame(meteo),
            "soil": pd.DataFrame(suelo),
            "location": pd.DataFrame(ubicaciones),
            "LUT_state": pd.DataFrame(lut),
        }

    return datos


def guardar_datos_CY_Bench(datos: dict, output_dir: str = "data") -> None:
    """Guarda los datos sintéticos en CSV."""
    os.makedirs(output_dir, exist_ok=True)
    mapping = {
        "yield_maize_MX": "yield_maize",
        "meteo_maize_MX": "meteo_maize",
        "soil_maize_MX": "soil_maize",
        "location_maize_MX": "location_maize",
        "LUT_state": "LUT_state",
    }
    for region, dfs in datos.items():
        region_dir = os.path.join(output_dir, region.lower())
        os.makedirs(region_dir, exist_ok=True)
        for key, df in dfs.items():
            filename = f"{mapping.get(key, key)}_MX.csv"
            df.to_csv(os.path.join(region_dir, filename), index=False)


if __name__ == "__main__":
    datos = generar_datos_maiz()
    guardar_datos_CY_Bench(datos, "data")
    print("Datos CY-Bench sintéticos generados en data/")
    for region, dfs in datos.items():
        print(f"\n{region}:")
        for key, df in dfs.items():
            print(f"  {key}: {len(df)} filas")