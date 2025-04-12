import os
import re
import cv2
import numpy as np
from pyzxing import BarCodeReader

# Constantes
TEMP_ZOOM_PATH = "temporal_zoom.jpg"
TEMP_BARCODE_PATH = "codigo_barras_mejorado.jpg"

def leer_codigo_barras(imagen_path):
    if not os.path.exists(imagen_path):
        print(f"❌ La imagen no existe: {imagen_path}")
        return ""
    
    reader = BarCodeReader()
    resultados = reader.decode(imagen_path)
    
    print(f"🔍 Resultados de la lectura de código de barras: {resultados}")
    
    if not resultados:
        return ""

    for codigo in resultados:
        raw_data = codigo.get("raw")
        if raw_data:
            try:
                if isinstance(raw_data, bytes):
                    return raw_data.decode("latin-1", errors="ignore").replace("\x00", " ").strip()
                return str(raw_data)
            except UnicodeDecodeError:
                return raw_data.decode("utf-8")

    return ""

def binarizar_negros(imagen, umbral=80):
    mascara = np.all(imagen < umbral, axis=2)
    resultado = imagen.copy()
    resultado[mascara] = [0, 0, 0]
    return resultado

def detectar_codigo_barras(ruta_imagen):
    print(f"🔍 Cargando imagen desde: {ruta_imagen}")
    
    img_original = cv2.imread(ruta_imagen)
    if img_original is None:
        print("❌ No se pudo cargar la imagen.")
        return None

    lector = BarCodeReader()

    for intento in range(6):
        escala = 1 + intento * 0.2
        print(f"🔍 Intento con zoom x{escala:.1f}")

        img_escalada = cv2.resize(img_original, None, fx=escala, fy=escala, interpolation=cv2.INTER_LINEAR)
        cv2.imwrite(TEMP_ZOOM_PATH, img_escalada)

        resultado = lector.decode(TEMP_ZOOM_PATH)
        print(f"🔍 Resultado con zoom x{escala:.1f}: {resultado}")
        
        if not resultado or 'parsed' not in resultado[0]:
            print(f"❌ No se detectó código con zoom x{escala:.1f}")
            continue

        info = resultado[0]
        if 'points' in info:
            puntos = [(int(p[0]), int(p[1])) for p in info['points']]
            x_min, x_max = min(p[0] for p in puntos), max(p[0] for p in puntos)
            y_min, y_max = min(p[1] for p in puntos), max(p[1] for p in puntos)

            margen = int(img_escalada.shape[1] * 0.02)
            x_min, x_max = max(0, x_min - margen), min(img_escalada.shape[1], x_max + margen)
            y_min, y_max = max(0, y_min - margen), min(img_escalada.shape[0], y_max + margen)

            recorte = img_escalada[y_min:y_max, x_min:x_max]

            for umbral in range(85, 111, 5):
                recorte_bin = binarizar_negros(recorte, umbral)
                cv2.imwrite(TEMP_BARCODE_PATH, recorte_bin)

                if lector.decode(TEMP_BARCODE_PATH)[0].get("raw"):
                    print(f"✅ Código detectado con zoom x{escala:.1f} y umbral {umbral}")
                    os.remove(TEMP_ZOOM_PATH)
                    return TEMP_BARCODE_PATH

                print(f"❌ No se detectó código con umbral {umbral}")
        else:
            print("⚠️ Código leído, pero sin puntos para recortar.")

    if os.path.exists(TEMP_ZOOM_PATH):
        os.remove(TEMP_ZOOM_PATH)

    print("❌ No se detectó el código de barras.")
    return None

def extraer_texto_qr(ruta_imagen=""):
    ubicacion = detectar_codigo_barras(ruta_imagen)
    if not ubicacion:
        return {"resultado": "No se pudo detectar código de barras"}

    texto = leer_codigo_barras(ubicacion)
    texto = texto.replace("\x00", " ").strip()

    print(f"🔍 Texto extraído del código de barras: {texto}")

    datos = {}

    if re.match(r'^\d{10}\s+PubDSK_1', texto):
        datos = extraer_datos_cedula(texto)

    elif re.match(r'^I\d+\s+PubDSK_1', texto):
        datos = extraer_datos_tarjeta_identidad(texto)

    else:
        datos = {"resultado": "No se reconoce el formato del texto"}

    if os.path.exists(ubicacion):
        os.remove(ubicacion)
        print(f"🗑️ Imagen temporal eliminada: {ubicacion}")

    return datos


