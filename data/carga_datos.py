"""
Módulo de ingesta de datos: automática + manual
Formatos soportados: CSV, Parquet, GeoJSON/Shapefile
"""
import streamlit as st
import pandas as pd
import geopandas as gpd
from pathlib import Path
from config.settings import RUTA_DATOS
from config.i18n import t

def cargar_archivo_subido(archivo_subido):
    """Carga archivo según extensión y devuelve DataFrame/GeoDataFrame"""
    if not archivo_subido:
        return None
    
    nombre = archivo_subido.name.lower()
    try:
        if nombre.endswith(".csv"):
            df = pd.read_csv(archivo_subido)
            st.success(f"✅ CSV cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
            return df
        elif nombre.endswith(".parquet"):
            df = pd.read_parquet(archivo_subido)
            st.success(f"✅ Parquet cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
            return df
        elif nombre.endswith((".geojson", ".json")):
            gdf = gpd.read_file(archivo_subido)
            st.success(f"✅ GeoJSON cargado: {gdf.shape[0]} geometrías")
            return gdf
        elif nombre.endswith(".zip"):
            gdf = gpd.read_file(archivo_subido)
            st.success(f"✅ Shapefile (ZIP) cargado: {gdf.shape[0]} geometrías")
            return gdf
        else:
            st.warning(f"⚠️ Formato no soportado: {nombre}")
            return None
    except Exception as e:
        st.error(f"❌ Error al cargar {nombre}: {str(e)}")
        return None

def guardar_datos(df, nombre_archivo):
    """Guarda datos en carpeta de datos del proyecto"""
    ruta = RUTA_DATOS / nombre_archivo
    if nombre_archivo.endswith(".csv"):
        df.to_csv(ruta, index=False)
    elif nombre_archivo.endswith(".parquet"):
        df.to_parquet(ruta, index=False)
    elif nombre_archivo.endswith((".geojson", ".json")):
        df.to_file(ruta, driver="GeoJSON")
    st.success(f"💾 Guardado en: {ruta}")
    return ruta

def listar_archivos_guardados():
    """Lista los archivos disponibles en la carpeta de datos"""
    if not RUTA_DATOS.exists():
        return []
    return [f.name for f in RUTA_DATOS.iterdir() if f.is_file()]

def interfaz_carga_datos():
    """Componente Streamlit para cargar datos manualmente"""
    st.header("📥 " + t("cargar_datos_ia", st.session_state.idioma))
    archivo = st.file_uploader(
        t("subir_archivo", st.session_state.idioma),
        type=["csv", "parquet", "geojson", "zip"],
        help="CSV, Parquet, GeoJSON o Shapefile comprimido en ZIP"
    )
    if archivo:
        df = cargar_archivo_subido(archivo)
        if df is not None:
            st.dataframe(df.head(10), use_container_width=True)
            if st.checkbox("💾 Guardar en carpeta de datos"):
                ruta_guardado = st.text_input("Nombre del archivo", archivo.name)
                if st.button("Guardar") and ruta_guardado:
                    guardar_datos(df, ruta_guardado)
    
    # Mostrar archivos disponibles
    archivos = listar_archivos_guardados()
    if archivos:
        st.subheader("📁 Archivos disponibles")
        st.write(", ".join(archivos))
    
    return archivo
