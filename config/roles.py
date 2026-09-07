from config.i18n import t

MATRIZ_PERMISOS = {
    "Administrador": {"simulacion": True, "ia": True, "reportes": True, "usuarios": True},
    "Agrónomo": {"simulacion": True, "ia": True, "reportes": True, "usuarios": False},
    "Agricultor": {"simulacion": True, "ia": False, "reportes": True, "usuarios": False},
    "Visor": {"simulacion": False, "ia": False, "reportes": False, "usuarios": False},
}

def verificar_permiso(rol_usuario, permiso):
    """Verifica si el rol tiene el permiso solicitado"""
    return MATRIZ_PERMISOS.get(rol_usuario, {}).get(permiso, False)
