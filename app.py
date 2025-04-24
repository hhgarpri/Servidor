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

    if not allowed_file(imagen.filename):
        return jsonify({'resultado': None, 'error': 'Archivo no permitido. Solo se permiten imágenes.'}), 400

    try:
        # Leer imagen y verificar tamaño
        contenido = imagen.read()
        tamanio_imagen = len(contenido)
        print(f"Tamaño de la imagen recibida: {tamanio_imagen//1024} Kb")

        if tamanio_imagen == 0:
            return jsonify({'resultado': None, 'error': 'La imagen está vacía'}), 400

        imagen.seek(0)  # Reset para guardar

        carpeta_temporal = "temporal"
        os.makedirs(carpeta_temporal, exist_ok=True)

        nombre_seguro = secure_filename(imagen.filename)
        imagen_path = os.path.join(carpeta_temporal, nombre_seguro)
        imagen.save(imagen_path)

        # Validación básica con OpenCV si quieres añadir
        import cv2
        img_cv = cv2.imread(imagen_path)
        if img_cv is None:
            os.remove(imagen_path)
            return jsonify({'resultado': None, 'error': 'No se pudo abrir la imagen con OpenCV'}), 400

        texto_extraido = detectar_mrz(imagen_path)
        if texto_extraido is None:
            texto_extraido = extraer_texto_qr(imagen_path)

        os.remove(imagen_path)  # Eliminar al final si todo fue bien

        if texto_extraido and isinstance(texto_extraido, dict):
            return jsonify({'resultado': texto_extraido}), 200
        else:
            return jsonify({'resultado': None, 'error': 'No se pudo extraer texto del código QR'}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'resultado': None, 'error': f'Error inesperado: {str(e)}'}), 500


if __name__ == '__main__':
    # El puerto es configurable, por si se ejecuta en diferentes entornos
    port = int(os.environ.get("PORT", 5000))  # Usa el puerto que el entorno asigna
    app.run(host='0.0.0.0', port=port)  # Asegúrate de que el servidor sea accesible externamente