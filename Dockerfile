# Usa una imagen base de Python 3.9 con Alpine
FROM python:3.9-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    && apt-get install -y mesa-utils \
    && apt-get install -y libglib2.0-0 \
    && apt-get install -y libx11-6 \
    && apt-get install -y libfreetype6-dev \
    && apt-get install -y openjdk-11-jdk \
    && apt-get install -y build-essential \
    && apt-get install -y cmake \
    && apt-get install -y ninja-build \
    && apt-get install -y libgcc-9-dev \
    && apt-get install -y tesseract-ocr \
    && apt-get install -y tesseract-ocr-eng \
    && apt-get install -y tesseract-ocr-spa \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Verificar que Java está instalado correctamente
RUN java -version

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el archivo requirements.txt
COPY requirements.txt /app/

# Instalar las dependencias de Python desde el archivo requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código fuente
COPY . /app

# Exponer el puerto que la aplicación usará
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:$PORT app:app"]

