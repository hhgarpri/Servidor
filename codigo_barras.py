import os
import re
import cv2
import numpy as np
from pyzxing import BarCodeReader

# Constantes
TEMP_ZOOM_PATH = "temporal_zoom.jpg"
TEMP_BARCODE_PATH = "temporal_barcode.jpg"


def leer_codigo_barras(imagen_path):
    if not os.path.exists(imagen_path):
        print(f"❌ La imagen no existe: {imagen_path}")
        return ""
    
    reader = BarCodeReader()
    resultados = reader.decode(imagen_path)
        
    if not resultados:
        return ""

    for codigo in resultados:
        raw_data = codigo.get("raw")
        if raw_data:
            try:
                if isinstance(raw_data, bytes):
                    return raw_data.decode("utf-8", errors="ignore").replace("\x00", " ").strip()
                return str(raw_data)
            except UnicodeDecodeError:
                return raw_data.decode("ISO-8859-1")

    return ""

def binarizar_negros(imagen, umbral):
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    _, binaria = cv2.threshold(gris, umbral, 255, cv2.THRESH_BINARY)
    return binaria

def detectar_codigo_barras(ruta_imagen):
    print(f"🔍 Cargando imagen desde: {ruta_imagen}")
    
    img_original = cv2.imread(ruta_imagen)
    if img_original is None:
        print("❌ No se pudo cargar la imagen.")
        return None

    lector = BarCodeReader()
    max_zoom_intentos = 5
    umbrales = list(range(80, 120, 10))
    brillo_factor = 1
    for intento in range(max_zoom_intentos):
        escala = 1 + intento * 0.2
        print(f"🔍 Intento con zoom x{escala:.1f}")
        img_escalada = cv2.resize(img_original, None, fx=escala, fy=escala, interpolation=cv2.INTER_LINEAR)
        
        # Aumentar brillo con 0.8 * intento
        if brillo_factor < 1.4:
            brillo_factor = 1 + 0.8 * intento
            img_escalada = np.clip(img_escalada * brillo_factor, 0, 255).astype(np.uint8)

        # Guardar imagen y aplicar filtro de enfoque
        cv2.imwrite(TEMP_ZOOM_PATH, img_escalada)
        img = cv2.imread(TEMP_ZOOM_PATH)
        sharpen_kernel = np.array([[0, -1, 0],
                                   [-1, 5, -1],
                                   [0, -1, 0]])
        sharpened = cv2.filter2D(img, -1, sharpen_kernel)
        cv2.imwrite(TEMP_ZOOM_PATH, sharpened)

        resultado = lector.decode(TEMP_ZOOM_PATH)
        print(f"🔍 Resultado con zoom x{escala:.1f}")

        if resultado and isinstance(resultado, list) and isinstance(resultado[0], dict):
            info = resultado[0]
            formato = info.get("format", b"").decode("utf-8", errors="ignore") if isinstance(info.get("format"), bytes) else str(info.get("format"))
            if formato == "PDF_417":
                raw_data = info.get("raw")
                if raw_data:
                    print(f"✅ Código detectado sin limpieza con zoom x{escala:.1f}")
                    return TEMP_ZOOM_PATH

        # Aplicar binarización directamente sobre la imagen escalada
        for umbral in umbrales:
            binarizada = binarizar_negros(img_escalada, umbral)
            cv2.imwrite(TEMP_BARCODE_PATH, binarizada)
            resultado_mejorado = lector.decode(TEMP_BARCODE_PATH)

            if resultado_mejorado and isinstance(resultado_mejorado[0], dict):
                info_mejorado = resultado_mejorado[0]
                formato_mejorado = info_mejorado.get("format", b"").decode("utf-8", errors="ignore") if isinstance(info_mejorado.get("format"), bytes) else str(info_mejorado.get("format"))
                if formato_mejorado == "PDF_417" and info_mejorado.get("raw"):
                    print(f"✅ Código detectado con limpieza y umbral {umbral} en zoom x{escala:.1f}")
                    return TEMP_BARCODE_PATH
                else:
                    print(f"❌ Formato no válido o código no detectado con umbral {umbral} en zoom x{escala:.1f}")
            else:
                print(f"❌ Falló con umbral {umbral} en zoom x{escala:.1f}")

    print("❌ No se detectó el código de barras después de todos los intentos.")
    return None


def extraer_texto_qr(ruta_imagen=""):
    ubicacion = detectar_codigo_barras(ruta_imagen)
    if not ubicacion:
        return None

    texto = leer_codigo_barras(ubicacion)
    texto = texto.replace("\x00", " ").strip()

    if os.path.exists(TEMP_ZOOM_PATH):
        os.remove(TEMP_ZOOM_PATH)
        print(f"🗑️ Imagen temporal eliminada: {TEMP_ZOOM_PATH}")
    
    if ubicacion != ruta_imagen and os.path.exists(ubicacion):
        os.remove(ubicacion)
        print(f"🗑️ Imagen temporal eliminada: {ubicacion}")

    if re.match(r'^\d{10}\s+PubDSK_1', texto):
        return extraer_datos_cedula(texto)

    elif re.match(r'^I\d+\s+PubDSK_1', texto):
        return extraer_datos_tarjeta_identidad(texto)

    return {"resultado": "No se reconoce el formato del texto"}


def extraer_datos_cedula(texto):
    tipo_Documento = "Cédula Ciudadana"
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
        "Tipo_documento": tipo_Documento,
        "cedula": cedula,
        "apellido1": apellido1,
        "apellido2": apellido2,
        "nombre": nombre,
        "fecha_nacimiento": fecha_nac_fmt,
        "sexo": sexo,
        "tipo_sangre": tipo_sangre
    }


def extraer_datos_tarjeta_identidad(texto):
    tipo_Documento = "Tarjeta de Identidad"
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
        "Tipo_documento": tipo_Documento,
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