def extraer_datos_cedula(texto):
    match = re.search(r'(\d{10})([A-ZÑÁÉÍÓÚÜ]+)', texto)
    if not match:
        return {"resultado": "No se pudo detectar la cédula y el apellido."}

    cedula = match.group(1)
    apellido1 = match.group(2)
    resto = texto[match.end():].strip().split()
    apellido2 = resto[0] if resto else "N/D"

    match_fecha = re.search(r'(19|20)\d{6}', texto)
    fecha_nac = match_fecha.group(0) if match_fecha else "N/D"
    fecha_nac_fmt = f"{fecha_nac[:4]}-{fecha_nac[4:6]}-{fecha_nac[6:]}" if fecha_nac != "N/D" else "N/D"

    nombre = "N/D"
    sexo = "N/D"
    if match_fecha:
        idx_apellido2 = texto.find(apellido2) + len(apellido2)
        idx_fecha = texto.find(fecha_nac)
        nombre_raw = texto[idx_apellido2:idx_fecha].strip()

        match_sexo = re.search(r'0([MF])', nombre_raw)
        if match_sexo:
            sexo = "Masculino" if match_sexo.group(1) == "M" else "Femenino"
            nombre = nombre_raw[:match_sexo.start()].strip()
        else:
            nombre = nombre_raw.strip()

        nombre = re.sub(r'\s+', ' ', nombre)

    match_sangre = re.search(r'(A|B|AB|O)[+-]', texto)
    tipo_sangre = match_sangre.group(0) if match_sangre else "N/D"

    return {
        "cedula": cedula,
        "apellido1": apellido1,
        "apellido2": apellido2,
        "nombre": nombre,
        "fecha_nacimiento": fecha_nac_fmt,
        "sexo": sexo,
        "tipo_sangre": tipo_sangre
    }


def extraer_datos_tarjeta_identidad(texto):
    texto = re.sub(r'\x00+', ' ', texto).strip()
    match_cedula = re.search(r"PubDSK_1\s+(\d{18})", texto)
    cedula = match_cedula.group(1)[8:] if match_cedula else "N/D"

    match_sf = re.search(r"0([MF])(\d{8})", texto)
    if match_sf:
        sexo = "Femenino" if match_sf.group(1) == "F" else "Masculino"
        fecha_nac_fmt = f"{match_sf.group(2)[:4]}-{match_sf.group(2)[4:6]}-{match_sf.group(2)[6:]}"
    else:
        sexo, fecha_nac_fmt = "N/D", "N/D"

    match_sangre = re.search(r"(A|B|AB|O)[+-]", texto)
    tipo_sangre = match_sangre.group(0) if match_sangre else "N/D"

    match_nombres = re.search(r"\d{18}\s+([A-ZÑÁÉÍÓÚÜ]+)\s+([A-ZÑÁÉÍÓÚÜ]+)\s+([A-ZÑÁÉÍÓÚÜ]+)\s+([A-ZÑÁÉÍÓÚÜ]+)", texto)
    if match_nombres:
        apellido1, apellido2 = match_nombres.group(1), match_nombres.group(2)
        nombre = f"{match_nombres.group(3)} {match_nombres.group(4)}"
    else:
        apellido1 = apellido2 = nombre = "N/D"

    return {
        "cedula": cedula,
        "apellido1": apellido1,
        "apellido2": apellido2,
        "nombre": nombre,
        "fecha_nacimiento": fecha_nac_fmt,
        "sexo": sexo,
        "tipo_sangre": tipo_sangre
    }


def imprimir_datos(cedula, apellido1, apellido2, nombre, fecha_nac, sexo, tipo_sangre):
    print("✅ DATOS EXTRAÍDOS")
    print(f"Cédula:           {cedula}")
    print(f"Primer Apellido:  {apellido1}")
    print(f"Segundo Apellido: {apellido2}")
    print(f"Nombres:          {nombre}")
    print(f"Fecha Nac:        {fecha_nac}")
    print(f"Sexo:             {sexo}")
    print(f"Tipo de Sangre:   {tipo_sangre}")

