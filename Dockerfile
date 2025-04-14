# Usa una imagen base de Python 3.9 con Alpine
FROM python:3.9-alpine

# Instalar dependencias del sistema, incluyendo compiladores, herramientas de construcción y Java
RUN apk update && apk add --no-cache \
    bash \
    mesa-gl \
    glib \
    libx11 \
    freetype-dev \
    openjdk11 \
    build-base \
    cmake \
    ninja \
    linux-headers \
    libgcc \
    && rm -rf /var/cache/apk/*

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
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
