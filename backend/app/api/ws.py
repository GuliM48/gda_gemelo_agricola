"""
backend/app/api/ws.py
Gestor de WebSockets para comunicación bidireccional en tiempo real entre el Frontend y FastAPI.
Transmite eventos de progreso, creación de simulaciones, frentes de Pareto y métricas sin REST.
"""
import json
import logging
import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app import crud, models, schemas

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🟢 Cliente WebSocket conectado. Total activos: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"🔴 Cliente WebSocket desconectado. Total activos: {len(self.active_connections)}")

    async def send_json(self, message: Dict[str, Any], websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.warning(f"Error enviando mensaje WebSocket: {e}")

    async def broadcast(self, message: Dict[str, Any]):
        mensaje_str = json.dumps(message, default=str)
        desconectados = []
        for connection in self.active_connections:
            try:
                await connection.send_text(mensaje_str)
            except Exception:
                desconectados.append(connection)
        for d in desconectados:
            self.disconnect(d)

manager = ConnectionManager()

# Instancia global accesible desde los workers
def notificar_progreso_websocket(simulacion_id: int, progreso: float, estado: str, error: str = None):
    """Permite a tareas síncronas o en hilos emitir progreso a clientes WebSocket"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({
                    "tipo": "simulacion_progreso",
                    "simulacion_id": simulacion_id,
                    "progreso": progreso,
                    "estado": estado,
                    "error_mensaje": error
                }),
                loop
            )
    except Exception:
        pass


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    db: Session = SessionLocal()
    try:
        # Enviar estado inicial y bienvenida
        user = db.query(models.User).first()
        if not user:
            user = models.User(username="dev_user", email="dev@gda.local", hashed_password="dev", role="Agrónomo", activo=True)
            db.add(user)
            db.commit()
            db.refresh(user)

        await manager.send_json({
            "tipo": "conexion_establecida",
            "mensaje": "Conexión WebSocket directa con FastAPI establecida con éxito",
            "usuario": {"username": user.username, "rol": user.role}
        }, websocket)

        # Enviar lista inicial de simulaciones y modelos
        sims = crud.simulacion.listar(db, limit=50)
        await manager.send_json({
            "tipo": "simulaciones_lista",
            "data": [
                {
                    "id": s.id, "nombre": s.nombre, "region": s.region,
                    "tipo": s.tipo.value if hasattr(s.tipo, "value") else str(s.tipo),
                    "estado": s.estado.value if hasattr(s.estado, "value") else str(s.estado),
                    "progreso": s.progreso, "fecha_creacion": s.fecha_creacion
                }
                for s in sims
            ]
        }, websocket)

        while True:
            raw_data = await websocket.receive_text()
            try:
                msg = json.loads(raw_data)
            except json.JSONDecodeError:
                await manager.send_json({"tipo": "error", "mensaje": "Formato JSON no válido"}, websocket)
                continue

            accion = msg.get("accion") or msg.get("action")

            # 1. PING / LATENCIA
            if accion == "ping":
                await manager.send_json({"tipo": "pong"}, websocket)

            # 2. LISTAR SIMULACIONES
            elif accion == "listar_simulaciones":
                sims = crud.simulacion.listar(db, limit=50)
                await manager.send_json({
                    "tipo": "simulaciones_lista",
                    "data": [
                        {
                            "id": s.id, "nombre": s.nombre, "region": s.region,
                            "tipo": s.tipo.value if hasattr(s.tipo, "value") else str(s.tipo),
                            "estado": s.estado.value if hasattr(s.estado, "value") else str(s.estado),
                            "progreso": s.progreso, "fecha_creacion": s.fecha_creacion
                        }
                        for s in sims
                    ]
                }, websocket)

            # 3. CREAR Y DESPACHAR SIMULACIÓN VÍA WEBSOCKET
            elif accion == "crear_simulacion":
                data = msg.get("data", {})
                tipo_str = data.get("tipo", "simulacion_abm")
                tipo_enum = models.TareaTipo(tipo_str) if tipo_str in [e.value for e in models.TareaTipo] else models.TareaTipo.SIMULACION_ABM

                nueva_sim = models.Simulacion(
                    nombre=data.get("nombre", "Simulación WebSocket"),
                    region=data.get("region", "NOROESTE"),
                    tipo=tipo_enum,
                    descripcion=data.get("descripcion", "Despachada vía WebSocket directo"),
                    parametros=data.get("parametros", {}),
                    estado=models.EstadoSimulacion.PENDIENTE,
                    progreso=0.0,
                    usuario_id=user.id
                )
                db.add(nueva_sim)
                db.commit()
                db.refresh(nueva_sim)

                # Notificar a todos los clientes que se creó la simulación
                await manager.broadcast({
                    "tipo": "simulacion_creada",
                    "simulacion": {
                        "id": nueva_sim.id,
                        "nombre": nueva_sim.nombre,
                        "region": nueva_sim.region,
                        "tipo": nueva_sim.tipo.value,
                        "estado": nueva_sim.estado.value,
                        "progreso": 0.0,
                        "fecha_creacion": nueva_sim.fecha_creacion
                    }
                })

                # Despachar ejecución en hilo y transmitir actualizaciones vía WebSocket
                from app.worker import ejecutar_simulacion_abm_task, orquestar_escenarios_task
                import threading

                def _ejecutar_y_transmitir(s_id, s_tipo):
                    from app.worker import actualizar_progreso
                    _db = SessionLocal()
                    try:
                        # Emite progreso 10%
                        actualizar_progreso(_db, s_id, 0.1, models.EstadoSimulacion.EJECUTANDO)
                        notificar_progreso_websocket(s_id, 0.1, "ejecutando")

                        if s_tipo == models.TareaTipo.SIMULACION_ABM:
                            ejecutar_simulacion_abm_task(None, s_id)
                        else:
                            orquestar_escenarios_task(None, s_id)

                        notificar_progreso_websocket(s_id, 1.0, "completada")
                    except Exception as err:
                        logger.error(f"Error en ejecución WebSocket: {err}")
                        notificar_progreso_websocket(s_id, 0.0, "fallida", error=str(err))
                    finally:
                        _db.close()

                threading.Thread(target=_ejecutar_y_transmitir, args=(nueva_sim.id, nueva_sim.tipo), daemon=True).start()

            # 4. OBTENER FRENTE DE PARETO Y MÉTRICAS
            elif accion == "obtener_pareto":
                sim_id = msg.get("simulacion_id")
                sim = crud.simulacion.obtener(db, id=sim_id)
                if not sim:
                    await manager.send_json({"tipo": "error", "mensaje": f"Simulación {sim_id} no encontrada"}, websocket)
                    continue

                escenarios = crud.escenario.listar_por_simulacion(db, simulacion_id=sim_id, limit=200)
                resultados = crud.resultado.listar_por_simulacion(db, simulacion_id=sim_id)

                # Extraer métricas
                metricas = {}
                if resultados:
                    r0 = resultados[0]
                    metricas = {
                        "rendimiento_ton_ha": r0.rendimiento_ton_ha,
                        "uso_agua_m3_ha": r0.uso_agua_m3_ha,
                        "lixiviacion_N_kg_ha": r0.lixiviacion_N_kg_ha,
                        "margen_economico_usd_ha": r0.margen_economico_usd_ha,
                        "detalles": r0.metricas_adicionales or {}
                    }

                await manager.send_json({
                    "tipo": "pareto_datos",
                    "simulacion_id": sim_id,
                    "simulacion_nombre": sim.nombre,
                    "region": sim.region,
                    "metricas": metricas,
                    "escenarios": [
                        {
                            "escenario_numero": e.escenario_numero,
                            "dosis_N_kg_ha": e.dosis_N_kg_ha,
                            "estrategia_riego": e.estrategia_riego,
                            "densidad_plantas_ha": e.densidad_plantas_ha,
                            "es_pareto": bool(e.es_pareto_optimo)
                        }
                        for e in escenarios
                    ]
                }, websocket)

            # 5. LISTAR MODELOS ML
            elif accion == "listar_modelos_ml":
                modelos = crud.modelo_ml.listar(db, limit=50)
                await manager.send_json({
                    "tipo": "modelos_ml_lista",
                    "data": [
                        {
                            "id": m.id, "nombre": m.nombre, "tipo": m.tipo,
                            "region": m.region, "r2_score": m.r2_score, "rmse": m.rmse
                        }
                        for m in modelos
                    ]
                }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Excepción en websocket: {e}")
        manager.disconnect(websocket)
    finally:
        db.close()
