import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
from config.settings import CONFIG_DB

def obtener_conexion():
    try:
        return psycopg2.connect(**CONFIG_DB)
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def probar_conexion():
    conn = obtener_conexion()
    if conn:
        conn.close()
        return True
    return False

def ejecutar_consulta(sql, parametros=None):
    conn = obtener_conexion()
    if not conn: return []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, parametros or ())
            conn.commit()
            if cur.description:
                return [dict(fila) for fila in cur.fetchall()]
        return []
    finally:
        conn.close()

def obtener_zonas_por_campo(campo_id):
    """Consulta geoespacial: devuelve zonas de manejo de un campo"""
    sql = """
    SELECT z.zona_id, z.codigo, z.ndvi_actual, z.estres_hidrico_pct,
           z.rendimiento_esperado_ton_ha, ST_AsGeoJSON(z.geometria) as geojson
    FROM zonas_manejo z
    WHERE z.campo_id = %s
    """
    return ejecutar_consulta(sql, (campo_id,))

def insertar_alerta(zona_id, tipo, probabilidad, semanas, recomendacion):
    """Registra una nueva alerta en la base de datos"""
    sql = """
    INSERT INTO alertas (zona_id, tipo, probabilidad_riesgo_pct, semanas_anticipacion, recomendacion)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING alerta_id
    """
    return ejecutar_consulta(sql, (zona_id, tipo, probabilidad, semanas, recomendacion))
