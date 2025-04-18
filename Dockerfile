FROM python:3.9

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
    tesseract-ocr-spa \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Verificación
RUN java -version && tesseract --version

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:$PORT app:app"]
