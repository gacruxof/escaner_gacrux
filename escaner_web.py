from flask import Flask, render_template_string, request, jsonify
import mysql.connector

app = Flask(__name__)

# ==========================================
# INTERFAZ WEB PROFESIONAL (Basada en Gacrux Principal)
# ==========================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Gacrux Scanner</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <!-- Usamos la librería pura para tener control total de la interfaz -->
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <style>
        :root {
            --bg-body: #121214;
            --bg-card: #1e1e24;
            --primary: #1e3a8a;
            --success: #2e7d32;
            --danger: #7f1d1d;
            --text: #ffffff;
        }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: var(--bg-body); 
            color: var(--text); 
            margin: 0; 
            padding: 15px; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            height: 100vh;
            box-sizing: border-box;
            overflow: hidden; /* Evita que la pantalla se deslice */
        }
        h2 { margin: 5px 0 15px 0; color: #89b4fa; letter-spacing: 1px; text-transform: uppercase; font-size: 1.5rem;}
        
        .panel { 
            background: var(--bg-card); 
            width: 100%; 
            max-width: 400px; 
            padding: 15px; 
            border-radius: 8px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.5); 
            border-bottom: 3px solid var(--primary);
            box-sizing: border-box;
        }

        .sound-selector { margin-bottom: 15px; text-align: left; }
        .sound-selector label { font-size: 0.85rem; color: #888; font-weight: bold; margin-bottom: 5px; display: block; text-transform: uppercase;}
        select { 
            width: 100%; padding: 10px; font-size: 1rem; border-radius: 4px; 
            border: 1px solid #333; background: #26262b; color: white; outline: none; 
        }

        .btn { 
            width: 100%; padding: 15px; font-size: 1.1rem; font-weight: bold; color: white; 
            border: none; border-radius: 4px; cursor: pointer; text-transform: uppercase; 
            margin-bottom: 10px;
        }
        .btn-start { background: var(--primary); }
        .btn-start:active { background: #1d4ed8; }
        
        /* Contenedor de la cámara */
        #contenedor-lector { display: none; width: 100%; }
        #reader { width: 100%; border-radius: 6px; overflow: hidden; border: 2px solid var(--primary); background: black; margin-bottom: 15px; }
        
        /* Controles cuando la cámara está activa */
        .camera-controls { display: flex; gap: 10px; width: 100%; }
        .btn-close { background: var(--danger); width: 35%; padding: 15px 0; font-size: 1rem;}
        .btn-scan { background: var(--success); flex-grow: 1; }
        .btn-scanning { background: #d08c00 !important; }

        #status { 
            margin-top: 15px; font-weight: bold; color: #888; font-size: 0.95rem; 
            background: #181825; padding: 10px; border-radius: 4px; text-align: center;
            border: 1px solid #333;
        }
    </style>
</head>
<body>
    <h2>GACRUX SCANNER</h2>
    
    <div class="panel">
        <div class="sound-selector" id="div-sonidos">
            <label for="soundSelect">Tono de confirmación:</label>
            <select id="soundSelect">
                <option value="beep">Bip Clásico</option>
                <option value="coin">Moneda de Mario</option>
                <option value="boing">Salto Boing</option>
                <option value="magic">Toque Mágico</option>
                <option value="fart">Pedito Gracioso</option>
            </select>
        </div>

        <button id="btn-encender" class="btn btn-start" onclick="encenderCamara()">ENCENDER CÁMARA</button>

        <div id="contenedor-lector">
            <div id="reader"></div>
            <div class="camera-controls">
                <button class="btn btn-close" onclick="apagarCamara()">CERRAR</button>
                <button id="btn-disparar" class="btn btn-scan" onclick="activarDisparo()">ESCANEAR</button>
            </div>
        </div>
        
        <div id="status">Sistema en espera.</div>
    </div>

    <script>
        // === SINTETIZADOR DE SONIDO ===
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

        function playSound() {
            if (audioCtx.state === 'suspended') audioCtx.resume();
            
            const type = document.getElementById("soundSelect").value;
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            const now = audioCtx.currentTime;

            if (type === 'beep') {
                oscillator.type = 'sine';
                oscillator.frequency.setValueAtTime(880, now);
                gainNode.gain.setValueAtTime(1, now);
                gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
                oscillator.start(now);
                oscillator.stop(now + 0.15);
            } 
            else if (type === 'coin') {
                oscillator.type = 'square';
                oscillator.frequency.setValueAtTime(987.77, now); 
                oscillator.frequency.setValueAtTime(1318.51, now + 0.1); 
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

        // === LÓGICA DEL LECTOR DE CÓDIGOS ===
        let html5QrCode = null;
        let scannerActivo = false;

        function encenderCamara() {
            if (audioCtx.state === 'suspended') audioCtx.resume();
            
            document.getElementById('btn-encender').style.display = 'none';
            document.getElementById('div-sonidos').style.display = 'none';
            document.getElementById('contenedor-lector').style.display = 'block';
            document.getElementById('status').innerText = "Cámara lista. Presiona ESCANEAR para leer.";
            document.getElementById('status').style.color = "#888";
            
            html5QrCode = new Html5Qrcode("reader");
            
            // Configuración optimizada para celular
            const config = { fps: 15, qrbox: { width: 250, height: 100 } };
            
            html5QrCode.start({ facingMode: "environment" }, config, 
                (decodedText) => {
                    // Solo leer si el usuario presionó "ESCANEAR"
                    if (scannerActivo) {
                        scannerActivo = false;
                        playSound();
                        
                        const btnDisparar = document.getElementById('btn-disparar');
                        btnDisparar.innerText = "ENVIANDO...";
                        btnDisparar.classList.remove("btn-scanning");
                        
                        const statusDiv = document.getElementById('status');
                        statusDiv.innerText = "Transmitiendo a PC...";
                        statusDiv.style.color = "#f9e2af";

                        // Enviar a Aiven a través de Flask
                        fetch('/escanear', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ codigo: decodedText })
                        })
                        .then(res => res.json())
                        .then(data => {
                            statusDiv.innerText = "¡Enviado! " + decodedText;
                            statusDiv.style.color = "#4caf50";
                            setTimeout(() => { btnDisparar.innerText = "ESCANEAR"; }, 500);
                        })
                        .catch(err => {
                            statusDiv.innerText = "Error de red al enviar.";
                            statusDiv.style.color = "#ff4a4a";
                            setTimeout(() => { btnDisparar.innerText = "ESCANEAR"; }, 1000);
                        });
                    }
                },
                (errorMessage) => { /* Ignorar errores de no lectura por frame */ }
            ).catch(err => {
                alert("Error al iniciar la cámara. Revisa los permisos.");
                apagarCamara();
            });
        }

        function activarDisparo() {
            if (!html5QrCode) return;
            if (audioCtx.state === 'suspended') audioCtx.resume();
            scannerActivo = true;
            
            const btnDisparar = document.getElementById('btn-disparar');
            btnDisparar.innerText = "ENFOCANDO...";
            btnDisparar.classList.add("btn-scanning");
            document.getElementById('status').innerText = "Acerca el código a la cámara...";
            document.getElementById('status').style.color = "#89b4fa";
        }

        function apagarCamara() {
            if (html5QrCode) {
                html5QrCode.stop().then(() => {
                    document.getElementById('contenedor-lector').style.display = 'none';
                    document.getElementById('btn-encender').style.display = 'block';
                    document.getElementById('div-sonidos').style.display = 'block';
                    document.getElementById('status').innerText = "Sistema en espera.";
                    document.getElementById('status').style.color = "#888";
                    scannerActivo = false;
                }).catch(err => {});
            }
        }
    </script>
</body>
</html>
"""

# ==========================================
# RUTAS DEL SERVIDOR
# ==========================================
@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/escanear', methods=['POST'])
def escanear():
    data = request.json
    codigo = data.get('codigo')
    
    if not codigo: 
        return jsonify({"error": "No hay código válido"}), 400
    
    try:
        # Inserción directa en el buzón (cola_escaneos)
        conexion = mysql.connector.connect(
            host="mysql-292462b-gacrux-of.a.aivencloud.com", 
            port=19257,
            user="avnadmin", 
            password="AVNS_lJSsblo1fLuMi6cA-yW", 
            database="defaultdb"
        )
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO cola_escaneos (codigo_barras) VALUES (%s)", (codigo,))
        conexion.commit()
        cursor.close()
        conexion.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
