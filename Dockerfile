# Usa una imagen base de Python 3.9 con Alpine
FROM python:3.13-slim-bookworm

# Instalar dependencias del sistema, incluyendo compiladores, herramientas de construcción y Java
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    mesa-utils \
    libglib2.0-0 \
    libx11-6 \
    libfreetype6-dev \
    openjdk-17-jdk \
    build-essential \
    cmake \
    ninja-build \
    linux-headers-$(uname -r) \
    libgcc-12-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-spa \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

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
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:$PORT", "app:app"]
#CMD ["/bin/sh", "-c", "exec gunicorn -w 4 -b 0.0.0.0:$PORT app:app"]
#CMD ["sh", "-c", "gunicorn -w 4 -k gthread --threads 2 -b 0.0.0.0:$PORT app:app"]
