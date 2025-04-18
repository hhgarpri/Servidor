FROM python:3.9-slim-buster

# 1. Instalar herramientas necesarias para usar apt
RUN apt-get update && apt-get install -y \
    gnupg \
    wget \
    curl \
    lsb-release \
    ca-certificates

# 2. Instalar dependencias del sistema y Tesseract con idiomas
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    mesa-utils \
    libglib2.0-0 \
    libx11-6 \
    libfreetype6-dev \
    openjdk-11-jdk \
    build-essential \
    cmake \
    ninja-build \
    libgcc-9-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-spa && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Verifica que Java y Tesseract están instalados
RUN java -version && tesseract --version

# Crear directorio de trabajo
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer puerto (si usas Flask o Gunicorn)
EXPOSE 5000

# Comando final
CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:$PORT app:app"]
