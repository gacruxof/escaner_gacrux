from flask import Flask, render_template_string, request, jsonify
import mysql.connector

app = Flask(__name__)

# ==========================================
# INTERFAZ WEB Y LÓGICA DEL ESCÁNER (HTML + JS)
# ==========================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Gacrux Scanner</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://unpkg.com/html5-qrcode"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; background: #11111b; color: white; margin: 0; padding: 20px; }
        h2 { color: #89b4fa; margin-bottom: 10px; }
        
        #reader { width: 100%; max-width: 400px; margin: 0 auto; border: 3px solid #313244; border-radius: 12px; overflow: hidden; background: white; transition: all 0.3s; }
        .reader-active { border-color: #a6e3a1 !important; box-shadow: 0 0 15px #a6e3a1; }
        
        .controls-panel { max-width: 400px; margin: 20px auto; padding: 15px; background: #1e1e2e; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        
        #btn-scan { width: 100%; padding: 15px; font-size: 1.2em; font-weight: bold; color: white; background: #1e3a8a; border: none; border-radius: 8px; cursor: pointer; transition: 0.2s; box-shadow: 0 4px 0 #0b0b12; margin-bottom: 15px;}
        #btn-scan:active { transform: translateY(4px); box-shadow: 0 0 0 #0b0b12; }
        .btn-scanning { background: #d08c00 !important; }
        
        select { width: 100%; padding: 10px; font-size: 1em; border-radius: 6px; border: 1px solid #45475a; background: #313244; color: white; font-weight: bold; outline: none; cursor: pointer;}
        
        #status { margin-top: 15px; font-weight: bold; color: #a6e3a1; font-size: 1.1em; background: #181825; padding: 10px; border-radius: 8px;}
    </style>
</head>
<body>
    <h2>🚀 GACRUX SCANNER</h2>
    
    <div id="reader"></div>

    <div class="controls-panel">
        <button id="btn-scan" onclick="activarEscaneo()">📷 ACTIVAR ESCÁNER</button>
        
        <label for="soundSelect" style="display:block; text-align:left; margin-bottom:5px; font-size:0.9em; color:#a6adc8;">🎵 Sonido al escanear:</label>
        <select id="soundSelect">
            <option value="beep">Bip Clásico 🔉</option>
            <option value="coin">Moneda de Mario 🪙</option>
            <option value="boing">Salto Boing 🦘</option>
            <option value="magic">Toque Mágico ✨</option>
            <option value="fart">Pedito Gracioso 💨</option>
        </select>
        
        <div id="status">Esperando instrucción...</div>
    </div>

    <script>
        // === 1. SINTETIZADOR DE SONIDO INFINITO Y MATEMÁTICO ===
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

        function playSound() {
            // Aseguramos que el navegador permita el audio (se desbloquea al tocar el botón)
            if (audioCtx.state === 'suspended') audioCtx.resume();
            
            const type = document.getElementById("soundSelect").value;
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            const now = audioCtx.currentTime;

            if (type === 'beep') {
                oscillator.type = 'sine';
                oscillator.frequency.setValueAtTime(880, now); // Nota A5
                gainNode.gain.setValueAtTime(1, now);
                gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
                oscillator.start(now);
                oscillator.stop(now + 0.15);
            } 
            else if (type === 'coin') {
                oscillator.type = 'square';
                oscillator.frequency.setValueAtTime(987.77, now); // B5
                oscillator.frequency.setValueAtTime(1318.51, now + 0.1); // E6
                gainNode.gain.setValueAtTime(1, now);
                gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
                oscillator.start(now);
                oscillator.stop(now + 0.4);
            } 
            else if (type === 'boing') {
                oscillator.type = 'triangle';
                oscillator.frequency.setValueAtTime(400, now);
                oscillator.frequency.exponentialRampToValueAtTime(50, now + 0.3);
                gainNode.gain.setValueAtTime(1, now);
                gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
                oscillator.start(now);
                oscillator.stop(now + 0.3);
            } 
            else if (type === 'magic') {
                oscillator.type = 'sine';
                oscillator.frequency.setValueAtTime(400, now);
                oscillator.frequency.linearRampToValueAtTime(800, now + 0.1);
                oscillator.frequency.linearRampToValueAtTime(1200, now + 0.2);
                gainNode.gain.setValueAtTime(1, now);
                gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
                oscillator.start(now);
                oscillator.stop(now + 0.4);
            }
            else if (type === 'fart') {
                oscillator.type = 'sawtooth';
                oscillator.frequency.setValueAtTime(80, now);
                oscillator.frequency.linearRampToValueAtTime(10, now + 0.3);
                gainNode.gain.setValueAtTime(1, now);
                gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
                oscillator.start(now);
                oscillator.stop(now + 0.3);
            }
        }

        // === 2. LÓGICA DEL ESCÁNER MANUAL ===
        let listoParaEscanear = false;
        const btnScan = document.getElementById("btn-scan");
        const statusDiv = document.getElementById("status");
        const readerDiv = document.getElementById("reader");

        // Función que se ejecuta al darle al botón
        function activarEscaneo() {
            if (audioCtx.state === 'suspended') audioCtx.resume(); // Desbloquear audio en el celular
            listoParaEscanear = true;
            
            btnScan.innerText = "⏳ ENFOCA EL CÓDIGO...";
            btnScan.classList.add("btn-scanning");
            readerDiv.classList.add("reader-active");
            statusDiv.innerText = "Cámara lista. Pasa la etiqueta.";
            statusDiv.style.color = "#89b4fa";
        }

        // Función que se ejecuta internamente cada vez que la cámara ve un código
        function onScanSuccess(decodedText, decodedResult) {
            // Si no le hemos dado al botón, ignoramos el código
            if (!listoParaEscanear) return;
            
            // Si pasamos el filtro, apagamos el escáner para no duplicar lecturas
            listoParaEscanear = false; 
            
            // Reproducir sonido dinámico
            playSound();
            
            // Cambiar UI a estado de "Enviando"
            btnScan.innerText = "✅ ENVIADO";
            btnScan.classList.remove("btn-scanning");
            readerDiv.classList.remove("reader-active");
            statusDiv.innerText = "⏳ Enviando a Gacrux: " + decodedText;
            statusDiv.style.color = "#f9e2af";

            // Enviar el código a nuestro servidor Python (que lo subirá a Aiven)
            fetch('/escanear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ codigo: decodedText })
            })
            .then(response => response.json())
            .then(data => {
                statusDiv.innerText = "✅ " + decodedText + " ¡Añadido a la PC!";
                statusDiv.style.color = "#a6e3a1";
                // Restablecer botón después de un segundo
                setTimeout(() => { 
                    btnScan.innerText = "📷 ESCANEAR OTRO"; 
                }, 1000);
            })
            .catch(err => {
                statusDiv.innerText = "❌ Error de conexión al enviar";
                statusDiv.style.color = "#f38ba8";
                setTimeout(() => { 
                    btnScan.innerText = "🔁 INTENTAR DE NUEVO"; 
                }, 1500);
            });
        }

        // Configuración de la cámara web
        let html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 15, qrbox: {width: 250, height: 100} }, false);
        html5QrcodeScanner.render(onScanSuccess);
    </script>
</body>
</html>
"""

# ==========================================
# RUTAS DEL SERVIDOR WEB
# ==========================================
@app.route('/')
def index():
    # Desplegar la página HTML al entrar a la URL
    return render_template_string(HTML_PAGE)

@app.route('/escanear', methods=['POST'])
def escanear():
    # Recibir el código desde el celular e inyectarlo en Aiven
    data = request.json
    codigo = data.get('codigo')
    
    if not codigo: 
        return jsonify({"error": "No hay código válido"}), 400
    
    try:
        conexion = mysql.connector.connect(
            host="mysql-292462b-gacrux-of.a.aivencloud.com", 
            port=19257,
            user="avnadmin", 
            password="AVNS_lJSsblo1fLuMi6cA-yW", 
            database="defaultdb"
        )
        cursor = conexion.cursor()
        
        # Inyectar en el buzón (la tabla cola_escaneos)
        cursor.execute("INSERT INTO cola_escaneos (codigo_barras) VALUES (%s)", (codigo,))
        conexion.commit()
        
        cursor.close()
        conexion.close()
        return jsonify({"status": "ok"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Punto de entrada para Gunicorn/Render
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
