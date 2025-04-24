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

    mrz = None
    cedula_detectada = False
    encontrado_simbolo_mrz = False

    for umbral in range(220, 125, -10):  # Va de 220 a 130, paso de -10
        print(f"🌓 Probando con umbral: {umbral}")
        imagen_filtrada = filtrar_negro(imagen, umbral)
        texto_crudo = pytesseract.image_to_string(imagen_filtrada, lang='eng+spa')

        if not encontrado_simbolo_mrz and umbral >= 200:
            if "<" not in texto_crudo:
                print("❌ No se detectaron signos '<'. Intentando con menor umbral...")
                continue
            else:
                encontrado_simbolo_mrz = True  # Habilita búsqueda completa

        elif not encontrado_simbolo_mrz and umbral < 200:
            print("❌ No se encontró el signo '<' hasta el umbral 200. Cancelando búsqueda.")
            return None

        lineas = [linea.strip() for linea in texto_crudo.strip().split('\n') if linea.strip()]
        mrz = extraer_lineas_mrz_validas(lineas)

        if mrz:
            print("✅ MRZ detectado con éxito.")
            tipo_mrz = ""
            primera_linea = mrz[0].upper()

            try:
                if "PC" in primera_linea:
                    tipo_mrz = "Permiso Temporal"
                    linea1 = mrz[0]
                    linea2 = mrz[1]
                    linea3 = mrz[2]

                    fecha_raw = linea2[0:6]
                    if not fecha_raw.isdigit():
                        raise ValueError("La fecha de nacimiento no es válida")

                    yy, mm, dd = fecha_raw[0:2], fecha_raw[2:4], fecha_raw[4:6]
                    anio = f"19{yy}" if int(yy) >= 25 else f"20{yy}"
                    fecha_nac_fmt = f"{anio}-{mm}-{dd}"

                    sexo = linea2[7]
                    sexo = 'Masculino' if sexo == 'M' else 'Femenino' if sexo == 'F' else ''

                    inicio = linea1.find("COL") if "COL" in linea1 else linea1.find("C0L")
                    fin = linea1.find("<", inicio)
                    cedula = linea1[inicio + 3:fin] if inicio != -1 and fin != -1 else ""

                    if cedula:
                        cedula_detectada = True

                    partes = linea3.replace('<', ' ').strip().split()
                    apellido1 = partes[0] if len(partes) > 0 else ""
                    apellido2 = partes[1] if len(partes) > 1 else ""
                    nombre = ' '.join(partes[2:]) if len(partes) > 2 else ""

                elif "CC" in primera_linea or "C0L" in primera_linea:
                    tipo_mrz = "Cédula Ciudadana"
                    linea2 = mrz[1]
                    linea3 = mrz[2]

                    fecha_raw = linea2[0:6]
                    if not fecha_raw.isdigit():
                        raise ValueError("La fecha de nacimiento no es válida")

                    yy, mm, dd = fecha_raw[0:2], fecha_raw[2:4], fecha_raw[4:6]
                    anio = f"19{yy}" if int(yy) >= 25 else f"20{yy}"
                    fecha_nac_fmt = f"{anio}-{mm}-{dd}"

                    sexo = linea2[7]
                    sexo = 'Masculino' if sexo == 'M' else 'Femenino' if sexo == 'F' else ''

                    inicio = linea2.find("C0L") if "C0L" in linea2 else linea2.find("COL")
                    fin = linea2.find("<", inicio)
                    cedula = linea2[inicio + 3:fin] if inicio != -1 and fin != -1 else ""

                    if cedula:
                        cedula_detectada = True

                    partes = linea3.replace('<', ' ').strip().split()
                    apellido1 = partes[0] if len(partes) > 0 else ""
                    apellido2 = partes[1] if len(partes) > 1 else ""
                    nombre = ' '.join(partes[2:]) if len(partes) > 2 else ""

                else:
                    tipo_mrz = "Desconocido"
                    continue

                if cedula_detectada:
                    return {
                        "Tipo_documento": tipo_mrz,
                        "cedula": cedula,
                        "apellido1": apellido1,
                        "apellido2": apellido2,
                        "nombre": nombre,
                        "fecha_nacimiento": fecha_nac_fmt,
                        "sexo": sexo,
                        "tipo_sangre": "",
                        "mrz_crudo": mrz
                    }
                else:
                    print("⚠️ MRZ detectado pero no se encontró la cédula. Bajando umbral...")

            except Exception as e:
                print(f"❌ Error al procesar los datos del MRZ: {e}")
                continue

    print("❌ No se pudo detectar la cédula tras probar todos los umbrales.")
    return {"error": "No se pudo extraer una cédula válida del MRZ", "mrz_crudo": mrz if mrz else []}


def imprimir_datos(cedula, apellido1, apellido2, nombre, fecha_nac, sexo, tipo_sangre):
    print("✅ DATOS EXTRAÍDOS")
    print(f"Cédula:           {cedula}")
    print(f"Primer Apellido:  {apellido1}")
    print(f"Segundo Apellido: {apellido2}")
    print(f"Nombres:          {nombre}")
    print(f"Fecha Nac:        {fecha_nac}")
    print(f"Sexo:             {sexo}")
    print(f"Tipo de Sangre:   {tipo_sangre}")
