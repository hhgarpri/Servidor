from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from codigo_barras import extraer_texto_qr

app = Flask(__name__)
CORS(app)  # <- Habilita CORS para todas las rutas

@app.route('/procesar-imagen', methods=['POST'])
def procesar_imagen():
    if 'imagen' not in request.files:
        return jsonify({'resultado': None, 'error': 'No se envió una imagen'}), 400

    imagen = request.files['imagen']
    carpeta_temporal = "temporal"
    os.makedirs(carpeta_temporal, exist_ok=True)

    nombre_seguro = secure_filename(imagen.filename)
    imagen_path = os.path.join(carpeta_temporal, nombre_seguro)
    imagen.save(imagen_path)

    texto_extraido = extraer_texto_qr(imagen_path)
    os.remove(imagen_path)

    if texto_extraido and isinstance(texto_extraido, dict):
        return jsonify({'resultado': texto_extraido}), 200
    else:
        return jsonify({'resultado': None, 'error': 'No se pudo extraer texto'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
