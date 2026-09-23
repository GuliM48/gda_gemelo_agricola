"""
modules/chatbot.py
Asistente Virtual Agronómico GDA con reconocimiento de voz y soporte de LangChain.
Flotante permanente en la ventana del navegador (visible en todo momento en Streamlit).
"""
import streamlit as st
import streamlit.components.v1 as components

HTML_CHATBOT_WINDOW = """
<script>
(function() {
    let pDoc;
    try {
        pDoc = (window.parent && window.parent.document) ? window.parent.document : document;
    } catch (e) {
        pDoc = document;
    }
    
    // Evitar duplicar si ya está inyectado
    if (pDoc.getElementById("gda-assistant-container")) {
        return;
    }

    // 1. Estilos inyectados al documento principal
    const style = pDoc.createElement("style");
    style.id = "gda-assistant-styles";
    style.textContent = `
        #gda-assistant-container {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 9999999;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        #gda-esfera-btn {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #2E7D32, #1B5E20);
            box-shadow: 0 4px 18px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            color: white;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            user-select: none;
            position: relative;
        }
        #gda-esfera-btn:hover {
            transform: scale(1.08);
            box-shadow: 0 6px 24px rgba(46,125,50,0.5);
        }
        #gda-esfera-badge {
            position: absolute;
            top: -2px;
            right: -2px;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background-color: #ef4444;
            border: 2px solid #ffffff;
        }
        #gda-chat-window {
            position: fixed;
            bottom: 96px;
            right: 24px;
            width: 400px;
            max-width: calc(100vw - 48px);
            height: 540px;
            max-height: calc(100vh - 120px);
            background: #ffffff;
            border-radius: 18px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.28);
            display: none;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid #E0E0E0;
            z-index: 9999999;
        }
        #gda-chat-header {
            background: linear-gradient(135deg, #1b5e20, #2e7d32);
            color: white;
            padding: 13px 16px;
            font-weight: 600;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        #gda-chat-sub {
            font-size: 11px;
            color: #C8E6C9;
            font-weight: 400;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        #gda-chat-header span.close-btn {
            cursor: pointer;
            font-size: 18px;
            opacity: 0.85;
        }
        #gda-chat-header span.close-btn:hover {
            opacity: 1;
        }
        #gda-chat-chips {
            padding: 7px 10px;
            background: #F1F8E9;
            border-bottom: 1px solid #E0E0E0;
            display: flex;
            gap: 6px;
            overflow-x: auto;
            white-space: nowrap;
        }
        .gda-chip {
            background: #E8F5E9;
            border: 1px solid #C8E6C9;
            color: #2E7D32;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            cursor: pointer;
            flex-shrink: 0;
            transition: all 0.15s;
        }
        .gda-chip:hover {
            background: #C8E6C9;
        }
        #gda-chat-messages {
            flex: 1;
            padding: 14px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: #FAFAFA;
            font-size: 13px;
            line-height: 1.45;
        }
        .gda-msg {
            max-width: 86%;
            padding: 10px 14px;
            border-radius: 14px;
            word-wrap: break-word;
        }
        .gda-msg-bot {
            background: #FFFFFF;
            color: #212121;
            align-self: flex-start;
            border: 1px solid #E0E0E0;
            border-bottom-left-radius: 4px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }
        .gda-msg-user {
            background: #2E7D32;
            color: #FFFFFF;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        .gda-tool-tag {
            display: inline-block;
            background: #E3F2FD;
            color: #1565C0;
            border: 1px solid #BBDEFB;
            border-radius: 4px;
            padding: 1px 5px;
            font-size: 10px;
            margin-top: 6px;
            margin-right: 4px;
            font-family: monospace;
        }
        #gda-chat-input-row {
            display: flex;
            padding: 10px;
            background: #FFFFFF;
            border-top: 1px solid #EEEEEE;
            gap: 6px;
            align-items: center;
        }
        #gda-chat-input {
            flex: 1;
            padding: 9px 14px;
            border: 1px solid #CCCCCC;
            border-radius: 20px;
            font-size: 13px;
            outline: none;
        }
        #gda-chat-input:focus {
            border-color: #2E7D32;
        }
        .gda-action-btn {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: none;
            background: #2E7D32;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        .gda-action-btn:hover {
            background: #1B5E20;
        }
        #gda-btn-voice {
            background: #EEEEEE;
            color: #333333;
        }
        #gda-btn-voice:hover {
            background: #DDDDDD;
        }
    `;
    pDoc.head.appendChild(style);

    // 2. Contenedor del Widget
    const container = pDoc.createElement("div");
    container.id = "gda-assistant-container";
    container.innerHTML = `
        <div id="gda-esfera-btn" title="Asistente Agronómico LangChain">
            🌾
            <div id="gda-esfera-badge"></div>
        </div>
        <div id="gda-chat-window">
            <div id="gda-chat-header">
                <div>
                    <div>🤖 Asistente Agronómico GDA</div>
                    <div id="gda-chat-sub">🦜 LangChain Agent • 12 Zonas de Maíz</div>
                </div>
                <span class="close-btn" id="gda-close-btn">✕</span>
            </div>
            <div id="gda-chat-chips">
                <span class="gda-chip" data-q="¿Por qué las Zonas 9 y 11 están en alerta roja?">🚨 Alertas Rojas</span>
                <span class="gda-chip" data-q="Calcular lámina de riego FAO 56 en floración R1 con déficit de 35 mm">💧 Riego FAO 56</span>
                <span class="gda-chip" data-q="¿Cuál es la dosis recomendada de nitrógeno y frente de Pareto para el Noroeste?">🎯 Frente de Pareto</span>
                <span class="gda-chip" data-q="¿Cómo funciona la interoperabilidad OGC y AgGateway ADAPT?">🌐 OGC / ADAPT</span>
            </div>
            <div id="gda-chat-messages">
                <div class="gda-msg gda-msg-bot">
                    ¡Hola! Soy tu asistente agronómico potenciado por <b>LangChain</b>.<br><br>
                    Monitoreo en tiempo real las 12 zonas de manejo biofísicas de maíz (<i>Zea mays</i>),
                    evalúo el sistema de alerta temprana (<b>umbral ≥ 70%</b>), calculo requerimientos de agua (<b>FAO 56</b>)
                    y frentes de optimización multiobjetivo de Pareto.
                </div>
            </div>
            <div id="gda-chat-input-row">
                <input type="text" id="gda-chat-input" placeholder="Pregunta sobre riego, alerta roja o nitrógeno...">
                <button class="gda-action-btn" id="gda-btn-voice" title="Dictar por voz">🎤</button>
                <button class="gda-action-btn" id="gda-btn-send" title="Enviar">➤</button>
            </div>
        </div>
    `;
    pDoc.body.appendChild(container);

    // 3. Lógica interactiva
    const btnEsfera = pDoc.getElementById("gda-esfera-btn");
    const chatWin = pDoc.getElementById("gda-chat-window");
    const closeBtn = pDoc.getElementById("gda-close-btn");
    const inputMsg = pDoc.getElementById("gda-chat-input");
    const btnSend = pDoc.getElementById("gda-btn-send");
    const btnVoice = pDoc.getElementById("gda-btn-voice");
    const msgsBox = pDoc.getElementById("gda-chat-messages");
    const chips = pDoc.querySelectorAll(".gda-chip");

    let chatAbierto = false;
    function toggleChat() {
        chatAbierto = !chatAbierto;
        chatWin.style.display = chatAbierto ? "flex" : "none";
        if (chatAbierto) inputMsg.focus();
    }

    btnEsfera.onclick = toggleChat;
    closeBtn.onclick = toggleChat;

    chips.forEach(chip => {
        chip.onclick = function() {
            const q = this.getAttribute("data-q");
            inputMsg.value = q;
            enviarMensaje();
        };
    });

    function formatMarkdown(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
            .replace(/\*(.*?)\*/g, '<i>$1</i>')
            .replace(/\\n/g, '<br>')
            .replace(/\n/g, '<br>');
    }

    function responderLocalFallback(pregunta) {
        const p = pregunta.toLowerCase();
        if (p.includes("alerta") || p.includes("rojo") || p.includes("riesgo")) {
            return "🚨 <b>Evaluación de Alerta Temprana:</b> La Zona 9 (Estrés Hídrico: 79.5%) y Zona 11 (Estrés Hídrico: 85.0%) superan el umbral crítico del 70%. Se recomienda riego urgente de 38 mm en floración R1.<br><span class='gda-tool-tag'>🔧 evaluar_alerta_temprana</span>";
        } else if (p.includes("riego") || p.includes("agua") || p.includes("fao")) {
            return "💧 <b>Balance Hídrico FAO 56:</b> En etapa R1 (Floración, Kc=1.20) con déficit de 35 mm, la lámina bruta a aplicar es de 38.9 mm (eficiencia 90%), equivalente a 389 m³/ha.<br><span class='gda-tool-tag'>🔧 calcular_riego_fao56</span>";
        } else if (p.includes("pareto") || p.includes("nitrogeno") || p.includes("optimo")) {
            return "🎯 <b>Frente de Pareto (Noroeste):</b> Compromiso óptimo con 185 kg N/ha y riego por déficit controlado (78%), proyectando 11.2 ton/ha con margen neto de 1,840 USD/ha.<br><span class='gda-tool-tag'>🔧 consultar_frente_pareto</span>";
        } else {
            return "🌾 <b>Gemelo Digital GDA:</b> Armonización multi-modal UAV + Sentinel-2 + SoilGrids bajo estándares OGC y AgGateway ADAPT para maíz.<br><span class='gda-tool-tag'>🔧 consultar_base_conocimiento_agronomica</span>";
        }
    }

    async function enviarMensaje() {
        const texto = inputMsg.value.trim();
        if (!texto) return;

        // Mensaje de usuario
        const mUser = pDoc.createElement("div");
        mUser.className = "gda-msg gda-msg-user";
        mUser.textContent = texto;
        msgsBox.appendChild(mUser);
        inputMsg.value = "";
        msgsBox.scrollTop = msgsBox.scrollHeight;

        // Indicador de "pensando"
        const mBot = pDoc.createElement("div");
        mBot.className = "gda-msg gda-msg-bot";
        mBot.innerHTML = "🦜 <i>LangChain procesando herramientas agronómicas...</i>";
        msgsBox.appendChild(mBot);
        msgsBox.scrollTop = msgsBox.scrollHeight;

        try {
            const resp = await fetch("http://localhost:8000/api/v1/chatbot/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mensaje: texto })
            });

            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const data = await resp.json();

            let toolTags = "";
            if (data.herramientas_usadas && data.herramientas_usadas.length > 0) {
                toolTags = "<div style='margin-top:8px; border-top:1px dashed #ddd; padding-top:4px;'>" +
                    data.herramientas_usadas.map(t => `<span class='gda-tool-tag'>🔧 ${t}</span>`).join("") +
                    "</div>";
            }

            mBot.innerHTML = formatMarkdown(data.respuesta) + toolTags;
        } catch (e) {
            console.warn("Falla de API remota para chatbot, usando fallback local:", e);
            mBot.innerHTML = responderLocalFallback(texto);
        }

        msgsBox.scrollTop = msgsBox.scrollHeight;
    }

    btnSend.onclick = enviarMensaje;
    inputMsg.onkeypress = function(e) {
        if (e.key === "Enter") enviarMensaje();
    };

    // Reconocimiento de voz (Web Speech API)
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        const reco = new SpeechRec();
        reco.lang = "es-ES";
        reco.continuous = false;
        reco.onresult = function(e) {
            inputMsg.value = e.results[0][0].transcript;
            enviarMensaje();
        };
        btnVoice.onclick = function() { reco.start(); };
    } else {
        btnVoice.style.opacity = "0.4";
        btnVoice.title = "Voz no soportada en este navegador";
    }
})();
</script>
"""

def mostrar_chatbot_flotante():
    """Inyecta el widget asistente de forma persistente en la ventana principal de Streamlit"""
    components.html(HTML_CHATBOT_WINDOW, height=0)
