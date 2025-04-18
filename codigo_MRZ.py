import pytesseract
from PIL import Image
import re
from io import BytesIO

def filtrar_negro(imagen, umbral):
    imagen = imagen.convert("L")
    imagen = imagen.point(lambda x: 0 if x < umbral else 255, '1')
    imagen_mostrar = imagen.convert("L")
    buffer = BytesIO()
    imagen_mostrar.save(buffer, format='PNG')
    return imagen_mostrar

def limpiar_linea_mrz(linea):
    return re.sub(r'[^A-Z0-9<]', '', linea)

def extraer_lineas_mrz_validas(lineas):
    lineas_limpias = [limpiar_linea_mrz(l) for l in lineas]
    for i in range(len(lineas_limpias) - 2):
        if all(28 <= len(lineas_limpias[j]) <= 32 for j in range(i, i + 3)):
            return [l[:30] for l in lineas_limpias[i:i+3]]
    return None

def detectar_mrz(ruta_imagen):
    print(f"🔍 Cargando imagen desde: {ruta_imagen}")
    imagen = Image.open(ruta_imagen)

    for umbral in range(200, 130, -10):  # 200, 190, ..., 140
        print(f"🌓 Probando con umbral: {umbral}")
        imagen_filtrada = filtrar_negro(imagen, umbral)
        texto_crudo = pytesseract.image_to_string(imagen_filtrada, lang='eng+spa')

        if "<" not in texto_crudo:
            print("❌ No se detectaron signos '<'. No parece haber MRZ.")
            return None

        lineas = [linea.strip() for linea in texto_crudo.strip().split('\n') if linea.strip()]
        mrz = extraer_lineas_mrz_validas(lineas)

        if mrz:
            print("✅ MRZ detectado con éxito.")
            break
        else:
            print("⏬ MRZ incompleto, bajando umbral...")
            

    if not mrz:
        print("⚠️ No se identificaron los datos de la Cedula")
        return False

    linea2 = mrz[1]
    fecha_raw = linea2[0:6]
    yy, mm, dd = fecha_raw[0:2], fecha_raw[2:4], fecha_raw[4:6]
    anio = f"19{yy}" if int(yy) >= 25 else f"20{yy}"
    fecha_nac_fmt = f"{anio}-{mm}-{dd}"
    sexo = linea2[7]
    if sexo == "M":
        sexo = 'Masculino'
    elif sexo == "F":
        sexo = 'Femenino'
    else:
        sexo = ''

    inicio = linea2.find("C0L")
    fin = linea2.find("<", inicio)
    cedula = linea2[inicio + 3:fin] if inicio != -1 and fin != -1 else ""
    tipo_sangre = ""  # Puedes implementar esta parte si conoces el formato

    linea3 = mrz[2].replace('<', ' ').strip()
    partes = linea3.split()
    apellido1 = partes[0] if len(partes) > 0 else ""
    apellido2 = partes[1] if len(partes) > 1 else ""
    nombre = ' '.join(partes[2:]) if len(partes) > 2 else ""

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
