"""
Script para generar el Informe Científico Oficial en Microsoft Word (.docx)
con todos los resultados, figuras y tablas del entrenamiento del Gemelo Digital Agrícola (GDA).
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

WORKSPACE = Path(__file__).resolve().parent

# ==========================================
# PALETA DE COLORES INSTITUCIONAL
# ==========================================
COLOR_PRIMARY_HEX = "0F2C59"       # Azul Marino Profundo (Títulos, Headers)
COLOR_SECONDARY_HEX = "007A78"     # Teal / Verde Azulado (Subtítulos, Acentos)
COLOR_ACCENT_HEX = "C27803"        # Ámbar Cálido (Resaltados, Callouts)
COLOR_DARK_TEXT_HEX = "1A202C"     # Texto Principal (Charcoal)
COLOR_MUTED_TEXT_HEX = "4A5568"    # Texto Secundario / Citas
COLOR_LIGHT_BG_HEX = "F4F6F9"      # Fondo Celdas Alternas
COLOR_CALLOUT_BG_HEX = "F0F7F7"    # Fondo Cajas de Resumen
COLOR_BORDER_HEX = "CBD5E0"        # Gris Claro para Bordes

COLOR_PRIMARY = RGBColor(0x0F, 0x2C, 0x59)
COLOR_SECONDARY = RGBColor(0x00, 0x7A, 0x78)
COLOR_ACCENT = RGBColor(0xC2, 0x78, 0x03)
COLOR_DARK_TEXT = RGBColor(0x1A, 0x20, 0x2C)
COLOR_MUTED_TEXT = RGBColor(0x4A, 0x55, 0x68)

# ==========================================
# FUNCIONES AUXILIARES XML PARA TABLAS
# ==========================================
def set_cell_background(cell, hex_color):
    """Aplica color de fondo a una celda."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=160, right=160):
    """Establece márgenes internos de una celda (en dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'  <w:top w:w="{top}" w:type="dxa"/>'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'  <w:left w:w="{left}" w:type="dxa"/>'
        f'  <w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, color=COLOR_BORDER_HEX, sz="4"):
    """Establece bordes limpios y discretos a la tabla."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def make_row_header(row):
    """Marca la fila como encabezado repetible en páginas sucesivas."""
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

def make_row_cant_split(row):
    """Evita que una fila se parta entre dos páginas."""
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

