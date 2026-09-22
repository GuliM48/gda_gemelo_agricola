# 🌾 GDA — Gemelo de Decisión Agronómica

> **Gemelo Digital 3D de Campos Agrícolas con IA**  
> Simulación basada en agentes (Mesa) + Alerta Temprana con umbral ≥70% + Visualización 3D + Modelado Predictivo

---

## ✅ Características Principales

- 🧠 **Simulación ABM**: Cada zona de manejo = agente independiente; reglas basadas en FAO 56
- 🚨 **Alerta Temprana**: Predice riesgo de pérdida con 4–8 semanas de anticipación; umbral crítico ≥70%
- 📊 **Motor IA**: EDA automático, modelos RF/XGBoost, validación espacial, explicabilidad SHAP
- 🗺️ **Visualización 3D**: Colores por NDVI + zonas en alerta resaltadas en ROJO
- 📄 **Reportes**: Exportación PDF / Word / Excel integrada
- 🌐 **Bilingüe**: Español / Inglés con selector centralizado
- 🔒 **Control de acceso**: 4 roles con permisos diferenciados
- 🗄️ **PostGIS**: Base de datos espacial completa con esquema relacional
- 🤖 **Chatbot flotante**: Asistente virtual con soporte de voz (Web Speech API)

---

## 📋 Requisitos Técnicos

- Python 3.10+
- PostgreSQL 14+ con extensión **PostGIS 3.0+**
- 4 GB RAM mínimo
- Navegador moderno (Chrome, Firefox, Edge)

---

## 🚀 Instalación Paso a Paso

### 1. Preparar entorno Python

```bash
cd gda_gemelo_agricola
python3.10 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install --upgrade pip setuptools wheel
pip install -r requisitos.txt
```

### 2. Instalar PostgreSQL + PostGIS

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install postgresql postgresql-contrib postgis

# Windows: descargar desde postgresql.org + habilitar PostGIS en Stack Builder
```

### 3. Crear base de datos y usuario

```sql
-- Ejecutar en consola psql o pgAdmin
CREATE DATABASE gda_gemelo;
\c gda_gemelo
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
CREATE USER gda_usuario WITH PASSWORD 'pon_tu_contraseña_segura';
GRANT ALL PRIVILEGES ON DATABASE gda_gemelo TO gda_usuario;
GRANT ALL ON SCHEMA public TO gda_usuario;
```

### 4. Cargar esquema de base de datos

```bash
psql -U gda_usuario -d gda_gemelo -f data/esquema.sql
```

### 5. Configurar conexión

Edita `config/settings.py` con tus credenciales reales:

```python
CONFIG_DB = {
    "host": "localhost",
    "port": 5432,
    "database": "gda_gemelo",
    "user": "gda_usuario",
    "password": "tu_contraseña_segura"
}
```

### 6. Ejecutar la aplicación

```bash
streamlit run app.py
```

Abrir en navegador: **http://localhost:8501**

---

## 📁 Estructura del Proyecto

```
gda_gemelo_agricola/
├── app.py                      # Punto de entrada Streamlit
├── config/
│   ├── settings.py             # Variables globales, umbrales científicos
│   ├── i18n.py                 # Traducciones ES/EN centralizadas
│   └── roles.py                # Matriz de permisos por rol
├── modules/
│   ├── gemelo.py               # Simulación ABM + Alertas + Visualización 3D
│   ├── ia_engine.py            # EDA, modelos ML, validación, SHAP
│   ├── alertas.py              # Módulo independiente de alertas
│   ├── reportes.py             # Generación PDF / Word / Excel
│   └── chatbot.py              # Asistente flotante con voz
├── data/
│   ├── database.py             # Conexión y consultas PostGIS
│   ├── esquema.sql             # Esquema completo + datos demo
│   └── carga_datos.py          # Ingesta automática y manual
├── assets/
│   ├── iconos/                 # Carpeta para iconos personalizados
│   └── estilos.css             # Estilos UI personalizados
├── requisitos.txt              # Dependencias Python
└── README.md                   # Esta guía
```

---

## ⚙️ Parámetros Científicos Configurables

Ubicados en `config/settings.py`:

| Parámetro                      | Valor                                             | Descripción                                |
| ------------------------------ | ------------------------------------------------- | ------------------------------------------ |
| `UMBRAL_ALERTA_ROJA_PCT`       | 70.0                                              | Umbral de activación de alerta prioritaria |
| `SEMANAS_ANTICIPACION_DEFECTO` | 6                                                 | Anticipación por defecto (rango 4–8)       |
| `PESOS_ALERTA`                 | NDVI 35%, Hídrico 35%, Nutricional 15%, Clima 15% | Ponderación del modelo de riesgo           |
| `COEFICIENTES_KY`              | Hídrico 0.65, Nutricional 0.35                    | Coeficientes FAO de respuesta al estrés    |
| `DURACION_SIMULACION_DIAS`     | 135                                               | Duración ciclo de cultivo                  |

---

## 🔑 Roles y Permisos

| Rol               | Simulación | Motor IA | Reportes | Gestión Usuarios |
| ----------------- | :--------: | :------: | :------: | :--------------: |
| **Administrador** |     ✅     |    ✅    |    ✅    |        ✅        |
| **Agrónomo**      |     ✅     |    ✅    |    ✅    |        ❌        |
| **Agricultor**    |     ✅     |    ❌    |    ✅    |        ❌        |
| **Visor**         |     ❌     |    ❌    |    ❌    |        ❌        |

---

## 🧪 Fundamento Científico

### Modelo de Estrés Hídrico

- Basado en **FAO 56**: balance hídrico diario + coeficientes de cultivo (Kc) por fase fenológica
- Umbral de estrés: fracción de agua útil < 50%
- Coeficiente de respuesta Ky = 0.65 para estrés hídrico

### Modelo de Alerta Temprana

- Combinación lineal ponderada de 4 factores agronómicamente validados
- Umbral de decisión: **≥ 70% probabilidad** → intervención recomendada
- Anticipación: 4–8 semanas antes del impacto en rendimiento final

### Validación

- Validación cruzada espacial para evitar fuga de datos geográficos
- Métricas: R², RMSE, MAE
- Explicabilidad: Importancia por permutación + valores SHAP

---

## 📚 Referencias Clave

1. **FAO 56** — Allen et al. (1998) — Evapotranspiración del cultivo
2. **Mesa** — Framework de modelado basado en agentes
3. **SoilGrids** — Hengl et al. (2017) — Datos de suelo globales a 250m
4. **SHAP** — Lundberg & Lee (2017) — Explicabilidad unificada de modelos
5. **Validación cruzada espacial** — Roberts et al. (2017)

---

## 🔧 Solución de Problemas

| Problema                   | Solución                                                                   |
| -------------------------- | -------------------------------------------------------------------------- |
| Error conexión BD          | Verificar credenciales en `config/settings.py`; servicio PostgreSQL activo |
| Falta PostGIS              | Ejecutar `CREATE EXTENSION postgis;` en la base de datos                   |
| Error de dependencias      | Actualizar pip: `pip install --upgrade pip` antes de instalar              |
| Chatbot de voz no funciona | Usar navegador Chrome/Edge; Web Speech API no soportada en Firefox         |

---

## 📄 Licencia

Proyecto de investigación y desarrollo. Uso académico y profesional permitido.

---

## 🚀 Prueba Rápida

Si no tienes PostgreSQL configurado, la aplicación aún funciona en modo demostración:

```bash
streamlit run app.py
```

Los módulos de simulación, IA, alertas y reportes funcionan con datos sintéticos de ejemplo.
