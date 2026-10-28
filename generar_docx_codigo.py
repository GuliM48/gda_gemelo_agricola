"""
Generador del Documento Word (.docx) con el Código Fuente Completo del Sistema
Gemelo Digital Agrícola para la Predicción y Optimización Multiobjetivo de Cultivos (GDA)
"""

import os
import sys
import time
from pathlib import Path
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

WORKSPACE = Path(__file__).resolve().parent

IGNORE_DIRS = {
    '.git', '.venv', 'venv', 'node_modules', '__pycache__', 
    'dist', 'build', '.kilo', 'catboost_info', 'gda_backend.egg-info',
    '.idea', '.vscode'
}

EXTENSIONS = {'.py', '.ts', '.tsx', '.json', '.txt', '.sh', '.bat'}

# Diccionario de descripciones técnicas enriquecidas
FILE_DESCRIPTIONS = {
    'app.py': 'Punto de entrada de la aplicación principal para ejecución local y servicios.',
    'caso_estudio.py': 'Simulación integral y validación agronómica aplicada al caso de estudio de cultivos.',
    'configuracion.py': 'Parámetros globales del sistema, rutas de datos y constantes agronómicas.',
    'run_pipeline.py': 'Orquestador principal que ejecuta secuencialmente las 11 fases del pipeline experimental.',
    'test_end_to_end.py': 'Suite de pruebas de integración de extremo a extremo (E2E) que valida el flujo completo.',
    'experiment_config.json': 'Configuración de experimentos, rangos de variables y parámetros de modelado.',
    'requirements.txt': 'Especificación de dependencias del entorno de producción y ejecución.',
    'requisitos.txt': 'Lista completa de paquetes y librerías del ecosistema de investigación.',
    'requisitos_orquestador.txt': 'Dependencias específicas para LangGraph, LangChain y orquestación multiagente.',
    
    # Config
    'config/settings.py': 'Gestión de configuración centralizada mediante variables de entorno y Pydantic.',
    'config/roles.py': 'Definición de roles de usuario, permisos y control de acceso.',
    'config/i18n.py': 'Módulo de internacionalización y soporte multilingüe del sistema.',

    # Pipeline
    'pipeline/digital_twin_model.py': 'Modelo biofísico y matemático diferencial del Gemelo Digital (balance hídrico, nitrógeno y rendimiento).',
    'pipeline/stage01_cleaning.py': 'Fase 1: Ingesta, limpieza de datos, unificación de esquemas multifuente y validación de tipos.',
    'pipeline/stage02_eda_missing_outliers.py': 'Fase 2: Análisis exploratorio de datos, detección y tratamiento de outliers e imputación.',
    'pipeline/stage03_statistical_tests.py': 'Fase 3: Batería de pruebas estadísticas de hipótesis (Kruskal-Wallis, ANOVA Welch, Dunn-Holm).',
    'pipeline/stage04_feature_engineering_split.py': 'Fase 4: Ingeniería de características agronómicas y partición estratificada Train/Val/Test.',
    'pipeline/stage05_train_cv_tuning.py': 'Fase 5: Entrenamiento con validación cruzada y ajuste de hiperparámetros (LightGBM, XGBoost, CatBoost, etc.).',
    'pipeline/stage06_model_comparison_test.py': 'Fase 6: Comparación rigurosa de algoritmos en conjunto de test independiente y selección del modelo campeón.',
    'pipeline/stage07_digital_twin_calibration.py': 'Fase 7: Calibración heurística/bayesiana de parámetros biofísicos del gemelo contra observaciones de campo.',
    'pipeline/stage08_langgraph_scenarios.py': 'Fase 8: Simulación de escenarios de cambio climático y estrés de recursos orquestados con LangGraph.',
    'pipeline/stage09_multiobjective_optimization.py': 'Fase 9: Optimización multiobjetivo del frente de Pareto con algoritmos evolutivos NSGA-II y NSGA-III.',
    'pipeline/stage10_global_sensitivity_analysis.py': 'Fase 10: Análisis de sensibilidad global mediante el método de Sobol (índices de primer orden y totales).',
    'pipeline/stage11_publication_tables_report.py': 'Fase 11: Generación automatizada de tablas estadísticas formales y reportes para publicación científica.',

    # Modules Core
    'modules/ia_engine.py': 'Motor principal de inferencia, predicción de rendimiento, estimación de incertidumbre y explicabilidad SHAP.',
    'modules/gemelo.py': 'Lógica de simulación del gemelo digital agrícola: continuo suelo-planta-atmósfera y balance dinámico.',
    'modules/chatbot.py': 'Asistente agronómico conversacional con contextualización de escenarios de cultivo.',
    'modules/chatbot_langchain.py': 'Integración avanzada de LLM con cadenas RAG y herramientas agronómicas de LangChain.',
    'modules/alertas.py': 'Sistema inteligente de detección temprana de estrés hídrico, déficit de nitrógeno y anomalías agroclimáticas.',
    'modules/reportes.py': 'Generador de informes técnicos y ejecutivos en Markdown y formatos tabulares.',
    'modules/api_client.py': 'Cliente de consumo para servicios externos de telemetría y APIs meteorológicas.',
    'modules/orquestador_api.py': 'Capa de mediación y coordinación entre las solicitudes de la API y los motores del gemelo.',

    # Orquestador LangGraph & ABM
    'modules/orquestador_langgraph/langgraph_agent/state.py': 'Definición del estado global y tipado del grafo de decisión en LangGraph.',
    'modules/orquestador_langgraph/langgraph_agent/nodes.py': 'Nodos de procesamiento, análisis agronómico y simulación del agente LangGraph.',
    'modules/orquestador_langgraph/langgraph_agent/graph.py': 'Construcción y compilación de la topología del grafo multiagente.',
    'modules/orquestador_langgraph/langgraph_agent/tools.py': 'Herramientas agronómicas registradas para consulta y cálculo del agente.',
    'modules/orquestador_langgraph/abm_model/agents.py': 'Implementación de agentes agricultores y parcelas en el modelo basado en agentes (ABM).',
    'modules/orquestador_langgraph/abm_model/model.py': 'Entorno biofísico y socio-ecológico del modelo ABM con Mesa.',
    'modules/orquestador_langgraph/abm_model/parametros.py': 'Parámetros de configuración, distribuciones y constantes del modelo ABM.',
    'modules/orquestador_langgraph/abm_model/server.py': 'Servidor de visualización web interactiva para el modelo basado en agentes.',
    'modules/orquestador_langgraph/optimizacion/pareto.py': 'Algoritmos de dominancia de Pareto, filtrado y extracción de arquetipos de cultivo.',
    'modules/orquestador_langgraph/optimizacion/analisis_sensibilidad.py': 'Rutinas de análisis de sensibilidad local para evaluar robustez ante perturbaciones.',
    'modules/orquestador_langgraph/optimizacion/diseno_experimental.py': 'Generación de planes de diseño de experimentos (DoE) para evaluación paramétrica.',
    'modules/orquestador_langgraph/visualizacion/figuras_articulo.py': 'Módulo de generación de gráficos vectoriales de alta resolución para artículos científicos.',
    'modules/orquestador_langgraph/datos/carga_mexico.py': 'Ingesta y normalización de datasets agroclimáticos del territorio mexicano.',

    # Backend
    'backend/main.py': 'Punto de entrada FastAPI del backend.',
    'backend/run.py': 'Script de arranque del servidor web Uvicorn.',
    'backend/run_worker.py': 'Script de inicio de workers de procesamiento en segundo plano.',
    'backend/app/main.py': 'Inicialización de la aplicación FastAPI, configuración de CORS y enrutamiento.',
    'backend/app/worker.py': 'Punto de entrada del worker Celery para tareas asíncronas pesadas.',
    'backend/app/api/deps.py': 'Inyección de dependencias para sesiones de base de datos y autenticación.',
    'backend/app/api/ws.py': 'Manejador de WebSockets para transmisión de telemetría y progreso en tiempo real.',
    'backend/app/api/api_v1/api.py': 'Agrupador de endpoints de la API versión 1.',
    'backend/app/api/api_v1/router_simulaciones.py': 'Endpoints para lanzamiento, consulta y control de simulaciones agrícolas.',
    'backend/app/api/api_v1/router_escenarios.py': 'Endpoints para gestión de escenarios climáticos y de manejo agronómico.',
    'backend/app/api/api_v1/router_modelos_ml.py': 'Endpoints de consulta de modelos predictivos, métricas y artefactos.',
    'backend/app/api/api_v1/router_resultados.py': 'Endpoints de exportación de frentes de Pareto y resultados de optimización.',
    'backend/worker/celery_app.py': 'Configuración de la instancia de Celery con Redis como message broker.',
    'backend/worker/tasks.py': 'Definición de tareas asíncronas: simulaciones masivas y calibración computacional.',

    # Frontend
    'frontend/src/App.tsx': 'Componente raíz y enrutador de vistas de la aplicación React.',
    'frontend/src/main.tsx': 'Punto de montaje en el DOM con soporte de proveedores de estado.',
    'frontend/src/pages/GemeloDigital.tsx': 'Vista principal unificada del Gemelo Digital Agrícola.',
    'frontend/src/client/api.ts': 'Cliente HTTP Axios tipado para comunicación con la API FastAPI.',
    'frontend/src/client/langflow.ts': 'Cliente de integración con el servicio de LangFlow.',
    'frontend/src/components/PanelControl.tsx': 'Panel de control interactivo para parámetros de suelo, riego y clima.',
    'frontend/src/components/GraficoPareto.tsx': 'Visualización interactiva 2D y 3D de frentes de Pareto multiobjetivo.',
    'frontend/src/components/EscenariosOptimos.tsx': 'Módulo comparativo entre escenarios óptimos y prácticas convencionales.',
    'frontend/src/components/ChatbotAsistente.tsx': 'Interfaz de usuario para el asistente agronómico conversacional.',
    'frontend/src/components/VisorGemeloDigital3D.tsx': 'Visualizador tridimensional con Three.js / Canvas para la parcela agrícola.',
    'frontend/src/components/TabGemeloPareto.tsx': 'Pestaña integrada de simulación del gemelo digital y optimización de recursos.',
    'frontend/src/components/TabBenchmarking.tsx': 'Visualización comparativa de métricas de precisión entre algoritmos ML.',
    'frontend/src/components/TabPruebasEstadisticas.tsx': 'Tablero de resultados de pruebas estadísticas de significancia.',
    'frontend/src/components/TabDataMultiFuente.tsx': 'Panel de visualización y monitoreo de datos agroclimáticos multifuente.',
    'frontend/src/components/TabEscenariosRobustez.tsx': 'Evaluación de robustez de cultivos ante estrés climático extremo.',
    'frontend/src/components/TabArquitectura.tsx': 'Diagrama interactivo de la arquitectura distribuida del sistema.',
    'frontend/src/components/VisualizadorFlujo.tsx': 'Visualizador del grafo de flujo de orquestación de agentes en tiempo real.'
}

