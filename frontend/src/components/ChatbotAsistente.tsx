import React, { useState, useEffect, useRef } from "react";
import {
  consultarChatbotLangChain,
  obtenerEstadoChatbot,
  type MensajeChatbot,
  type ChatbotEstadoResponse,
} from "../client/api";

const PREGUNTAS_SUGERIDAS = [
  "¿Por qué las Zonas 9 y 11 están en alerta roja?",
  "Calcular lámina de riego FAO 56 en floración R1 con déficit de 35 mm",
  "¿Cuál es la dosis recomendada de nitrógeno y frente de Pareto en el Noroeste?",
  "¿Cómo funciona la interoperabilidad OGC y AgGateway ADAPT?",
  "Consultar estado biofísico de la Zona 3 (Bajío Húmedo)",
];

export const ChatbotAsistente: React.FC = () => {
  const [abierto, setAbierto] = useState<boolean>(false);
  const [mensajes, setMensajes] = useState<MensajeChatbot[]>([
    {
      rol: "asistente",
      texto:
        "👋 ¡Hola! Soy tu **Asistente Agronómico Inteligente con LangChain**.\n\n" +
        "Puedo evaluar el estado biofísico de las 12 zonas de manejo de maíz (*Zea mays*), " +
        "analizar **alertas tempranas (umbral ≥70%)**, balance hídrico **FAO 56** y optimización multiobjetivo de **Pareto**.",
      herramientas_usadas: ["consultar_base_conocimiento_agronomica"],
      modo: "LangChain Engine",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputTexto, setInputTexto] = useState<string>("");
  const [cargando, setCargando] = useState<boolean>(false);
  const [estadoAgente, setEstadoAgente] = useState<ChatbotEstadoResponse | null>(null);
  const finMensajesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    obtenerEstadoChatbot()
      .then((res) => setEstadoAgente(res))
      .catch(() => setEstadoAgente(null));
  }, []);

  useEffect(() => {
    if (abierto) {
      finMensajesRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [mensajes, abierto]);

  const handleEnviar = async (texto: string) => {
    const consulta = texto.trim();
    if (!consulta || cargando) return;

    const ahora = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const nuevoMensajeUsuario: MensajeChatbot = {
      rol: "usuario",
      texto: consulta,
      timestamp: ahora,
    };

    setMensajes((prev) => [...prev, nuevoMensajeUsuario]);
    setInputTexto("");
    setCargando(true);

    try {
      // Crear historial resumido para LangChain
      const historial = mensajes.slice(-6).map((m) => ({
        role: m.rol === "usuario" ? "human" : "assistant",
        content: m.texto,
      }));

      const res = await consultarChatbotLangChain(consulta, historial);
      const nuevoMensajeAsistente: MensajeChatbot = {
        rol: "asistente",
        texto: res.respuesta,
        herramientas_usadas: res.herramientas_usadas,
        modo: res.modo,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMensajes((prev) => [...prev, nuevoMensajeAsistente]);
    } catch (err: any) {
      setMensajes((prev) => [
        ...prev,
        {
          rol: "asistente",
          texto:
            `⚠️ No se pudo conectar con el agente LangChain (${err.message || "Error de red"}). ` +
            `Asegúrate de que el backend FastAPI esté en ejecución en el puerto 8000.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setCargando(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleEnviar(inputTexto);
    }
  };

  // Formateador simple de texto con negrita y listas
  const renderTextoFormateado = (txt: string) => {
    return txt.split("\n").map((line, i) => {
      // Reemplazo simple de **texto** por <b>texto</b>
      const partes = line.split(/(\*\*.*?\*\*)/g);
      return (
        <div key={i} style={{ minHeight: line.trim() ? "auto" : "8px", margin: "2px 0" }}>
          {partes.map((p, idx) => {
            if (p.startsWith("**") && p.endsWith("**")) {
              return <strong key={idx}>{p.slice(2, -2)}</strong>;
            }
            return <span key={idx}>{p}</span>;
          })}
        </div>
      );
    });
  };

  return (
    <>
      {/* Botón flotante disparador */}
      <div
        onClick={() => setAbierto(!abierto)}
        title="Asistente Agronómico LangChain"
        style={{
          position: "fixed",
          bottom: "24px",
          right: "24px",
          width: "60px",
          height: "60px",
          borderRadius: "50%",
          background: "linear-gradient(135deg, #10b981 0%, #047857 100%)",
          color: "white",
          boxShadow: "0 6px 20px rgba(16, 185, 129, 0.45)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "26px",
          cursor: "pointer",
          zIndex: 9999,
          transition: "transform 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
          userSelect: "none",
          transform: abierto ? "scale(0.92)" : "scale(1)",
        }}
      >
        🌾
        {/* Pulsating badge */}
        <span
          style={{
            position: "absolute",
            top: "-2px",
            right: "-2px",
            width: "14px",
            height: "14px",
            borderRadius: "50%",
            backgroundColor: "#ef4444",
            border: "2px solid #0f172a",
          }}
        />
      </div>

      {/* Ventana de Chat flotante */}
      {abierto && (
        <div
          style={{
            position: "fixed",
            bottom: "96px",
            right: "24px",
            width: "420px",
            maxWidth: "calc(100vw - 48px)",
            height: "580px",
            maxHeight: "calc(100vh - 120px)",
            backgroundColor: "#0f172a",
            borderRadius: "18px",
            border: "1px solid rgba(255,255,255,0.12)",
            boxShadow: "0 18px 45px rgba(0,0,0,0.6), 0 0 1px 1px rgba(16,185,129,0.2)",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            zIndex: 9999,
            fontFamily: "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: "14px 16px",
              background: "linear-gradient(90deg, #064e3b 0%, #0f172a 100%)",
              borderBottom: "1px solid rgba(255,255,255,0.1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "10px",
                  background: "rgba(16, 185, 129, 0.2)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "18px",
                  border: "1px solid rgba(16, 185, 129, 0.4)",
                }}
              >
                🦜
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: "14px", color: "#f8fafc" }}>
                  Asistente Agronómico GDA
                </div>
                <div style={{ fontSize: "11px", color: "#34d399", display: "flex", alignItems: "center", gap: "5px" }}>
                  <span
                    style={{
                      width: "6px",
                      height: "6px",
                      borderRadius: "50%",
                      backgroundColor: "#10b981",
                      display: "inline-block",
                    }}
                  />
                  {estadoAgente ? estadoAgente.motor : "LangChain Engine Activo"}
                </div>
              </div>
            </div>

            <div style={{ display: "flex", gap: "6px" }}>
              <button
                onClick={() =>
                  setMensajes([
                    {
                      rol: "asistente",
                      texto: "Conversación reiniciada. ¿En qué puedo asistirte con el gemelo de maíz?",
                      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                    },
                  ])
                }
                title="Limpiar conversación"
                style={{
                  background: "none",
                  border: "none",
                  color: "#94a3b8",
                  cursor: "pointer",
                  fontSize: "14px",
                  padding: "4px",
                }}
              >
                🗑️
              </button>
              <button
                onClick={() => setAbierto(false)}
                title="Cerrar ventana"
                style={{
                  background: "none",
                  border: "none",
                  color: "#94a3b8",
                  cursor: "pointer",
                  fontSize: "18px",
                  padding: "4px",
                }}
              >
                ✕
              </button>
            </div>
          </div>

          {/* Sugerencias Rápidas */}
          <div
            style={{
              padding: "8px 12px",
              background: "#1e293b",
              borderBottom: "1px solid rgba(255,255,255,0.06)",
              display: "flex",
              gap: "6px",
              overflowX: "auto",
              whiteSpace: "nowrap",
            }}
          >
            {PREGUNTAS_SUGERIDAS.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleEnviar(p)}
                disabled={cargando}
                style={{
                  background: "rgba(16, 185, 129, 0.12)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  color: "#a7f3d0",
                  padding: "4px 9px",
                  borderRadius: "12px",
                  fontSize: "11px",
                  cursor: "pointer",
                  flexShrink: 0,
                  transition: "background 0.2s",
                }}
              >
                💬 {p.length > 32 ? p.slice(0, 30) + "..." : p}
              </button>
            ))}
          </div>

          {/* Contenedor de Mensajes */}
          <div
            style={{
              flex: 1,
              padding: "14px",
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
              backgroundColor: "#090d16",
              fontSize: "13px",
              lineHeight: "1.45",
            }}
          >
            {mensajes.map((m, i) => {
              const esUsuario = m.rol === "usuario";
              return (
                <div
                  key={i}
                  style={{
                    alignSelf: esUsuario ? "flex-end" : "flex-start",
                    maxWidth: "88%",
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                  }}
                >
                  <div
                    style={{
                      padding: "10px 14px",
                      borderRadius: esUsuario ? "14px 14px 2px 14px" : "14px 14px 14px 2px",
                      backgroundColor: esUsuario ? "#047857" : "#1e293b",
                      color: esUsuario ? "#ffffff" : "#f1f5f9",
                      border: esUsuario ? "none" : "1px solid rgba(255,255,255,0.08)",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.25)",
                      wordBreak: "break-word",
                    }}
                  >
                    {renderTextoFormateado(m.texto)}

                    {/* Chips de herramientas LangChain invocadas */}
                    {m.herramientas_usadas && m.herramientas_usadas.length > 0 && (
                      <div
                        style={{
                          marginTop: "8px",
                          paddingTop: "6px",
                          borderTop: "1px dashed rgba(255,255,255,0.15)",
                          display: "flex",
                          flexWrap: "wrap",
                          gap: "4px",
                        }}
                      >
                        <span style={{ fontSize: "10px", color: "#94a3b8", width: "100%" }}>
                          Herramientas LangChain ejecutadas:
                        </span>
                        {m.herramientas_usadas.map((tool, tIdx) => (
                          <span
                            key={tIdx}
                            style={{
                              fontSize: "10.5px",
                              backgroundColor: "rgba(59, 130, 246, 0.2)",
                              border: "1px solid rgba(59, 130, 246, 0.4)",
                              color: "#93c5fd",
                              padding: "2px 6px",
                              borderRadius: "6px",
                              fontFamily: "monospace",
                            }}
                          >
                            🔧 {tool}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <span
                    style={{
                      fontSize: "10px",
                      color: "#64748b",
                      alignSelf: esUsuario ? "flex-end" : "flex-start",
                      padding: "0 4px",
                    }}
                  >
                    {m.timestamp} {m.modo ? `• ${m.modo}` : ""}
                  </span>
                </div>
              );
            })}

            {cargando && (
              <div
                style={{
                  alignSelf: "flex-start",
                  padding: "10px 14px",
                  borderRadius: "14px 14px 14px 2px",
                  backgroundColor: "#1e293b",
                  border: "1px solid rgba(255,255,255,0.08)",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  color: "#94a3b8",
                  fontSize: "12px",
                }}
              >
                <span>🦜 Agente LangChain consultando herramientas...</span>
                <span style={{ animation: "pulse 1s infinite" }}>⏳</span>
              </div>
            )}
            <div ref={finMensajesRef} />
          </div>

          {/* Input Row */}
          <div
            style={{
              padding: "10px 12px",
              backgroundColor: "#0f172a",
              borderTop: "1px solid rgba(255,255,255,0.1)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <input
              type="text"
              value={inputTexto}
              onChange={(e) => setInputTexto(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Pregunta sobre riego, alerta roja, FAO 56 o Pareto..."
              disabled={cargando}
              style={{
                flex: 1,
                padding: "10px 14px",
                backgroundColor: "#1e293b",
                border: "1px solid rgba(255,255,255,0.15)",
                borderRadius: "20px",
                color: "#f8fafc",
                fontSize: "13px",
                outline: "none",
              }}
            />
            <button
              onClick={() => handleEnviar(inputTexto)}
              disabled={cargando || !inputTexto.trim()}
              title="Enviar consulta"
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "50%",
                border: "none",
                background:
                  cargando || !inputTexto.trim()
                    ? "#334155"
                    : "linear-gradient(135deg, #10b981 0%, #047857 100%)",
                color: "white",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: cargando || !inputTexto.trim() ? "not-allowed" : "pointer",
                fontSize: "15px",
                transition: "background 0.2s",
                boxShadow: cargando || !inputTexto.trim() ? "none" : "0 2px 8px rgba(16,185,129,0.4)",
              }}
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
};
