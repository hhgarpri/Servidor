from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from codigo_MRZ import detectar_mrz
from codigo_barras import extraer_texto_qr

app = Flask(__name__)
CORS(app)  # Habilita CORS para todas las rutas

# Extensiones permitidas para archivos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Verifica si el archivo tiene una extensión permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return 'Servidor Flask funcionando. Usa /procesar-imagen para subir una imagen.'

@app.route('/procesar-imagen', methods=['POST'])
def procesar_imagen():
    if 'imagen' not in request.files:
        return jsonify({'resultado': None, 'error': 'No se envió una imagen'}), 400

    imagen = request.files['imagen']

    # Verificar si la imagen tiene una extensión permitida
    if not allowed_file(imagen.filename):
        return jsonify({'resultado': None, 'error': 'Archivo no permitido. Solo se permiten imágenes.'}), 400

    # Obtener y mostrar el tamaño de la imagen en bytes
    tamanio_imagen = len(imagen.read())
    print(f"Tamaño de la imagen recibida: {tamanio_imagen//1024} Kb")
    imagen.seek(0)  # Volver al inicio del stream para poder guardarla

    carpeta_temporal = "temporal"
    os.makedirs(carpeta_temporal, exist_ok=True)

    nombre_seguro = secure_filename(imagen.filename)
    imagen_path = os.path.join(carpeta_temporal, nombre_seguro)
    imagen.save(imagen_path)

    try:
        texto_extraido = detectar_mrz(imagen_path)
        if texto_extraido is None:
            texto_extraido = extraer_texto_qr(imagen_path)
    except Exception as e:
        os.remove(imagen_path)
        return jsonify({'resultado': None, 'error': str(e)}), 500

    os.remove(imagen_path)

    if texto_extraido and isinstance(texto_extraido, dict):
        return jsonify({'resultado': texto_extraido}), 200
    else:
        return jsonify({'resultado': None, 'error': 'No se pudo extraer texto del código QR'}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