CATEGORIES = [
    {
        'id': '1',
        'title': '1. CONFIGURACIÓN DEL SISTEMA, DEPENDENCIAS Y SCRIPTS PRINCIPALES',
        'desc': 'Archivos de configuración global, definición de dependencias del entorno de ejecución, puntos de entrada y scripts de validación end-to-end.',
        'filter': lambda r: (r in ['app.py', 'caso_estudio.py', 'configuracion.py', 'run_pipeline.py', 'test_end_to_end.py', 'experiment_config.json', 'requirements.txt', 'requisitos.txt', 'requisitos_orquestador.txt']) or r.startswith('config/')
    },
    {
        'id': '2',
        'title': '2. PIPELINE CIENTÍFICO Y CALIBRACIÓN DEL GEMELO DIGITAL',
        'desc': 'Pipeline de 11 etapas que abarca desde la limpieza, EDA y pruebas estadísticas, hasta el entrenamiento de modelos ML, calibración biofísica, optimización multiobjetivo NSGA-II/NSGA-III y análisis de sensibilidad global Sobol.',
        'filter': lambda r: r.startswith('pipeline/')
    },
    {
        'id': '3',
        'title': '3. MOTORES DE INTELIGENCIA ARTIFICIAL Y GEMELO DIGITAL CORE',
        'desc': 'Módulos centrales del Gemelo Digital Agrícola, incluyendo el motor predictivo de machine learning, la simulación biofísica del cultivo, el sistema de alertas tempranas y el asistente conversacional con RAG.',
        'filter': lambda r: r.startswith('modules/') and not r.startswith('modules/orquestador_langgraph/')
    },
    {
        'id': '4',
        'title': '4. ORQUESTADOR MULTIAGENTE LANGGRAPH, SIMULACIÓN ABM Y OPTIMIZACIÓN',
        'desc': 'Sistema multiagente con grafo de toma de decisiones en LangGraph, modelo de simulación basado en agentes (ABM) con Mesa, cálculo de frentes de Pareto y diseño experimental DoE.',
        'filter': lambda r: r.startswith('modules/orquestador_langgraph/')
    },
    {
        'id': '5',
        'title': '5. BACKEND REST API FASTAPI, MODELOS DE DATOS Y WORKER CELERY',
        'desc': 'Arquitectura de backend construida con FastAPI, enrutadores modulares, modelos ORM SQLAlchemy, validaciones Pydantic, WebSockets para telemetría y workers asíncronos en Celery.',
        'filter': lambda r: r.startswith('backend/')
    },
    {
        'id': '6',
        'title': '6. INTEGRACIÓN Y COMPONENTES VISUALES LANGFLOW',
        'desc': 'Módulos y flujos exportados de LangFlow que permiten orquestar y visualizar de forma modular los procesos de inferencia y optimización del gemelo agrícola.',
        'filter': lambda r: r.startswith('integracion_langflow/') or r.startswith('outputs/langflow/')
    },
    {
        'id': '7',
        'title': '7. INTERFAZ DE USUARIO WEB (FRONTEND REACT + TYPESCRIPT)',
        'desc': 'Aplicación frontend construida con React, TypeScript y Vite, que incluye paneles de control, visores de parcelas 3D, gráficos interactivos de frentes de Pareto y asistentes de recomendación.',
        'filter': lambda r: r.startswith('frontend/src/') or r in ['frontend/package.json', 'frontend/vite.config.ts', 'frontend/tsconfig.json']
    }
]

