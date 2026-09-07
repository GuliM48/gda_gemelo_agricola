import streamlit as st
import streamlit.components.v1 as components
from config.i18n import t

HTML_CHATBOT = """
<style>
/* Contenedor flotante */
#chatbot-esfera {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 9999;
    cursor: pointer;
}
/* Esfera animada */
.esfera {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4CAF50, #2E7D32);
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    color: white;
    animation: pulso 2s infinite ease-in-out;
    transition: transform 0.3s;
}
.esfera:hover { transform: scale(1.1); }
@keyframes pulso {
    0% { box-shadow: 0 0 0 0 rgba(76,175,80,0.5); }
    70% { box-shadow: 0 0 0 14px rgba(76,175,80,0); }
    100% { box-shadow: 0 0 0 0 rgba(76,175,80,0); }
}
/* Panel de chat */
#chat-panel {
    position: fixed;
    bottom: 100px;
    right: 24px;
    width: 360px;
    max-height: 480px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 5px 25px rgba(0,0,0,0.2);
    padding: 16px;
    overflow-y: auto;
    display: none;
    flex-direction: column;
    gap: 8px;
}
.mensaje { padding: 8px 12px; border-radius: 16px; max-width: 85%; }
.usuario { background: #E3F2FD; margin-left: auto; }
.asistente { background: #F1F8E9; margin-right: auto; }
.entrada { display: flex; gap: 6px; margin-top: 8px; }
.entrada input { flex: 1; padding: 8px; border-radius: 20px; border: 1px solid #ccc; }
.entrada button { border-radius: 50%; width: 36px; height: 36px; border: none; cursor: pointer; }
</style>

<div id="chatbot-esfera" onclick="alternarChat()">
    <div class="esfera">🌾</div>
</div>

<div id="chat-panel">
    <h4 style="margin:0 0 8px 0;">Asistente Agronómico GDA</h4>
    <div id="mensajes"></div>
    <div class="entrada">
        <input type="text" id="texto-usuario" placeholder="Escribe tu pregunta...">
        <button id="btn-voz" title="Dictar por voz">🎤</button>
        <button onclick="enviarMensaje()">➤</button>
    </div>
</div>

<script>
let abierto = false;
const panel = document.getElementById("chat-panel");
const caja = document.getElementById("texto-usuario");
const mensajes = document.getElementById("mensajes");

function alternarChat() {
    abierto = !abierto;
    panel.style.display = abierto ? "flex" : "none";
}

function agregarMensaje(texto, esUsuario) {
    const div = document.createElement("div");
    div.className = "mensaje " + (esUsuario ? "usuario" : "asistente");
    div.textContent = texto;
    mensajes.appendChild(div);
    mensajes.scrollTop = mensajes.scrollHeight;
}

function enviarMensaje() {
    const t = caja.value.trim();
    if (!t) return;
    agregarMensaje(t, true);
    caja.value = "";
    // Respuesta simulada
    setTimeout(() => {
        agregarMensaje("Entendido. Estoy procesando tu consulta sobre: " + t + ". En un módulo completo conecto con la lógica de simulación y base de datos.", false);
    }, 600);
}

// Reconocimiento de voz (Web Speech API)
const btnVoz = document.getElementById("btn-voz");
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const reconocimiento = new SpeechRecognition();
    reconocimiento.lang = "es-ES";
    reconocimiento.continuous = false;
    reconocimiento.onresult = e => {
        caja.value = e.results[0][0].transcript;
    };
    btnVoz.onclick = () => reconocimiento.start();
} else {
    btnVoz.disabled = true;
    btnVoz.title = "Navegador no soporta reconocimiento de voz";
    btnVoz.style.opacity = "0.4";
}

caja.addEventListener("keypress", e => { if (e.key === "Enter") enviarMensaje(); });
</script>
"""

def mostrar_chatbot_flotante():
    components.html(HTML_CHATBOT, height=650)