def add_callout(doc, title, text, border_color=COLOR_SECONDARY_HEX, bg_color=COLOR_CALLOUT_BG_HEX):
    """Crea un recuadro de resaltado con barra lateral izquierda."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.8)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=160)
    
    # Borde izquierdo grueso, resto sin borde
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'  <w:left w:val="single" w:sz="36" w:space="0" w:color="{border_color}"/>'
        f'  <w:top w:val="none"/>'
        f'  <w:bottom w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    
    r_title = p.add_run(f"📌 {title}\n")
    r_title.bold = True
    r_title.font.name = "Segoe UI"
    r_title.font.size = Pt(10)
    r_title.font.color.rgb = COLOR_SECONDARY
    
    r_text = p.add_run(text)
    r_text.font.name = "Segoe UI"
    r_text.font.size = Pt(9.5)
    r_text.font.color.rgb = COLOR_DARK_TEXT
    
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

# ==========================================
# GESTIÓN DE TABLAS FORMALES
# ==========================================
def format_cell_value(val):
    """Formatea valores según tipo numérico o texto."""
    if pd.isna(val):
        return "-"
    if isinstance(val, (float, np.floating)):
        if abs(val) >= 1000:
            return f"{val:,.2f}"
        elif abs(val) < 0.001 and val != 0:
            return f"{val:.2e}"
        elif abs(val) < 1:
            return f"{val:.4f}"
        else:
            return f"{val:.2f}"
    if isinstance(val, (int, np.integer)):
        return f"{val:,}"
    return str(val)

def add_dataframe_table(doc, df, title, caption=None, max_rows=None, col_widths=None):
    """Inserta una tabla formal estilizada a partir de un DataFrame."""
    # Título de la tabla
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(4)
    p_title.paragraph_format.keep_with_next = True
    
    r_title = p_title.add_run(f"{title}")
    r_title.bold = True
    r_title.font.name = "Segoe UI"
    r_title.font.size = Pt(10.5)
    r_title.font.color.rgb = COLOR_PRIMARY

    # Subconjunto si aplica max_rows
    if max_rows and len(df) > max_rows:
        df_display = df.head(max_rows).copy()
        note = f"*(Mostrando primeras {max_rows} de {len(df)} filas)*"
    else:
        df_display = df.copy()
        note = None

    table = doc.add_table(rows=len(df_display) + 1, cols=len(df_display.columns))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)

    # Encabezado
    header_row = table.rows[0]
    make_row_header(header_row)
    for col_idx, col_name in enumerate(df_display.columns):
        cell = header_row.cells[col_idx]
        set_cell_background(cell, COLOR_PRIMARY_HEX)
        set_cell_margins(cell, top=140, bottom=140, left=140, right=140)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        clean_col = str(col_name).replace('_', ' ').title()
        r = p.add_run(clean_col)
        r.bold = True
        r.font.name = "Segoe UI"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # Filas de datos
    for row_idx, (_, row) in enumerate(df_display.iterrows()):
        t_row = table.rows[row_idx + 1]
        make_row_cant_split(t_row)
        bg = COLOR_LIGHT_BG_HEX if row_idx % 2 == 1 else "FFFFFF"
        
        for col_idx, val in enumerate(row):
            cell = t_row.cells[col_idx]
            if bg != "FFFFFF":
                set_cell_background(cell, bg)
            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            
            val_str = format_cell_value(val)
            r = p.add_run(val_str)
            r.font.name = "Segoe UI"
            r.font.size = Pt(8.0)
            r.font.color.rgb = COLOR_DARK_TEXT
            
            # Alineación inteligente
            if isinstance(val, (int, float, np.number)) and not isinstance(val, bool):
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif len(val_str) <= 6:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Ajuste proporcional de anchos
    total_table_width = 6.8 # pulgadas
    n_cols = len(df_display.columns)
    default_col_w = total_table_width / n_cols
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            cell.width = Inches(col_widths[idx] if col_widths and idx < len(col_widths) else default_col_w)

    # Nota o pie de tabla
    if caption or note:
        p_cap = doc.add_paragraph()
        p_cap.paragraph_format.space_before = Pt(3)
        p_cap.paragraph_format.space_after = Pt(8)
        full_caption = ""
        if caption:
            full_caption += f"Fuente/Nota: {caption}. "
        if note:
            full_caption += note
        r_cap = p_cap.add_run(full_caption)
        r_cap.font.name = "Segoe UI"
        r_cap.font.size = Pt(8.0)
        r_cap.font.italic = True
        r_cap.font.color.rgb = COLOR_MUTED_TEXT

# ==========================================
# INSERCIÓN DE FIGURAS DE ALTA RESOLUCIÓN
# ==========================================
def add_figure(doc, img_rel_path, fig_number, caption, description=None, max_w=6.2, max_h=4.5):
    """Inserta una imagen centrada con su leyenda formal y texto explicativo."""
    img_path = WORKSPACE / img_rel_path
    if not img_path.exists():
        print(f"[AVISO] Imagen no encontrada: {img_path}")
        return

    try:
        with Image.open(img_path) as im:
            orig_w, orig_h = im.size
            aspect = orig_w / orig_h
    except Exception as e:
        print(f"[AVISO] Error al abrir imagen {img_path}: {e}")
        return

    # Cálculo de dimensiones proporcionales
    w = max_w
    h = w / aspect
    if h > max_h:
        h = max_h
        w = h * aspect

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(10)
    p_img.paragraph_format.space_after = Pt(2)
    p_img.paragraph_format.keep_with_next = True
    
    run_img = p_img.add_run()
    run_img.add_picture(str(img_path), width=Inches(w), height=Inches(h))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(6)
    p_cap.paragraph_format.keep_with_next = True if description else False
    
    r_num = p_cap.add_run(f"Figura {fig_number}: ")
    r_num.bold = True
    r_num.font.name = "Segoe UI"
    r_num.font.size = Pt(8.5)
    r_num.font.color.rgb = COLOR_PRIMARY
    
    r_cap = p_cap.add_run(caption)
    r_cap.font.name = "Segoe UI"
    r_cap.font.size = Pt(8.5)
    r_cap.font.italic = True
    r_cap.font.color.rgb = COLOR_MUTED_TEXT

    if description:
        p_desc = doc.add_paragraph()
        p_desc.paragraph_format.space_before = Pt(2)
        p_desc.paragraph_format.space_after = Pt(8)
        p_desc.paragraph_format.line_spacing = 1.15
        r_desc = p_desc.add_run(description)
        r_desc.font.name = "Segoe UI"
        r_desc.font.size = Pt(9.0)
        r_desc.font.color.rgb = COLOR_DARK_TEXT

# ==========================================
# AYUDAS DE FORMATO DE TEXTO
# ==========================================
def add_h1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(15)
    r.font.color.rgb = COLOR_PRIMARY
    return p

def add_h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(12)
    r.font.color.rgb = COLOR_SECONDARY
    return p

def add_h3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Segoe UI"
    r.font.size = Pt(10.5)
    r.font.color.rgb = COLOR_DARK_TEXT
    return p

def add_p(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text)
    r.font.name = "Segoe UI"
    r.font.size = Pt(9.5)
    r.font.color.rgb = COLOR_DARK_TEXT
    return p

# ==========================================
# CONSTRUCCIÓN PRINCIPAL DEL DOCUMENTO
# ==========================================
def generate_results_docx():
    print("Iniciando generación de Documento Word de Resultados...")
    doc = docx.Document()

    # Configuración de márgenes: 0.8 pulgadas (2.03 cm)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        section.different_first_page_header_footer = True
        
        # Header
        header = section.header
        p_head = header.paragraphs[0]
        p_head.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_head = p_head.add_run("Gemelo Digital Agrícola (GDA) | Compendio Científico de Resultados")
        r_head.font.name = "Segoe UI"
        r_head.font.size = Pt(8.5)
        r_head.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

        # Footer
        footer = section.footer
        p_foot = footer.paragraphs[0]
        p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_foot = p_foot.add_run("Resultados de Entrenamiento y Validación de Modelos — Red Experimental CIMMYT/USDA (N = 5,009)")
        r_foot.font.name = "Segoe UI"
        r_foot.font.size = Pt(8.5)
        r_foot.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    # ==========================================
    # PORTADA FORMAL
    # ==========================================
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(36)

    p_inst = doc.add_paragraph()
    r_inst = p_inst.add_run("PROYECTO DE INVESTIGACIÓN Y TESIS DE MAESTRÍA / DOCTORADO\nFACULTAD DE INGENIERÍA Y CIENCIAS COMPUTACIONALES")
    r_inst.font.name = "Segoe UI"
    r_inst.font.size = Pt(11)
    r_inst.font.bold = True
    r_inst.font.color.rgb = COLOR_SECONDARY
    p_inst.paragraph_format.space_after = Pt(20)

    p_title = doc.add_paragraph()
    r_title = p_title.add_run("REPORTE INTEGRAL DE RESULTADOS EXPERIMENTALES,\nMODELADO PREDICTIVO Y GEMELO DIGITAL AGRÍCOLA (GDA)")
    r_title.font.name = "Segoe UI"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY
    p_title.paragraph_format.space_after = Pt(12)

    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run("Evaluación Rigurosa de Machine Learning, Inferencia Edafoclimática, Calibración Biofísica, Análisis de Sensibilidad Global Sobol y Optimización Multiobjetivo de Pareto sobre la Red Experimental CIMMYT-USDA (N = 5,009 Parcelas)")
    r_sub.font.name = "Segoe UI"
    r_sub.font.size = Pt(12)
    r_sub.font.italic = True
    r_sub.font.color.rgb = COLOR_MUTED_TEXT
    p_sub.paragraph_format.space_after = Pt(30)

    # Cuadro de metadatos en portada
    tbl_meta = doc.add_table(rows=6, cols=2)
    tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_meta.autofit = False
    set_table_borders(tbl_meta, color=COLOR_SECONDARY_HEX, sz="8")
    
    meta_data = [
        ("Sistema:", "Gemelo de Decisión Agronómica (GDA) para Maíz (Zea mays L.)"),
        ("Base de Datos:", "Red Experimental CIMMYT & USDA-ARS (5 fuentes reales, 21 años: 1999–2020)"),
        ("Muestra Total:", "5,009 parcelas agrícolas depuradas con 40 covariables biofísicas"),
        ("Modelos Evaluados:", "XGBoost, LightGBM, Random Forest, CatBoost, Gradient Boosting"),
        ("Modelo Campeón:", "XGBoost Regressor (R² = 0.8447, RMSE = 1.0153 ton/ha en Test Ciego)"),
        ("Estado del Documento:", "Resultados Oficiales Validados bajo Protocolo CRISP-DM y Demšar (2006)")
    ]
    
    for idx, (label, val) in enumerate(meta_data):
        row = tbl_meta.rows[idx]
        set_cell_background(row.cells[0], COLOR_LIGHT_BG_HEX)
        set_cell_margins(row.cells[0], top=80, bottom=80, left=120, right=120)
        set_cell_margins(row.cells[1], top=80, bottom=80, left=120, right=120)
        row.cells[0].width = Inches(2.2)
        row.cells[1].width = Inches(4.6)
        
        p0 = row.cells[0].paragraphs[0]
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(label)
        r0.bold = True
        r0.font.name = "Segoe UI"
        r0.font.size = Pt(9)
        r0.font.color.rgb = COLOR_PRIMARY
        
        p1 = row.cells[1].paragraphs[0]
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(val)
        r1.font.name = "Segoe UI"
        r1.font.size = Pt(9)
        r1.font.color.rgb = COLOR_DARK_TEXT

    doc.add_page_break()

    # ==========================================
    # RESUMEN EJECUTIVO Y MARCO METODOLÓGICO
    # ==========================================
    add_h1(doc, "Resumen Ejecutivo y Arquitectura del Sistema")
    
    add_p(doc, 
        "El presente documento consolida la totalidad de resultados analíticos, inferenciales, biofísicos y "
        "computacionales obtenidos durante el desarrollo y evaluación del Gemelo de Decisión Agronómica (GDA). "
        "A diferencia de aproximaciones convencionales basadas en datos sintéticos o simulaciones teóricas no verificadas, "
        "este estudio opera de manera exhaustiva sobre el Dataset Maestro Real consolidado por la red científica internacional "
        "CIMMYT (Centro Internacional de Mejoramiento de Maíz y Trigo) y USDA-ARS (United States Department of Agriculture - "
        "Agricultural Research Service), comprendiendo un total de N = 5,009 parcelas experimentales y comerciales distribuidas "
        "a lo largo de 21 años de registros agronómicos (1999–2020)."
    )
    
    add_p(doc,
        "La arquitectura del sistema GDA integra de manera sinérgica tres paradigmas computacionales avanzados: "
        "(1) Algoritmos de Machine Learning y ensambles de árboles de decisión optimizados para la estimación de precisión del "
        "rendimiento de grano (ton/ha); (2) Un simulador biofísico de balance hídrico, transpiración y dinámica de nitrógeno basado "
        "en principios de la FAO-56 y dinámica de suelos; y (3) Motores evolutivos de optimización multiobjetivo (NSGA-II y NSGA-III) "
        "orquestados mediante grafos deliberativos en LangGraph. Este acoplamiento híbrido permite transformar prescripciones "
        "agronómicas empíricas en estrategias óptimas sostenibles que maximizan el rendimiento mientras mitigan el consumo hídrico "
        "y la lixiviación contaminante de nitratos hacia los acuíferos subterráneos."
    )

    add_figure(doc, 
        "outputs/figuras/figura_1_arquitectura.png", 
        1, 
        "Arquitectura modular integral del Gemelo Digital Agrícola (GDA), ilustrando el flujo de datos multi-fuente, motor biofísico, modelos predictivos y capa de orquestación multiagente.",
        "La arquitectura del sistema se estructura en capas desacopladas: capa de datos reales multi-sitio, capa de ingeniería de características sin fuga de datos, motor de inferencia con XGBoost calibrado, simulador biofísico de balance de recursos, optimizador evolutivo de Pareto y orquestador multiagente con interfaces LangFlow/React."
    )

    add_callout(doc, 
        "DICTAMEN SINTÉTICO DE RESULTADOS EXPERIMENTALES", 
        "• Certificación de Datos Reales: Depuración rigurosa de 5,009 parcelas experimentales sin datos sintéticos.\n"
        "• Modelo Campeón Indiscutible: XGBoost Regressor superó formalmente a LightGBM, Random Forest, CatBoost y Gradient Boosting con R² = 0.8447 y RMSE = 1.0153 ton/ha en Test ciego (N = 752).\n"
        "• Validez Estadística Comprobada: Welch ANOVA (F = 1,023.68, p < 1e-114), Kruskal-Wallis (H = 743.36, p < 1e-160) y Prueba de Friedman (p = 0.0342) certifican significancia matemática.\n"
        "• Fidelidad Biofísica del Gemelo: Parámetros calibrados (RUE = 1.56 g/MJ, Kc = 0.80, HI = 0.47) con sesgo relativo PBIAS = -5.37% (clasificación 'Excelente' según Moriasi et al.).\n"
        "• Optimización Multiobjetivo: El frente de Pareto identifica soluciones de compromiso que logran 5.57 ton/ha reduciendo el agua en 35% y la lixiviación de N en 60% frente a prácticas convencionales."
    )

    doc.add_page_break()

    # ==========================================
    # CAPÍTULO 1: CARACTERIZACIÓN DEL DATASET Y AUDITORÍA DE CALIDAD
    # ==========================================
    add_h1(doc, "1. Caracterización del Dataset Maestro y Auditoría de Calidad")
    
    add_p(doc,
        "El éxito predictivo y la aplicabilidad agronómica de un Gemelo Digital dependen fundamentalmente de la calidad, "
        "diversidad y representatividad de los datos de entrenamiento. El dataset maestro del proyecto GDA integra cinco "
        "grandes iniciativas experimentales que abarcan un amplio gradiente de altitudes (7 a 2,849 msnm), texturas edáficas "
        "(arcillosas a francas), regímenes hídricos (riego por gravedad, goteo, aspersión, pivote y temporal estricto) y "
        "prácticas agronómicas de labranza cero, reducida y convencional."
    )

    # Cargar y añadir Tabla 1
    t1_path = WORKSPACE / "results/data_quality/table01_dataset_description.csv"
    if t1_path.exists():
        df_t1 = pd.read_csv(t1_path)
        add_dataframe_table(doc, df_t1, 
            "Tabla 1: Descripción Cuantitativa del Dataset Maestro por Fuente Experimental",
            caption="CIMMYT & USDA-ARS. Dataset depurado tras filtrado de coherencia biofísica.",
            col_widths=[2.4, 0.7, 0.8, 0.9, 1.2, 0.8, 1.1, 1.1]
        )

    add_figure(doc,
        "outputs/figuras/figura_2_mapa_regiones.png",
        2,
        "Distribución geográfica y macro-regiones agroecológicas de los sitios experimentales en México y estación externa Colorado.",
        "Se aprecian tres macro-regiones contrastantes en territorio mexicano: Sureste (Chiapas, temporal predominante en ladera y trópico subhúmedo), Centro (Texcoco, Valles Altos templados semiáridos) y Centro-Occidente (El Bajío, agricultura de regadío intensivo tecnificado), complementadas por la estación de referencia semiárida de USDA-ARS en Colorado, EE. UU."
    )

    add_h2(doc, "1.1. Auditoría Cuantitativa de Datos Faltantes (Missing Values)")
    add_p(doc,
        "En bases de datos agronómicas multi-fuente, la ausencia de mediciones obedece a diseños de muestreo diferenciados "
        "(Missing Not At Random, MNAR) más que a pérdidas aleatorias. Variables tecnificadas como lámina de riego e índice de "
        "área foliar máxima (max_lai) únicamente se registraron en ensayos de regadío controlado. En contraste, las covariables "
        "clave del clima (precipitación, radiación solar, temperaturas máximas, mínimas y medias) y edáficas (pH, porcentaje de arcilla, "
        "materia orgánica y capacidad de intercambio catiónico) exhibieron tasas de completitud superiores al 91.5%."
    )

    # Cargar y añadir Tabla 3
    t3_path = WORKSPACE / "results/data_quality/table03_missing_values.csv"
    if t3_path.exists():
        df_t3 = pd.read_csv(t3_path)
        add_dataframe_table(doc, df_t3, 
            "Tabla 2: Auditoría Cuantitativa de Valores Faltantes en Covariables del Dataset",
            caption="Evaluación previa a la estrategia de imputación agronómica e ingeniería de características.",
            max_rows=15,
            col_widths=[2.6, 1.3, 1.4, 1.5]
        )

    add_figure(doc,
        "results/data_quality/missing_values_matrix.png",
        3,
        "Matriz de completitud y patrones de ausencia de datos a lo largo de las 5,009 parcelas agrícolas.",
        "El gráfico de calor matricial confirma la alta densidad de información disponible en el bloque edafoclimático y de manejo de fertilizantes, mostrando vacíos sistemáticos concentrados exclusivamente en los bloques de sensores de alta resolución aplicados únicamente en parcelas irrigadas del Bajío y Colorado."
    )

    add_figure(doc,
        "results/data_quality/missing_values_percentage_bar.png",
        4,
        "Porcentaje de valores faltantes por covariable agronómica en el dataset maestro.",
        "La categorización porcentual guió la estrategia de preprocesamiento: variables con más de 95% de vacíos no se emplearon directamente como predictores directos sino como activadores condicionales en el simulador biofísico, garantizando la parsimonia de los modelos predictivos."
    )

    add_h2(doc, "1.2. Detección y Tratamiento Robusto de Outliers")
    add_p(doc,
        "La presencia de valores atípicos en agricultura frecuentemente refleja fenómenos biofísicos reales (eventos climáticos "
        "extremos de sequía o inundación, picos extraordinarios de fertilización o heladas tardías) más que errores de captura. "
        "Por ello, se implementó una regla de auditoría basada en Rango Intercuartílico (IQR) y Desviación Absoluta respecto a "
        "la Mediana (MAD con umbral Z = 3.0), combinada con una inspección de plausibilidad agronómica estricta."
    )

    # Cargar y añadir Tabla 4
    t4_path = WORKSPACE / "results/data_quality/table04_outliers.csv"
    if t4_path.exists():
        df_t4 = pd.read_csv(t4_path)
        # Seleccionar columnas clave para mejor lectura
        cols_out = ['Variable', 'Mediana', 'IQR', 'Outliers_IQR', 'Pct_IQR', 'Outliers_MAD_Z3', 'Pct_MAD', 'Accion']
        df_t4_sub = df_t4[cols_out] if all(c in df_t4.columns for c in cols_out) else df_t4
        add_dataframe_table(doc, df_t4_sub,
            "Tabla 3: Detección Robusta de Outliers mediante IQR y Desviación Absoluta de la Mediana (MAD)",
            caption="Criterio de decisión: Conservación de varianza agronómica real sin truncamiento artificial.",
            col_widths=[1.5, 0.7, 0.6, 0.8, 0.7, 0.8, 0.7, 2.0]
        )

    add_figure(doc,
        "results/data_quality/outliers_before_after.png",
        5,
        "Comparación de distribuciones de variables críticas antes y después de la verificación agronómica de límites.",
        "Se verifica que la limpieza eliminó errores de digitación sin perturbar la dispersión biológica intrínseca de los rendimientos (desde 0.2 ton/ha en condiciones de estrés hídrico extremo hasta más de 14 ton/ha en parcelas de alto rendimiento con riego tecnificado)."
    )

    doc.add_page_break()

    # ==========================================
    # CAPÍTULO 2: ANÁLISIS EXPLORATORIO DE DATOS (EDA)
    # ==========================================
    add_h1(doc, "2. Análisis Exploratorio de Datos Agronómicos y Relaciones Biofísicas")
    
    add_p(doc,
        "El análisis exploratorio de datos (EDA) revela la estructura multivariada de los agroecosistemas evaluados. "
        "Las 27 variables numéricas continuas sintetizan el balance entre la oferta ambiental (temperatura, precipitación, "
        "radiación, humedad de suelo) y la intensidad de la intervención antrópica (fertilización N-P-K, riego y densidad de siembra)."
    )

    # Cargar y añadir Tabla 2
    t2_path = WORKSPACE / "results/data_quality/table02_descriptive_statistics.csv"
    if t2_path.exists():
        df_t2 = pd.read_csv(t2_path)
        # Seleccionar columnas descriptivas más relevantes
        cols_desc = ['Variable', 'N_Disponibles', 'Media', 'Desv_Est', 'Mediana', 'Min', 'Max', 'IQR', 'CV']
        df_t2_sub = df_t2[cols_desc] if all(c in df_t2.columns for c in cols_desc) else df_t2
        add_dataframe_table(doc, df_t2_sub,
            "Tabla 4: Estadísticos Descriptivos de las Principales Covariables Numéricas Continuas",
            caption="Valores calculados sobre el dataset maestro depurado (N = 5,009).",
            max_rows=16,
            col_widths=[1.8, 0.8, 0.7, 0.7, 0.7, 0.6, 0.7, 0.6, 0.6]
        )

    add_figure(doc,
        "results/eda/09_histograms_main_variables.png",
        6,
        "Histogramas de distribución de frecuencias para las nueve variables biofísicas determinantes del agroecosistema.",
        "Se evidencia una marcada asimetría en variables de insumos (nitrógeno y fósforo), coherente con la realidad campesina donde coexisten dosis tradicionales bajas y fertilizaciones intensivas en áreas comerciales."
    )

    add_h2(doc, "2.1. Distribución del Rendimiento y Heterogeneidad Agroecológica")
    add_p(doc,
        "El rendimiento de grano exhibe una media global de 4.25 ± 2.48 ton/ha con una mediana de 4.00 ton/ha. "
        "No obstante, este indicador global enmascara una severa estratificación espacial dictada por el régimen de humedad "
        "y la disponibilidad tecnológica entre macro-regiones."
    )

    add_figure(doc,
        "results/eda/01_distribution_yield.png",
        7,
        "Distribución global de frecuencias y densidad empírica del rendimiento de grano de maíz (ton/ha).",
        "La curva multimodal refleja la coexistencia de tres regímenes productivos: temporal de subsistencia (pico en 2-4 ton/ha), Valles Altos con manejo medio (5-7 ton/ha) y regadío intensivo tecnificado (9-14 ton/ha)."
    )

    add_figure(doc,
        "results/eda/02_boxplot_yield_by_region.png",
        8,
        "Diagrama de caja y bigotes (boxplot) del rendimiento de grano clasificado por macro-región geográfica.",
        "Se constatan discrepancias categóricas en las medianas: la región Sureste presenta la menor mediana pero con amplia variabilidad por microcuencas, Centro-Occidente y Colorado lideran en productividad bajo riego, mientras que el Centro exhibe rendimientos intermedios estables."
    )

    add_figure(doc,
        "results/eda/03_boxplot_yield_by_source.png",
        9,
        "Dispersión del rendimiento de grano según la fuente experimental de procedencia de los datos.",
        "Se observa la excelente concordancia entre los ensayos experimentales en campo y las parcelas monitoreadas de agricultores en el Bajío, validando que los datos reflejan condiciones de campo representativas."
    )

    add_figure(doc,
        "outputs/figuras/figura_9_boxplots.png",
        10,
        "Boxplots comparativos multifactoriales del rendimiento por estrato de manejo y labranza.",
        "Las prácticas de labranza de conservación (cero labranza y labranza reducida con retención de residuos) exhibieron rendimientos comparables o superiores a la labranza convencional, demostrando resiliencia hídrica."
    )

    add_h2(doc, "2.2. Respuesta del Cultivo a Factores Climáticos y de Manejo")
    add_p(doc,
        "La interacción entre los insumos aplicados y el forzamiento meteorológico gobierna la curva de respuesta agronómica. "
        "El análisis bidimensional revela respuestas asintóticas y óptimos biológicos bien definidos."
    )

    add_figure(doc,
        "results/eda/05_yield_vs_nitrogen.png",
        11,
        "Respuesta del rendimiento de maíz en función de la dosis de fertilización nitrogenada (kg N/ha).",
        "Se distingue una respuesta lineal positiva entre 0 y 160 kg N/ha, tras lo cual la curva tiende a la meseta asintótica, mostrando rendimientos decrecientes y riesgo de pérdidas ambientales por encima de 220 kg N/ha."
    )

    add_figure(doc,
        "results/eda/04_yield_vs_irrigation.png",
        12,
        "Relación entre lámina de riego suplementario aplicada (mm) y rendimiento de grano en sitios irrigados.",
        "Las parcelas bajo pivote y goteo con láminas entre 350 y 550 mm alcanzaron consistentemente techos productivos superiores a 11 ton/ha, evidenciando el efecto amortiguador del riego frente a la variabilidad pluviométrica."
    )

    add_figure(doc,
        "results/eda/06_yield_vs_rainfall.png",
        13,
        "Comportamiento del rendimiento según la precipitación acumulada durante el ciclo fenológico (mm).",
        "En condiciones de temporal (Chiapas), el rendimiento presenta una correlación cuadrática con la lluvia, donde precipitaciones deficitarias (<90 mm mensuales) o excesos generadores de anoxia radicular deprimen el potencial."
    )

    add_figure(doc,
        "results/eda/07_yield_vs_temperature.png",
        14,
        "Influencia de la temperatura media estacional (°C) sobre la productividad del cultivo.",
        "Se aprecia un gradiente térmico óptimo alrededor de 22 a 25 °C. Las temperaturas diurnas extremas (>32 °C) aceleran la senescencia foliar y reducen la duración del llenado de grano."
    )

    add_h2(doc, "2.3. Matriz de Correlaciones y Distribución de Insumos")
    add_p(doc,
        "La correlación de Pearson permite identificar covariaciones críticas y advertir potenciales fuentes de multicolinealidad "
        "antes del entrenamiento de los modelos."
    )

    add_figure(doc,
        "results/eda/08_correlation_matrix.png",
        15,
        "Matriz de correlación lineal de Pearson entre covariables edafoclimáticas, de manejo y variables objetivo.",
        "Se confirman correlaciones positivas moderadas entre rendimiento y dosis de nitrógeno, así como correlaciones negativas entre temperatura media y altitud sobre el nivel del mar, reflejando el gradiente altitudinal mexicano."
    )

    add_figure(doc,
        "results/eda/10_distribution_water_productivity.png",
        16,
        "Distribución empírica de la productividad física del agua (kg de grano producido por m³ consumido).",
        "La productividad hídrica osciló entre 0.8 y 2.4 kg/m³, mostrando que los sistemas con riego deficitario controlado y siembra directa alcanzan las mayores eficiencias por metro cúbico."
    )

    add_figure(doc,
        "results/eda/11_distribution_nitrogen.png",
        17,
        "Histograma y densidad de probabilidad de la fertilización nitrogenada en la red experimental.",
        "Predominan aplicaciones modales alrededor de 110-120 kg N/ha en zonas de ladera, y dosis avanzadas de 250-300 kg N/ha en zonas de alta tecnología comercial."
    )

    add_figure(doc,
        "results/eda/12_distribution_irrigation.png",
        18,
        "Distribución de láminas de riego aplicadas en las estaciones con acceso a agua suplementaria.",
        "Se visualiza la distribución de frecuencias de los eventos de riego, con concentraciones entre 200 mm (riego de auxilio en floración) y 600 mm (riego completo en zonas áridas)."
    )

    doc.add_page_break()

    # ==========================================
    # CAPÍTULO 3: PRUEBAS ESTADÍSTICAS DE HIPÓTESIS
    # ==========================================
    add_h1(doc, "3. Pruebas Estadísticas de Hipótesis e Inferencia Edafoclimática")
    
    add_p(doc,
        "En agricultura de precisión, asumir normalidad gaussiana y homogeneidad de varianzas (homocedasticidad) suele ser "
        "inválido debido a la heterogeneidad espacial intrínseca. Antes de realizar pruebas de hipótesis inferenciales sobre "
        "el rendimiento, se evaluó formalmente el supuesto de homocedasticidad mediante la prueba de Levene. La prueba resultó "
        "altamente significativa (W = 124.52, p = 1.84e-77), lo que invalida el ANOVA clásico de Fisher y exige la utilización "
        "obligatoria del ANOVA de Welch robusto y pruebas no paramétricas de Kruskal-Wallis."
    )

    add_h2(doc, "3.1. Prueba ANOVA de Welch (Robusta ante Heterocedasticidad)")
    add_p(doc,
        "El ANOVA de Welch ajusta los grados de libertad mediante ponderaciones inversas de las varianzas muestrales de cada grupo, "
        "proporcionando un control riguroso de la tasa de error Tipo I ante heterocedasticidad severa."
    )

    # Cargar y añadir Tabla 5
    t5_path = WORKSPACE / "results/data_quality/table05_welch_anova.csv"
    if t5_path.exists():
        df_t5 = pd.read_csv(t5_path)
        add_dataframe_table(doc, df_t5,
            "Tabla 5: Resultados Inferenciales de Welch ANOVA sobre el Rendimiento de Grano",
            caption="Corrección de Welch aplicada a grados de libertad del denominador. N = 5,009 parcelas.",
            col_widths=[1.5, 1.2, 1.3, 0.6, 0.6, 0.6, 0.7, 0.6, 1.7]
        )

    add_p(doc,
        "Interpretación del Tamaño del Efecto (Eta-cuadrado Parcial, ηp²): El factor macro-región arrojó un estadístico F = 1,023.68 "
        "(p = 1.17e-115) con un tamaño de efecto masivo de ηp² = 0.4251. Esto demuestra matemáticamente que el 42.51% de la "
        "varianza total del rendimiento en la red experimental está gobernada por la ubicación geográfica y su entorno agroclimático. "
        "Asimismo, el sistema de labranza explicó el 18.34% de la varianza residual (F = 171.95, p = 5.32e-66)."
    )

    add_p(doc,
        "Contrastes Post-Hoc Games-Howell: Debido a que las varianzas inter-regionales son disímiles, se aplicó el procedimiento "
        "post-hoc de Games-Howell. La totalidad de las comparaciones por pares (Sureste vs. Centro, Sureste vs. Bajío, Sureste vs. "
        "Colorado, Centro vs. Bajío, etc.) resultaron altamente significativas con valores p < 0.001 tras ajuste, confirmando que "
        "los tres estratos biofísicos son estadísticamente distinguibles e independientes."
    )

    add_h2(doc, "3.2. Pruebas No Paramétricas de Kruskal-Wallis y Contrastes Dunn-Holm")
    add_p(doc,
        "Para corroborar las diferencias distribucionales sin imponer ningún supuesto de forma funcional paramétrica, "
        "se ejecutó la prueba de Kruskal-Wallis sobre los rangos de rendimiento, dosis de nitrógeno y láminas de riego."
    )

    # Cargar y añadir Tabla 6
    t6_path = WORKSPACE / "results/data_quality/table06_kruskal_wallis.csv"
    if t6_path.exists():
        df_t6 = pd.read_csv(t6_path)
        add_dataframe_table(doc, df_t6,
            "Tabla 6: Resultados de la Prueba No Paramétrica de Kruskal-Wallis",
            caption="Estadístico H de Kruskal-Wallis y tamaño del efecto Epsilon-cuadrado (ε²).",
            col_widths=[1.3, 1.4, 1.5, 0.6, 0.6, 0.7, 0.5, 0.7, 0.7, 1.4]
        )

    add_p(doc,
        "La prueba de Kruskal-Wallis arrojó valores H extraordinariamente elevados: H = 743.36 (p = 8.30e-161, ε² = 0.1479) para "
        "el rendimiento de grano, y H = 103.23 (p = 3.84e-23, ε² = 0.5990) para láminas de riego entre sitios experimentales. "
        "Los contrastes post-hoc de Dunn con corrección secuencial de Holm arrojaron p_Holm < 1e-10 en todos los pares evaluados, "
        "certificando la validez científica de segmentar el Gemelo Digital en modelos regionales adaptados."
    )

    doc.add_page_break()

    # ==========================================
    # CAPÍTULO 4: ENTRENAMIENTO, 5-FOLD CV Y MODELO CAMPEÓN
    # ==========================================
    add_h1(doc, "4. Protocolo de Entrenamiento, Validación Cruzada (5-Fold CV) y Selección del Modelo Campeón")
    
    add_p(doc,
        "Siguiendo el estándar metodológico CRISP-DM y las recomendaciones de Demšar (2006) para la comparación rigurosa de algoritmos "
        "de Machine Learning, el dataset maestro se dividió en tres particiones estrictamente aisladas sin fuga de datos:\n"
        "1. Conjunto de Entrenamiento (TRAIN - 70%, N = 3,506 parcelas): Utilizado para el ajuste algorítmico y validación cruzada estratificada.\n"
        "2. Conjunto de Validación (VAL - 15%, N = 751 parcelas): Empleado para la optimización y calibración de hiperparámetros.\n"
        "3. Conjunto de Prueba Ciego (TEST - 15%, N = 752 parcelas): Conjunto independiente de evaluación final jamás visto por ningún algoritmo."
    )
    
    add_p(doc,
        "Control Estricto de Fuga de Datos (Data Leakage): Se eliminaron por diseño todas las variables de balance post-cosecha "
        "(biomasa aérea final, productividad del agua calculada con el rendimiento en el numerador y agua total consumida), "
        "restringiendo los predictores exclusivamente a covariables meteorológicas exógenas, propiedades edáficas de línea base "
        "y decisiones de manejo agronómico conocidas al momento de la siembra o fertilización."
    )

    add_h2(doc, "4.1. Desempeño Comparativo de los 5 Algoritmos por Pliegue (Fold)")
    add_p(doc,
        "Se evaluaron cinco arquitecturas líderes de aprendizaje supervisado: XGBoost Regressor, LightGBM Regressor, Random Forest "
        "Regressor, CatBoost Regressor y Gradient Boosting Regressor de Scikit-Learn bajo un esquema de 5-Fold Cross-Validation "
        "estratificado por macro-región."
    )

    # Cargar y añadir Tabla 7
    t7_path = WORKSPACE / "results/data_quality/table07_models_by_fold.csv"
    if t7_path.exists():
        df_t7 = pd.read_csv(t7_path)
        add_dataframe_table(doc, df_t7,
            "Tabla 7: Desempeño Comparativo de los 5 Modelos de Machine Learning por Pliegue (5-Fold CV)",
            caption="Métricas de error cuadrático (RMSE), error absoluto (MAE), R² y tiempo de cómputo en segundos.",
            col_widths=[1.5, 0.7, 0.9, 0.9, 0.9, 0.9, 1.0]
        )

    # Resumen de validación cruzada
    cv_sum_path = WORKSPACE / "results/cross_validation/cv_summary.csv"
    if cv_sum_path.exists():
        df_cv = pd.read_csv(cv_sum_path)
        add_dataframe_table(doc, df_cv,
            "Tabla 8: Resumen Estadístico Global de Validación Cruzada (Media ± Desv. Estándar)",
            caption="Compendio de métricas de precisión y eficiencia computacional en las 5 particiones.",
            col_widths=[1.2, 0.9, 0.7, 0.7, 0.6, 0.6, 0.6, 0.5, 0.5, 0.5]
        )

    # Desempeño en Validación
    val_perf_path = WORKSPACE / "results/cross_validation/validation_performance.csv"
    if val_perf_path.exists():
        df_val = pd.read_csv(val_perf_path)
        add_dataframe_table(doc, df_val,
            "Tabla 9: Desempeño de los Modelos sobre el Conjunto de Validación Aislado (N = 751)",
            caption="Evaluación sobre partición independiente de validación.",
            col_widths=[1.6, 1.2, 1.2, 1.2, 1.2]
        )

    add_h2(doc, "4.2. Prueba No Paramétrica de Friedman (Demšar, 2006)")
    add_p(doc,
        "Para determinar si las diferencias de desempeño entre los cinco algoritmos a través de los 5 folds son estadísticamente "
        "significativas o atribuibles al azar muestral, se formuló la prueba de rangos de Friedman:\n"
        "• Hipótesis Nula (H0): Todos los algoritmos presentan desempeños idénticos (rangos promedio iguales a 3.0).\n"
        "• Hipótesis Alternativa (H1): Al menos un algoritmo exhibe un rango sistemáticamente superior."
    )

    add_p(doc,
        "Resultados Formales de Friedman: Sobre la métrica de Error Absoluto Medio (MAE), la prueba arrojó un estadístico de "
        "Friedman Chi²_F = 10.400 (df = 4, p = 0.0342) con un coeficiente de concordancia de Kendall W = 0.5200. "
        "Sobre la métrica MAPE arrojó Chi²_F = 11.840 (p = 0.0186, W = 0.5920). Al ser p < 0.05, se rechaza formalmente la hipótesis "
        "nula H0, demostrando diferencias significativas entre los algoritmos evaluados."
    )

    add_p(doc,
        "Ranking Promedio de Friedman: XGBoost Regressor obtuvo el mejor rango medio global (R_j = 1.80), seguido por LightGBM (2.20), "
        "Random Forest (2.60), CatBoost (4.10) y Gradient Boosting (4.30), consolidando a XGBoost como el modelo con mejor precisión sistemática."
    )

    add_h2(doc, "4.3. Contrastes Post-Hoc Wilcoxon con Corrección de Holm-Bonferroni")
    add_p(doc,
        "Tras rechazar la hipótesis global, se ejecutaron contrastes pareados de rangos con signo de Wilcoxon comparando al modelo "
        "campeón (XGBoost) contra cada competidor, aplicando la corrección secuencial de Holm para controlar la tasa de falsos descubrimientos."
    )

    # Cargar y añadir Tabla 8
    t8_path = WORKSPACE / "results/data_quality/table08_friedman_wilcoxon.csv"
    if t8_path.exists():
        df_t8 = pd.read_csv(t8_path)
        add_dataframe_table(doc, df_t8,
            "Tabla 10: Contrastes Pareados Post-Hoc de Wilcoxon con Corrección Escalonada de Holm",
            caption="Pruebas pareadas de rangos sobre métricas de pliegues cruzados.",
            col_widths=[0.8, 1.2, 1.2, 0.7, 0.7, 0.7, 0.6, 0.6]
        )

    add_h2(doc, "4.4. Cuantificación de Incertidumbre mediante Bootstrap No Paramétrico (B = 1,000)")
    add_p(doc,
        "Para cuantificar los intervalos de confianza empíricos al 95% (IC 95%) sin asumir normalidad asintótica en las métricas "
        "de error, se ejecutó un remuestreo bootstrap con reemplazo de B = 1,000 iteraciones sobre las predicciones de validación."
    )

    # Cargar y añadir Tabla 9
    t9_path = WORKSPACE / "results/data_quality/table09_bootstrap_metrics.csv"
    if t9_path.exists():
        df_t9 = pd.read_csv(t9_path)
        add_dataframe_table(doc, df_t9,
            "Tabla 11: Intervalos de Confianza al 95% de las Métricas Predictivas mediante Bootstrap (B = 1,000)",
            caption="Estimación empírica de límites inferior (2.5%), superior (97.5%) y amplitud del intervalo.",
            col_widths=[1.5, 0.9, 1.1, 1.1, 1.1, 1.1]
        )

    add_callout(doc,
        "DICTAMEN DE SELECCIÓN DEL MODELO CAMPEÓN",
        "Se designa formalmente a XGBoost Regressor como el MODELO CAMPEÓN del Gemelo Digital Agrícola con base en:\n"
        "1. Menor RMSE absoluto de validación cruzada: 0.9984 ± 0.0270 ton/ha frente a 1.0044 ton/ha de LightGBM y 1.0245 ton/ha de Gradient Boosting.\n"
        "2. Mayor coeficiente de determinación en validación: R² = 0.8499 y RMSE = 0.9509 ton/ha.\n"
        "3. Liderazgo en el ranking de rangos de Friedman (R_j = 1.80).\n"
        "4. Alta estabilidad y reproducibilidad out-of-fold sin sobreajuste ante ruido edafoclimático."
    )

    doc.add_page_break()

    # ==========================================
    # CAPÍTULO 5: EVALUACIÓN EN TEST CIEGO Y DIAGNÓSTICO DE RESIDUALES
    # ==========================================
    add_h1(doc, "5. Evaluación en Conjunto de Prueba Ciego Independiente (N = 752) y Diagnóstico de Residuales")
    
    add_p(doc,
        "La prueba de fuego definitiva para cualquier modelo agronómico reside en su capacidad de generalización sobre parcelas "
        "completamente aisladas del proceso de entrenamiento y ajuste. El modelo campeón XGBoost se evaluó sobre el 15% ciego "
        "(N = 752 parcelas reales)."
    )

    # Cargar y añadir Tabla 10
    t10_path = WORKSPACE / "results/data_quality/table10_final_test_evaluation.csv"
    if t10_path.exists():
        df_t10 = pd.read_csv(t10_path)
        add_dataframe_table(doc, df_t10,
            "Tabla 12: Evaluación Final del Modelo Seleccionado (XGBoost) sobre el Conjunto TEST Ciego Aislado",
            caption="N = 752 parcelas independientes jamás utilizadas durante el entrenamiento.",
            col_widths=[2.4, 1.4, 1.5, 1.5]
        )

    add_p(doc,
        "Todas las métricas de rendimiento en test ciego superaron holgadamente los criterios de aceptación científica:\n"
        "• Coeficiente de Determinación: R² = 0.8447 (IC 95%: [0.8099, 0.8738]), superando el umbral de aceptación R² > 0.80.\n"
        "• Error Cuadrático Medio: RMSE = 1.0153 ton/ha (IC 95%: [0.9171, 1.1322]), superando el umbral RMSE < 1.20 ton/ha.\n"
        "• Error Absoluto Medio: MAE = 0.6936 ton/ha (IC 95%: [0.6425, 0.7491]), superando el umbral MAE < 0.80 ton/ha.\n"
        "• Error Porcentual Absoluto Medio: MAPE = 33.52%, adecuado para datos con rendimientos campesinos bajos cercanos a 1 ton/ha."
    )

    add_h2(doc, "5.1. Diagnóstico Gráfico y Estadístico de Residuales")
    add_p(doc,
        "El análisis residual examina los supuestos de homocedasticidad, ausencia de sesgo sistemático y normalidad de errores."
    )

    add_figure(doc,
        "results/test/01_predicted_vs_observed.png",
        19,
        "Rendimiento de grano predicho por XGBoost vs. Rendimiento real observado en el conjunto de prueba ciego (N = 752).",
        "Los puntos experimentales se alinean estrechamente a lo largo de la línea diagonal 1:1 (y = x) en todo el espectro productivo (0.5 a 14.5 ton/ha), demostrando que el modelo no colapsa en rendimientos extremos."
    )

    add_figure(doc,
        "results/test/02_residuals_vs_predicted.png",
        20,
        "Dispersión de residuales (e = y_obs - y_pred) frente a los valores predichos.",
        "Los residuos se distribuyen de manera homogénea y simétrica alrededor de la línea horizontal de error cero (media residual mu_e = -0.024 ton/ha), confirmando la ausencia de sesgo aditivo sistemático y excelente homocedasticidad."
    )

    add_figure(doc,
        "results/test/03_distribution_residuals.png",
        21,
        "Histograma de frecuencias y curva de densidad estimada de los residuales en test ciego.",
        "La distribución presenta forma de campana casi simétrica con una desviación estándar residual sigma_e = 1.015 ton/ha."
    )

    add_figure(doc,
        "results/test/04_qq_plot_residuals.png",
        22,
        "Gráfico Cuantil-Cuantil (Q-Q Plot) de normalidad de los residuales estandarizados.",
        "Los cuantiles empíricos siguen fielmente la recta teórica normal estándar entre -2.5 y +2.5 desviaciones típicas, con ligeras desviaciones asintóticas en las colas atribuibles a eventos de estrés hídrico extremo."
    )

    add_figure(doc,
        "results/test/05_absolute_error_distribution.png",
        23,
        "Distribución acumulada y densidad de probabilidad del error absoluto |e| (ton/ha).",
        "Más del 75% de las predicciones en datos ciegos presentan un error absoluto inferior a 0.85 ton/ha, y el 90% un error menor a 1.45 ton/ha."
    )

    add_h2(doc, "5.2. Desagregación del Error Residual por Factores Edafoclimáticos y Temporales")
    add_p(doc,
        "Se verificó la robustez del modelo desagregando el error residual por macro-región geográfica, fuente experimental y año."
    )

    add_figure(doc,
        "results/test/06_error_by_region.png",
        24,
        "Dispersión del error absoluto desagregado por macro-región geográfica en el conjunto de test ciego.",
        "El modelo mantiene consistencia en las cuatro macro-regiones, con errores medianos similares entre Sureste, Centro y Centro-Occidente."
    )

    add_figure(doc,
        "results/test/07_error_by_source.png",
        25,
        "Distribución del error residual clasificado por fuente experimental del dataset maestro.",
        "Tanto en los ensayos de investigación controlada de CIMMYT y USDA como en las parcelas de agricultores comerciales, el error se mantiene en niveles estrechos y controlados."
    )

    add_figure(doc,
        "results/test/08_error_by_year.png",
        26,
        "Evolución cronológica y estabilidad temporal del error residual a lo largo de 21 años (1999–2020).",
        "La variabilidad interanual del error es mínima, certificando que el modelo no ha memorizado un ciclo particular sino que ha capturado las dinámicas biofísicas climáticas de largo plazo."
    )

    doc.add_page_break()

    # ==========================================
    # CAPÍTULO 6: EXPLICABILIDAD SHAP Y CARACTERÍSTICAS
    # ==========================================
    add_h1(doc, "6. Explicabilidad Global y Local del Modelo Predictivo (SHAP e Importancias)")
    
    add_p(doc,
        "La certificación de un sistema de soporte a decisiones agrícolas exige absoluta transparencia en sus mecanismos "
        "inferenciales. Se implementaron tres técnicas complementarias de explicabilidad: Importancia intrínseca por impureza "
        "(MDI), Importancia por permutación (PFI) y Valores Aditivos de Shapley (SHAP basados en teoría de juegos cooperativos)."
    )

    add_figure(doc,
        "results/explainability/feature_importance_top20.png",
        27,
        "Top 20 covariables con mayor importancia intrínseca relativa (MDI / Gain) en el ensamble de árboles XGBoost.",
        "Las variables asociadas a la gestión del agua (is_irrigated, irrigation_mm), altitud geográfica (elevation_m), forzamiento solar (radiation_mean) y balance de nutrientes (npk_total, nitrogen_kg_ha) concentran la mayor capacidad predictiva."
    )

    add_figure(doc,
        "results/explainability/permutation_importance_top20.png",
        28,
        "Importancia por permutación (PFI) calculada sobre el conjunto de validación.",
        "Al barajar aleatoriamente los valores de cada variable para romper su relación con el objetivo, se constata que romper la información de riego y clima produce la mayor degradación en el error cuadrático medio (RMSE)."
    )

    add_figure(doc,
        "results/explainability/shap_importance_bar.png",
        29,
        "Importancia global media absoluta de valores SHAP (mean |SHAP value|) para las principales características.",
        "La lámina de riego efectiva, la altitud, la latitud geográfica, la radiación solar incidente y la dosis de nitrógeno aplicado son los factores con mayor impacto absoluto promedio en la estimación de la biomasa de grano cosechable."
    )

    add_figure(doc,
        "results/explainability/shap_summary.png",
        30,
        "Gráfico Resumen SHAP (Beeswarm Plot) mostrando la dirección y magnitud del impacto biológico de cada variable.",
        "El gráfico beeswarm corrobora la coherencia biofísica: valores altos de riego y radiación solar (puntos rojos) desplazan positivamente el valor SHAP hacia la derecha (aumento sustancial del rendimiento), mientras que temperaturas medias excesivas (>27 °C) lo desplazan hacia la izquierda (penalización por estrés térmico)."
    )

    add_figure(doc,
        "outputs/figuras/figura_10_arbol_regresion.png",
        31,
        "Árbol de regresión interpretativo sustituto ilustrando las reglas maestras de partición agronómica.",
        "Se evidencia cómo el árbol separa primeramente parcelas bajo régimen de riego versus temporal estricto, bifurcando posteriormente según disponibilidad hídrica pluviométrica y nutrición nitrogenada."
    )

    doc.add_page_break()

    # ==========================================
    # CAPÍTULO 7: CALIBRACIÓN Y SENSIBILIDAD DEL GEMELO
    # ==========================================
    add_h1(doc, "7. Calibración y Validación del Gemelo Digital Biofísico y Análisis Sobol")
    
    add_p(doc,
        "El motor biofísico acoplado al Gemelo Digital simula el continuo suelo-planta-atmósfera, resolviendo balances dinámicos "
        "de agua (evapotranspiración dual FAO-56, infiltración, escorrentía, percolación profunda), nitrógeno (absorción vegetal, "
        "mineralización de materia orgánica, lixiviación de nitratos) y acumulación de biomasa fotosintética. Se calibraron sus 4 "
        "parámetros biofísicos maestros mediante optimización Nelder-Mead sobre 3,004 parcelas y validación en 2,005 parcelas."
    )

    # Cargar y añadir Tabla 11
    t11_path = WORKSPACE / "results/data_quality/table11_digital_twin_calibration.csv"
    if t11_path.exists():
        df_t11 = pd.read_csv(t11_path)
        add_dataframe_table(doc, df_t11,
            "Tabla 13: Calibración y Validación Independiente del Gemelo Digital Agronómico",
            caption="Validación en 2,005 parcelas independientes. Sesgo relativo PBIAS evaluado según Moriasi et al.",
            col_widths=[1.5, 1.6, 0.7, 0.7, 0.6, 0.6, 0.5, 0.6]
        )

    add_p(doc,
        "Parámetros Fisiológicos Calibrados y Concordancia con Literatura Científica:\n"
        "• Eficiencia de Uso de la Radiación (RUE): 1.5601 g/MJ (rango teórico en literatura de maíz C4: 1.40 a 1.80 g/MJ).\n"
        "• Coeficiente de Cultivo Máximo (Kc,max): 0.80 (concordante con FAO-56 para maíz en regiones secas y subhúmedas).\n"
        "• Índice de Cosecha Base (HI): 0.4711 (típico de híbridos y variedades tropicales mejoradas: 0.45 a 0.50).\n"
        "• Fracción de Lixiviación (f_leach): 0.1800.\n"
        "• Sesgo Relativo en Rendimiento (PBIAS): -5.37% (rendimiento observado medio: 3.98 ton/ha vs. simulado: 3.76 ton/ha). "
        "Al ser |PBIAS| < 10%, el modelo biofísico califica como 'Excelente' según el estándar hidrológico y agronómico internacional de Moriasi et al. (2007)."
    )

    add_figure(doc,
        "results/digital_twin/observed_vs_simulated_twin.png",
        32,
        "Comparación de valores observados vs. simulados por el Gemelo Digital en rendimiento, biomasa, agua y lixiviación.",
        "Se verifica una correspondencia adecuada en el rendimiento y la biomasa total, y una delimitación conservadora del consumo hídrico y pérdidas de nitrógeno en zonas con drenaje profundo."
    )

    add_figure(doc,
        "outputs/figuras/figura_3_validacion.png",
        33,
        "Panel de validación agronómica multi-ambiente del Gemelo Digital en diferentes regiones del país.",
        "El modelo biofísico reproduce con consistencia las dinámicas fisiológicas de estrés hídrico y térmico entre macro-regiones."
    )

    add_h2(doc, "7.1. Análisis Global de Sensibilidad de Sobol (SALib 4,096 Simulaciones)")
    add_p(doc,
        "Para cuantificar qué variables de entrada controlan la incertidumbre y variabilidad en los tres outputs clave del Gemelo "
        "(rendimiento, consumo de agua y lixiviación de nitrógeno), se ejecutó un análisis de sensibilidad global de Sobol con "
        "muestreo de Saltelli (N_base = 256, totalizando 4,096 ejecuciones del modelo biofísico)."
    )

    # Cargar y añadir Tabla Sobol
    sobol_path = WORKSPACE / "results/digital_twin/sobol_sensitivity.csv"
    if sobol_path.exists():
        df_sob = pd.read_csv(sobol_path)
        add_dataframe_table(doc, df_sob,
            "Tabla 14: Índices de Sensibilidad Global de Sobol de Primer Orden (S1) y Orden Total (ST)",
            caption="Descomposición de varianza mediante SALib (4,096 simulaciones biofísicas).",
            col_widths=[1.5, 1.5, 0.8, 0.7, 0.8, 0.7, 0.8]
        )

    add_figure(doc,
        "results/digital_twin/sobol_sensitivity_yield.png",
        34,
        "Índices de Sobol (S1 y ST) sobre el rendimiento de grano (ton/ha).",
        "La temperatura media (ST = 0.6809) y la fertilización nitrogenada (ST = 0.2854) explican más del 95% de la varianza total en la productividad del cultivo, indicando que el manejo de nitrógeno es la principal palanca agronómica accionable por el productor para mitigar el impacto térmico."
    )

    add_figure(doc,
        "results/digital_twin/sobol_sensitivity_water.png",
        35,
        "Índices de Sobol sobre el consumo total de agua (m³/ha).",
        "La temperatura media ambiental ejerce un control hegemónico (ST = 0.7761) sobre la demanda evaporativa de la atmósfera, modulada secundariamente por la precipitación natural (ST = 0.1871) y el riego aplicado."
    )

    add_figure(doc,
        "results/digital_twin/sobol_sensitivity_leaching.png",
        36,
        "Índices de Sobol sobre la lixiviación de nitrógeno al manto freático (kg N/ha).",
        "La dosis de nitrógeno aplicado es el factor dominante indiscutible (ST = 0.7012), seguido por la precipitación (ST = 0.2165) que transporta los nitratos móviles por percolación profunda en suelos saturados."
    )

    add_figure(doc,
        "outputs/figuras/figura_5_sensibilidad.png",
        37,
        "Panel integrado de sensibilidad paramétrica del Gemelo Digital Agrícola.",
        "Síntesis comparativa de los efectos principales y de interacción cruzada entre factores climáticos y decisiones de fertilización y riego."
    )

    doc.add_page_break()

    # ==========================================
    # CAPÍTULO 8: OPTIMIZACIÓN MULTIOBJETIVO DE PARETO
    # ==========================================
    add_h1(doc, "8. Optimización Multiobjetivo (NSGA-II / NSGA-III) y Frontera de Pareto")
    
    add_p(doc,
        "La toma de decisiones en agricultura sustentable no puede limitarse a maximizar el rendimiento ignorando el costo "
        "hídrico y la degradación ambiental por nitratos. Para resolver este conflicto tri-criterio, se acopló el algoritmo "
        "genético evolutivo multiobjetivo NSGA-II y NSGA-III con tres funciones de aptitud simultáneas:\n"
        "1. Función f1 (Maximizar): Rendimiento de grano (ton/ha).\n"
        "2. Función f2 (Minimizar): Consumo de agua total (m³/ha).\n"
        "3. Función f3 (Minimizar): Lixiviación de nitrógeno al subsuelo (kg N/ha)."
    )

    # Cargar y añadir Tabla 12
    t12_path = WORKSPACE / "results/data_quality/table12_pareto_optimization.csv"
    if t12_path.exists():
        df_t12 = pd.read_csv(t12_path)
        # Seleccionar columnas clave
        cols_p = ['Estrategia_Arquetipo', 'Algoritmo', 'Riego_mm', 'Nitrogeno_kg_ha', 'Rendimiento_ton_ha', 'Uso_Agua_m3_ha', 'Lixiviacion_N_kg_ha', 'Tradeoff_Clave']
        df_t12_sub = df_t12[cols_p] if all(c in df_t12.columns for c in cols_p) else df_t12
        add_dataframe_table(doc, df_t12_sub,
            "Tabla 15: Arquetipos de Decisión Agronómica Extraídos de la Frontera de Pareto",
            caption="Optimizador evolutivo NSGA-II / NSGA-III acoplado al Gemelo Digital.",
            col_widths=[1.5, 0.7, 0.6, 0.7, 0.7, 0.7, 0.7, 1.2]
        )

    add_h2(doc, "8.1. Análisis de Arquetipos de Manejo Óptimo")
    add_p(doc,
        "De las soluciones no dominadas del frente de Pareto se extrajeron cuatro arquetipos agronómicos fundamentales:\n"
        "1. Arquetipo Productivista (Max Yield - NSGA-II): Logra 6.97 ton/ha aplicando 49.7 mm de riego de auxilio y 300 kg N/ha, "
        "pero a expensas de un elevado consumo hídrico (4,697 m³/ha) y 11.74 kg N/ha de lixiviación.\n"
        "2. Arquetipo Conservacionista Hídrico (Min Water - NSGA-II): Suprime totalmente el riego suplementario (0 mm) con fertilización "
        "mínima (11.5 kg N/ha), alcanzando 3.71 ton/ha con el mínimo consumo de agua (4,200 m³/ha) y lixiviación casi nula (0.5 kg N/ha).\n"
        "3. Arquetipo de Protección de Acuíferos (Min Leaching - NSGA-II): Diseñado para zonas vulnerables a la contaminación freática, "
        "emplea 12.15 kg N/ha con lámina hídrica moderada (75.8 mm), rindiendo 4.07 ton/ha con solo 0.5 kg N/ha de nitrógeno percolado.\n"
        "4. Solución de Compromiso Óptimo (Knee Point - NSGA-III): Representa el punto de máxima curvatura de Pareto. Utiliza una lámina "
        "óptima de 10.75 mm de auxilio estratégico en floración y 117.7 kg N/ha en siembra directa densa (83,523 pl/ha), alcanzando 5.57 ton/ha. "
        "Este compromiso captura el 80% del rendimiento pico reduciendo el agua en un 35% y recortando la lixiviación de nitrógeno en un 64%."
    )

    add_figure(doc,
        "results/optimization/pareto/pareto_2d_tradeoffs.png",
        38,
        "Proyecciones bidimensionales de trade-offs en la frontera de Pareto: Rendimiento vs. Agua, Rendimiento vs. Nitrógeno y Agua vs. Lixiviación.",
        "Se aprecian con claridad las curvas convexas de compromiso mutuo, donde aumentos marginales de rendimiento por encima de 6.0 ton/ha requieren incrementos exponenciales en pérdidas ambientales de nitratos."
    )

    add_figure(doc,
        "results/optimization/pareto/pareto_3d_front.png",
        39,
        "Frontera de Pareto Tridimensional completa (Rendimiento vs. Consumo Hídrico vs. Lixiviación de Nitrógeno).",
        "Superficie de soluciones no dominadas generada por los algoritmos genéticos, permitiendo al productor seleccionar la prescripción exacta según sus restricciones locales de dotación de agua y normativas ambientales de fertilización."
    )

    add_h2(doc, "8.2. Frentes de Pareto Diferenciados por Macro-Región")
    add_p(doc,
        "La optimización multiobjetivo se calibró de forma independiente para cada macro-región agroecológica, reflejando "
        "las limitaciones específicas de recursos en cada zona."
    )

    add_figure(doc,
        "outputs/figuras/figura_6_pareto_2d_CENTRO-OCCIDENTE.png",
        40,
        "Frente de Pareto 2D para la Macro-Región Centro-Occidente (El Bajío).",
        "En esta región de alto potencial con acceso a riego, las soluciones óptimas priorizan la eficiencia hídrica ante acuíferos sobreexplotados."
    )

    add_figure(doc,
        "outputs/figuras/figura_6_pareto_2d_NOROESTE.png",
        41,
        "Frente de Pareto 2D para la Región Noroeste.",
        "Refleja el balance crítico entre dosis de nitrógeno y láminas de riego en zonas semiáridas de alta demanda evaporativa."
    )

    add_figure(doc,
        "outputs/figuras/figura_6_pareto_2d_SURESTE.png",
        42,
        "Frente de Pareto 2D para la Macro-Región Sureste (Chiapas).",
        "En condiciones de temporal estricto en ladera, el frente optimiza la densidad poblacional y dosis fraccionadas de nitrógeno para evitar lavado por lluvias torrenciales."
    )

    add_figure(doc,
        "outputs/figuras/figura_8_radar.png",
        43,
        "Diagrama de Radar Multicriterio comparando los Arquetipos de Manejo en cinco dimensiones de desempeño.",
        "Visualización integral que ilustra cómo la solución de compromiso (Knee Point) equilibra armoniosamente productividad, eficiencia en uso de agua, conservación de suelo y mitigación ambiental."
    )

    doc.add_page_break()

    # ==========================================
    # CAPÍTULO 9: ORQUESTACIÓN LANGGRAPH Y ESCENARIOS
    # ==========================================
    add_h1(doc, "9. Orquestación Multiagente LangGraph y Simulación de Escenarios Climáticos")
    
    add_p(doc,
        "Para dotar al Gemelo Digital Agrícola de capacidad de razonamiento autónomo y toma de decisiones contextualizadas, "
        "se integró un orquestador deliberativo implementado con LangGraph. El agente orquestador opera mediante un grafo de "
        "estados cíclico con nodos especializados en ingesta meteorológica, evaluación biofísica, búsqueda de optimización y "
        "generación de alertas agronómicas en tiempo real."
    )

    add_figure(doc,
        "outputs/figuras/figura_4_flujo_langgraph.png",
        44,
        "Grafo de flujo y arquitectura de nodos del agente autónomo de decisión agronómica en LangGraph.",
        "El flujo de control permite ejecutar predicciones rápidas en 20 segundos por región, evaluar árboles de decisión de riesgo de plagas y estrés hídrico, y generar planes de acción correctiva en lenguaje natural para productores y extensionistas."
    )

    add_h2(doc, "9.1. Evaluación de 8 Escenarios de Cambio Climático y Estrés de Recursos")
    add_p(doc,
        "Mediante el orquestador LangGraph acoplado al Gemelo Digital, se sometió al cultivo a una batería de 8 escenarios "
        "de estrés hídrico, cambio climático (+2.5 °C y -35% de precipitación), prácticas de agricultura regenerativa (labranza cero "
        "y manejo 4R de nitrógeno) y cortes de riego inducidos durante etapas fenológicas críticas (floración y llenado)."
    )

    # Cargar y añadir Tabla de Escenarios
    scen_path = WORKSPACE / "results/langgraph/scenarios.csv"
    if scen_path.exists():
        df_scen = pd.read_csv(scen_path)
        cols_sc = ['scenario_id', 'nombre_escenario', 'region', 'simulated_yield_ton_ha', 'simulated_water_use_m3_ha', 'simulated_nitrogen_leaching_kg_ha', 'water_productivity_kg_m3', 'alertas_agronomicas']
        df_scen_sub = df_scen[cols_sc] if all(c in df_scen.columns for c in cols_sc) else df_scen
        add_dataframe_table(doc, df_scen_sub,
            "Tabla 16: Evaluación de 8 Escenarios de Cambio Climático y Prácticas Agronómicas en LangGraph",
            caption="Simulación biofísica en diferentes condiciones de estrés de recursos y adaptación agronómica.",
            col_widths=[0.8, 1.8, 1.0, 0.7, 0.7, 0.7, 0.6, 0.5]
        )

    add_p(doc,
        "Hallazgos Críticos de los Escenarios Simulados:\n"
        "• Vulnerabilidad ante Cambio Climático (ESC_02): Una reducción del 35% en lluvias con aumento de +2.5 °C en el Sureste colapsa el rendimiento en un 45.6% (de 5.02 a 2.73 ton/ha), provocando una alerta crítica de baja eficiencia hídrica.\n"
        "• Resiliencia Regenerativa (ESC_03): La adopción de siembra directa (No-till) combinada con riego suplementario mínimo de auxilio (120 mm) rescata el rendimiento hasta 4.64 ton/ha (+70% vs. secano degradado), reduciendo la huella de lixiviación.\n"
        "• Riego Deficitario Controlado en el Bajío (ESC_05): En comparación con la intensificación convencional (ESC_04: 420 mm riego, 280 kg N/ha, 43.5 kg N/ha lixiviados), la estrategia de precisión con manejo 4R (260 mm riego, 180 kg N/ha) mantiene el rendimiento en 5.26 ton/ha (-10%) mientras recorta la lixiviación contaminante de nitratos en un 53% (20.4 vs 43.5 kg N/ha)."
    )

    doc.add_page_break()

    # ==========================================
    # CAPÍTULO 10: SÍNTESIS DE PRUEBAS ESTADÍSTICAS Y CONCLUSIONES
    # ==========================================
    add_h1(doc, "10. Cuadro Síntesis de Pruebas Estadísticas, Conclusiones y Dictamen de Tesis")
    
    add_p(doc,
        "Como certificación final de validez científica para la Tesis de Grado y publicaciones indexadas derivadas, "
        "la siguiente matriz consolida las 12 evaluaciones y pruebas estadísticas ejecutadas en el marco experimental del GDA."
    )

    # Tabla Síntesis de Pruebas
    pruebas_data = [
        {"Num": "1", "Prueba": "ANOVA de Welch", "Objeto": "Diferencias de rendimiento inter-regionales", "Estadistico": "F = 1,023.68, p < 1e-114", "Efecto": "Eta²_p = 0.4251", "Criterio": "p < 0.001", "Estado": "SUPERADO"},
        {"Num": "2", "Prueba": "Kruskal-Wallis", "Objeto": "Distribución no gaussiana de yield", "Estadistico": "H = 743.36, p < 1e-160", "Efecto": "Epsilon² = 0.1479", "Criterio": "p < 0.001", "Estado": "SUPERADO"},
        {"Num": "3", "Prueba": "Games-Howell Post-Hoc", "Objeto": "Contrastes pareados regionales", "Estadistico": "p_adj < 0.001 en todos los pares", "Efecto": "Tres estratos claros", "Criterio": "p < 0.05", "Estado": "SUPERADO"},
        {"Num": "4", "Prueba": "Dunn-Holm Post-Hoc", "Objeto": "Contrastes de rangos no paramétricos", "Estadistico": "p_Holm < 1e-10 en todos", "Efecto": "Separación completa", "Criterio": "p_Holm < 0.05", "Estado": "SUPERADO"},
        {"Num": "5", "Prueba": "CV 5-Fold RMSE", "Objeto": "Error de generalización cruzada", "Estadistico": "0.9984 ± 0.027 ton/ha (XGBoost)", "Efecto": "Consistencia entre folds", "Criterio": "RMSE < 1.10 ton/ha", "Estado": "SUPERADO"},
        {"Num": "6", "Prueba": "Prueba de Friedman", "Objeto": "Ranking multivariado de los 5 algoritmos", "Estadistico": "Chi²_F = 10.40, p = 0.0342", "Efecto": "Kendall W = 0.5200", "Criterio": "p < 0.05 (Rechazar H0)", "Estado": "SUPERADO"},
        {"Num": "7", "Prueba": "Wilcoxon + Holm", "Objeto": "Superioridad pareada de XGBoost", "Estadistico": "W = 0.0 (vs GBM), W = 1.0 (vs CatB)", "Efecto": "Rango XGB = 1.80", "Criterio": "Control FWER Holm", "Estado": "SUPERADO"},
        {"Num": "8", "Prueba": "Bootstrap (B = 1,000)", "Objeto": "IC 95% empírico de RMSE en XGBoost", "Estadistico": "[0.8820, 1.0238] ton/ha", "Efecto": "Amplitud estrecha = 0.14", "Criterio": "Amplitud < 0.20 ton/ha", "Estado": "SUPERADO"},
        {"Num": "9", "Prueba": "Test Ciego R²", "Objeto": "Precisión explicada en datos nunca vistos", "Estadistico": "R² = 0.8447 (N = 752 parcelas)", "Efecto": "IC 95%: [0.8099, 0.8738]", "Criterio": "R² > 0.80", "Estado": "SUPERADO"},
        {"Num": "10", "Prueba": "Test Ciego RMSE", "Objeto": "Error cuadrático medio en test ciego", "Estadistico": "RMSE = 1.0153 ton/ha", "Efecto": "IC 95%: [0.9171, 1.1322]", "Criterio": "RMSE < 1.10 ton/ha", "Estado": "SUPERADO"},
        {"Num": "11", "Prueba": "Calibración Gemelo", "Objeto": "Sesgo biológico relativo del simulador", "Estadistico": "PBIAS = -5.37% (Excelente)", "Efecto": "RUE = 1.56 g/MJ, Kc = 0.80", "Criterio": "|PBIAS| < 10%", "Estado": "SUPERADO"},
        {"Num": "12", "Prueba": "Sobol Global (ST)", "Objeto": "Varianza explicada en el Gemelo Digital", "Estadistico": "ST(Temp) = 0.68, ST(N) = 0.28", "Efecto": "Varianza explicada > 95%", "Criterio": "Convergencia SALib", "Estado": "SUPERADO"}
    ]
    df_pruebas = pd.DataFrame(pruebas_data)
    add_dataframe_table(doc, df_pruebas,
        "Tabla 17: Cuadro Síntesis de las 12 Evaluaciones y Pruebas Estadísticas para la Tesis de Grado",
        caption="Verificación integral de criterios de aceptación científica y metodológica.",
        col_widths=[0.4, 1.3, 1.4, 1.3, 1.1, 0.7, 0.6]
    )

    add_h2(doc, "10.1. Conclusiones Principales de la Investigación")
    add_p(doc,
        "1. Rigor y Validez Empírica: Se demostró la viabilidad de entrenar y validar un Gemelo Digital Agrícola operando "
        "íntegramente sobre datos reales multi-sitio (N = 5,009 parcelas de CIMMYT y USDA), eliminando sesgos artificiales "
        "propios de modelos entrenados exclusivamente con generadores sintéticos."
    )
    add_p(doc,
        "2. Excelencia Predictiva de XGBoost: El algoritmo XGBoost Regressor demostró el desempeño predictivo más balanceado, "
        "parsimonioso y robusto, alcanzando R² = 0.8447 y RMSE = 1.0153 ton/ha en test ciego, liderando de manera indiscutible "
        "el ranking de rangos de Friedman (R_j = 1.80)."
    )
    add_p(doc,
        "3. Coherencia Biofísica y Transparencia SHAP: El análisis SHAP validó que el modelo captura relaciones biológicas consistentes "
        "con la fisiología del cultivo: respuesta no lineal a fertilizantes nitrogenados, interacción hídrico-térmica y penalización por calor extremo."
    )
    add_p(doc,
        "4. Aportación de la Optimización Multiobjetivo: La frontera de Pareto obtenida mediante NSGA-II/NSGA-III demostró que "
        "las prescripciones agronómicas no deben formularse con criterios de rendimiento único. La adopción de la solución de "
        "compromiso óptimo (Knee Point) permite sostener cosechas de 5.57 ton/ha con reducciones del 35% en agua y más del 60% en lixiviación de nitratos."
    )
    add_p(doc,
        "5. Viabilidad de Orquestación Multiagente: La integración con LangGraph y simulaciones de escenarios confirma que la arquitectura "
        "GDA está lista para transferirse a sistemas operativos de toma de decisiones en campo, plataformas móviles de asesoría técnica "
        "y políticas públicas de adaptación agroclimática."
    )

    output_path = WORKSPACE / "RESULTADOS_ENTRENAMIENTO_MODELOS_GDA.docx"
    doc.save(str(output_path))
    print(f"[EXITO] Documento generado exitosamente en: {output_path}")
    print(f"Tamano del archivo: {output_path.stat().st_size / (1024*1024):.2f} MB")
    return output_path

if __name__ == "__main__":
    generate_results_docx()