def set_cell_background(cell, hex_color):
    """Aplica color de fondo a una celda de tabla."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Establece márgenes internos de una celda."""
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

def scan_repository():
    all_files = []
    for root, dirs, files in os.walk(WORKSPACE):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            p = Path(root) / f
            if p.suffix in EXTENSIONS:
                rel = p.relative_to(WORKSPACE).as_posix()
                # Excluir archivos no fuente o de testeo temporal
                if f in ['package-lock.json', 'usda_barc_data.json', 'test_scan.py', 'generar_docx_codigo.py']:
                    continue
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as fl:
                        content = fl.read()
                        lines = content.splitlines()
                        all_files.append({
                            'path': rel,
                            'full_path': str(p),
                            'name': f,
                            'suffix': p.suffix,
                            'lines_count': len(lines),
                            'lines': lines,
                            'size_kb': round(p.stat().st_size / 1024, 2)
                        })
                except Exception as e:
                    pass
    return all_files

def build_docx():
    print("Iniciando escaneo de archivos del repositorio...")
    raw_files = scan_repository()
    
    # Clasificar archivos en categorías
    categorized = {cat['id']: [] for cat in CATEGORIES}
    assigned_paths = set()

    for cat in CATEGORIES:
        filt = cat['filter']
        for f in raw_files:
            if f['path'] not in assigned_paths and filt(f['path']):
                categorized[cat['id']].append(f)
                assigned_paths.add(f['path'])

    # Si algún archivo no quedó clasificado, asignarlo a la categoría 1
    for f in raw_files:
        if f['path'] not in assigned_paths:
            categorized['1'].append(f)
            assigned_paths.add(f['path'])

    total_files = len(raw_files)
    total_lines = sum(f['lines_count'] for f in raw_files)
    print(f"Total archivos a incluir: {total_files}")
    print(f"Total líneas de código: {total_lines}")

    # Crear Documento Word
    doc = docx.Document()

    # Configuración de márgenes de página: 2.0 cm (56.7 pt * 2 = ~113.4 dxa * 10)
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        section.different_first_page_header_footer = True
        
        # Encabezado
        header = section.header
        p_head = header.paragraphs[0]
        p_head.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_head = p_head.add_run("Gemelo Digital Agrícola (GDA) | Anexo Técnico de Código Fuente")
        r_head.font.name = "Segoe UI"
        r_head.font.size = Pt(8.5)
        r_head.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

        # Pie de página
        footer = section.footer
        p_foot = footer.paragraphs[0]
        p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_foot = p_foot.add_run("Documento de Código del Sistema — Proyecto de Investigación y Tesis")
        r_foot.font.name = "Segoe UI"
        r_foot.font.size = Pt(8.5)
        r_foot.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    # Configurar estilo Normal
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Consolas'
    style_normal.font.size = Pt(8)
    style_normal.font.color.rgb = RGBColor(0x1A, 0x20, 0x2C)
    style_normal.paragraph_format.space_before = Pt(0)
    style_normal.paragraph_format.space_after = Pt(0)
    style_normal.paragraph_format.line_spacing = 1.0

    # ==========================================
    # 1. PORTADA ELEGANTE
    # ==========================================
    p_port_space = doc.add_paragraph()
    p_port_space.paragraph_format.space_before = Pt(36)

    p_inst = doc.add_paragraph()
    r_inst = p_inst.add_run("PROYECTO DE INVESTIGACIÓN Y TESIS DE GRADO\nINGENIERÍA DE SISTEMAS / COMPUTACIÓN")
    r_inst.font.name = "Segoe UI"
    r_inst.font.size = Pt(11)
    r_inst.font.bold = True
    r_inst.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)
    p_inst.paragraph_format.space_after = Pt(24)

    p_title = doc.add_paragraph()
    r_title = p_title.add_run("ANEXO TÉCNICO:\nCÓDIGO FUENTE DEL SISTEMA")
    r_title.font.name = "Segoe UI"
    r_title.font.size = Pt(26)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
    p_title.paragraph_format.space_after = Pt(12)

    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run("Gemelo Digital Agrícola para la Predicción de Rendimiento y Optimización Multiobjetivo de Recursos (GDA)")
    r_sub.font.name = "Segoe UI"
    r_sub.font.size = Pt(13)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(0x2B, 0x6C, 0xB0)
    p_sub.paragraph_format.space_after = Pt(36)

    # Tabla de Ficha Técnica
    tbl_meta = doc.add_table(rows=7, cols=2)
    tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_meta.autofit = False

    meta_data = [
        ("Sistema de Software", "Gemelo Digital Agrícola (GDA) v2.0"),
        ("Arquitectura del Sistema", "Híbrida: Biofísica + Machine Learning + ABM + Orquestador LangGraph"),
        ("Lenguajes de Programación", "Python 3.11+, TypeScript, SQL, Bash"),
        ("Frameworks Principales", "FastAPI, Celery, LangGraph, PyMoo, Scikit-Learn, LightGBM, React, Vite"),
        ("Total de Archivos de Código", f"{total_files} archivos fuente"),
        ("Total de Líneas de Código", f"{total_lines:,} líneas de código fuente"),
        ("Fecha de Compilación", "Octubre 2026")
    ]

    for idx, (lbl, val) in enumerate(meta_data):
        row = tbl_meta.rows[idx]
        cell_lbl, cell_val = row.cells[0], row.cells[1]
        cell_lbl.width = Inches(2.5)
        cell_val.width = Inches(4.2)
        set_cell_margins(cell_lbl, top=80, bottom=80, left=100, right=100)
        set_cell_margins(cell_val, top=80, bottom=80, left=100, right=100)

        # Alternar color de fondo
        bg_col = "F7FAFC" if idx % 2 == 0 else "EDF2F7"
        set_cell_background(cell_lbl, bg_col)
        set_cell_background(cell_val, bg_col)

        p1 = cell_lbl.paragraphs[0]
        r1 = p1.add_run(lbl)
        r1.font.name = "Segoe UI"
        r1.font.size = Pt(9.5)
        r1.font.bold = True
        r1.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

        p2 = cell_val.paragraphs[0]
        r2 = p2.add_run(val)
        r2.font.name = "Segoe UI"
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)

    doc.add_page_break()

    # ==========================================
    # 2. ÍNDICE EJECUTIVO Y RESUMEN DE MÓDULOS
    # ==========================================
    p_sec_title = doc.add_paragraph()
    r_sec = p_sec_title.add_run("ÍNDICE ESTRUCTURAL DEL CÓDIGO FUENTE")
    r_sec.font.name = "Segoe UI"
    r_sec.font.size = Pt(18)
    r_sec.font.bold = True
    r_sec.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
    p_sec_title.paragraph_format.space_after = Pt(8)

    p_intro = doc.add_paragraph()
    r_in = p_intro.add_run(
        "A continuación se presenta el desglose cuantitativo y modular del código fuente implementado para el sistema. "
        "El proyecto se divide en 7 subsistemas principales que abarcan la totalidad del pipeline biofísico, computacional y de visualización."
    )
    r_in.font.name = "Segoe UI"
    r_in.font.size = Pt(10)
    r_in.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)
    p_intro.paragraph_format.space_after = Pt(14)

    # Tabla resumen de categorías
    tbl_cats = doc.add_table(rows=len(CATEGORIES) + 2, cols=4)
    tbl_cats.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_cats.autofit = False

    headers = ["N°", "Módulo / Subsistema", "Archivos", "Líneas de Código"]
    col_widths = [Inches(0.6), Inches(3.8), Inches(1.0), Inches(1.3)]

    # Fila de cabecera
    hdr_row = tbl_cats.rows[0]
    for c_idx, h_text in enumerate(headers):
        cell = hdr_row.cells[c_idx]
        cell.width = col_widths[c_idx]
        set_cell_background(cell, "1A365D")
        set_cell_margins(cell, top=100, bottom=100, left=80, right=80)
        p = cell.paragraphs[0]
        if c_idx >= 2:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = p.add_run(h_text)
        r.font.name = "Segoe UI"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # Filas de datos
    for idx, cat in enumerate(CATEGORIES):
        row = tbl_cats.rows[idx + 1]
        cat_files = categorized[cat['id']]
        cat_lines = sum(f['lines_count'] for f in cat_files)

        vals = [
            cat['id'],
            cat['title'],
            str(len(cat_files)),
            f"{cat_lines:,}"
        ]

        bg_col = "F7FAFC" if idx % 2 == 0 else "EDF2F7"

        for c_idx, val in enumerate(vals):
            cell = row.cells[c_idx]
            cell.width = col_widths[c_idx]
            set_cell_background(cell, bg_col)
            set_cell_margins(cell, top=70, bottom=70, left=80, right=80)
            p = cell.paragraphs[0]
            if c_idx >= 2:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(val)
            r.font.name = "Segoe UI"
            r.font.size = Pt(9)
            r.font.color.rgb = RGBColor(0x2D, 0x37, 0x48)
            if c_idx == 0 or c_idx == 1:
                r.font.bold = (c_idx == 0)

    # Fila de Total
    tot_row = tbl_cats.rows[-1]
    tot_vals = ["", "TOTAL SISTEMA", str(total_files), f"{total_lines:,}"]
    for c_idx, val in enumerate(tot_vals):
        cell = tot_row.cells[c_idx]
        cell.width = col_widths[c_idx]
        set_cell_background(cell, "CBD5E0")
        set_cell_margins(cell, top=80, bottom=80, left=80, right=80)
        p = cell.paragraphs[0]
        if c_idx >= 2:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = p.add_run(val)
        r.font.name = "Segoe UI"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

    doc.add_page_break()

    # ==========================================
    # 3. CONTENIDO DE CÓDIGO POR SECCIÓN
    # ==========================================
    for cat_idx, cat in enumerate(CATEGORIES):
        cat_id = cat['id']
        cat_files = categorized[cat_id]
        if not cat_files:
            continue

        print(f"Procesando Sección {cat_id}: {cat['title']} ({len(cat_files)} archivos)...")

        # Título de Sección
        p_sec = doc.add_paragraph()
        p_sec.paragraph_format.space_before = Pt(18)
        p_sec.paragraph_format.space_after = Pt(6)
        r_sec_title = p_sec.add_run(cat['title'])
        r_sec_title.font.name = "Segoe UI"
        r_sec_title.font.size = Pt(15)
        r_sec_title.font.bold = True
        r_sec_title.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

        # Descripción de la sección
        p_desc = doc.add_paragraph()
        p_desc.paragraph_format.space_after = Pt(14)
        r_desc = p_desc.add_run(cat['desc'])
        r_desc.font.name = "Segoe UI"
        r_desc.font.size = Pt(9.5)
        r_desc.font.italic = True
        r_desc.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

        # Procesar cada archivo
        for f_idx, file_info in enumerate(cat_files):
            file_num = f"{cat_id}.{f_idx + 1}"
            rel_path = file_info['path']
            lines = file_info['lines']
            lines_count = file_info['lines_count']
            size_kb = file_info['size_kb']
            suffix = file_info['suffix']

            lang_map = {
                '.py': 'Python',
                '.ts': 'TypeScript',
                '.tsx': 'TypeScript React',
                '.json': 'JSON',
                '.txt': 'Plain Text / Config',
                '.sh': 'Shell Script',
                '.bat': 'Batch Script'
            }
            lang_name = lang_map.get(suffix, 'Texto')

            # Obtener descripción específica o genérica
            file_desc = FILE_DESCRIPTIONS.get(
                rel_path,
                f"Módulo de implementación de {Path(rel_path).name} dentro del subsistema {cat['title'].split('.')[1].strip()}."
            )

            # Banner de información del archivo (Tabla estilizada)
            tbl_info = doc.add_table(rows=1, cols=1)
            tbl_info.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl_info.autofit = False
            cell_banner = tbl_info.rows[0].cells[0]
            cell_banner.width = Inches(6.7)
            set_cell_background(cell_banner, "EDF2F7")
            set_cell_margins(cell_banner, top=70, bottom=70, left=100, right=100)

            p_bnr = cell_banner.paragraphs[0]
            p_bnr.paragraph_format.space_before = Pt(0)
            p_bnr.paragraph_format.space_after = Pt(0)

            # Título del archivo en banner
            r_num = p_bnr.add_run(f"[{file_num}] {rel_path}\n")
            r_num.font.name = "Segoe UI"
            r_num.font.size = Pt(10)
            r_num.font.bold = True
            r_num.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

            r_meta = p_bnr.add_run(f"Lenguaje: {lang_name}   |   Líneas: {lines_count}   |   Tamaño: {size_kb} KB\n")
            r_meta.font.name = "Segoe UI"
            r_meta.font.size = Pt(8.5)
            r_meta.font.bold = True
            r_meta.font.color.rgb = RGBColor(0x2B, 0x6C, 0xB0)

            r_d = p_bnr.add_run(f"Descripción: {file_desc}")
            r_d.font.name = "Segoe UI"
            r_d.font.size = Pt(8.5)
            r_d.font.italic = True
            r_d.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

            # Espacio antes del código
            p_gap = doc.add_paragraph()
            p_gap.paragraph_format.space_before = Pt(4)
            p_gap.paragraph_format.space_after = Pt(2)

            # Líneas de código
            if not lines:
                p_empty = doc.add_paragraph()
                r_emp = p_empty.add_run("   1 | # Archivo vacío")
                r_emp.font.name = "Consolas"
                r_emp.font.size = Pt(8)
                r_emp.font.color.rgb = RGBColor(0xA0, 0xAE, 0xC0)
            else:
                for line_idx, line_raw in enumerate(lines):
                    p_code = doc.add_paragraph()
                    p_code.paragraph_format.space_before = Pt(0)
                    p_code.paragraph_format.space_after = Pt(0)
                    p_code.paragraph_format.line_spacing = 1.0

                    line_clean = line_raw.expandtabs(4)
                    
                    # Número de línea
                    r_lno = p_code.add_run(f"{line_idx + 1:4d} | ")
                    r_lno.font.name = "Consolas"
                    r_lno.font.size = Pt(8)
                    r_lno.font.color.rgb = RGBColor(0xA0, 0xAE, 0xC0)

                    # Contenido de la línea
                    r_lcontent = p_code.add_run(line_clean)
                    r_lcontent.font.name = "Consolas"
                    r_lcontent.font.size = Pt(8)
                    
                    # Coloreado básico: comentarios en verde/gris, código en slate
                    stripped = line_clean.strip()
                    if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
                        r_lcontent.font.color.rgb = RGBColor(0x4A, 0x7C, 0x59)
                        r_lcontent.font.italic = True
                    else:
                        r_lcontent.font.color.rgb = RGBColor(0x1A, 0x20, 0x2C)

            # Separador tras cada archivo
            p_sep = doc.add_paragraph()
            p_sep.paragraph_format.space_before = Pt(8)
            p_sep.paragraph_format.space_after = Pt(8)

        # Salto de página entre secciones grandes
        if cat_idx < len(CATEGORIES) - 1:
            doc.add_page_break()

    # Guardar documento
    output_filename = "CODIGO_FUENTE_SISTEMA_GDA.docx"
    output_path = WORKSPACE / output_filename
    print(f"Guardando documento final en: {output_path}...")
    doc.save(str(output_path))
    print(f"¡Documento generado exitosamente! Tamaño del archivo: {round(output_path.stat().st_size / (1024*1024), 2)} MB")

if __name__ == '__main__':
    t0 = time.time()
    build_docx()
    print(f"Tiempo total transcurrido: {round(time.time() - t0, 2)} segundos.")
