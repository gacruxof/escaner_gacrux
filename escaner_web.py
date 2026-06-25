from flask import Flask, render_template_string, request, jsonify
import mysql.connector

app = Flask(__name__)

# Esta es la página web que verá tu celular
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
        h2 { color: #89b4fa; }
        #reader { width: 100%; max-width: 400px; margin: 0 auto; border: 3px solid #89b4fa; border-radius: 12px; overflow: hidden; background: white;}
        #status { margin-top: 20px; font-weight: bold; color: #a6e3a1; font-size: 1.2em; padding: 10px; border-radius: 8px; background: #1e1e2e; box-shadow: 0 4px 6px rgba(0,0,0,0.3);}
        .logo { width: 80px; margin-bottom: -10px; }
    </style>
</head>
<body>
    <h2>🚀 GACRUX SCANNER</h2>
    <div id="reader"></div>
    <div id="status">Enfoca un código de barras...</div>

    <script>
        let escaneando = true;

        function onScanSuccess(decodedText, decodedResult) {
            if (!escaneando) return;
            escaneando = false; // Pausamos la cámara un segundo para no mandar 10 veces el mismo código
            
            let statusDiv = document.getElementById('status');
            statusDiv.innerText = "⏳ Enviando a la PC: " + decodedText;
            statusDiv.style.color = "#f9e2af";

            // Enviar a nuestro servidor Flask
            fetch('/escanear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ codigo: decodedText })
            })
            .then(response => response.json())
            .then(data => {
                statusDiv.innerText = "✅ " + decodedText + " ¡Añadido!";
                statusDiv.style.color = "#a6e3a1";
                // Reactivamos la cámara después de 1.5 segundos
                setTimeout(() => { escaneando = true; statusDiv.innerText = "Enfoca el siguiente código..."; }, 1500);
            })
            .catch(err => {
                statusDiv.innerText = "❌ Error al enviar";
                statusDiv.style.color = "#f38ba8";
                setTimeout(() => { escaneando = true; }, 1500);
            });
        }

        // Configuración del lector (acepta códigos 1D como EAN-13)
        let html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: {width: 250, height: 100} }, false);
        html5QrcodeScanner.render(onScanSuccess);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Cuando entres desde el celular, te sirve la página HTML
    return render_template_string(HTML_PAGE)

@app.route('/escanear', methods=['POST'])
def escanear():
    # Cuando la cámara detecta algo, manda los datos aquí y los sube a Aiven
    data = request.json
    codigo = data.get('codigo')
    if not codigo: 
        return jsonify({"error": "No hay código"}), 400
    
    try:
        conexion = mysql.connector.connect(
            host="mysql-292462b-gacrux-of.a.aivencloud.com", port=19257,
            user="avnadmin", password="AVNS_lJSsblo1fLuMi6cA-yW", database="defaultdb"
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
    # Ejecuta el servidor web
    app.run(host='0.0.0.0', port=5000)