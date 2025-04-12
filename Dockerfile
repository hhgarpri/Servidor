# Usar la imagen base de Amazon Corretto 22 (Alpine)
FROM amazoncorretto:22.0.2-alpine-jdk

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar todo el contenido del proyecto al contenedor
COPY . /app

# Instalar Python 3 y pip
RUN apk add --no-cache python3 py3-pip gcc musl-dev python3-dev libffi-dev

# Instalar dependencias de Python (requirements.txt debe existir)
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto del servidor Flask
EXPOSE 5000

# Comando por defecto: ejecutar el archivo JAR generado por Maven
CMD ["java", "-jar", "target/python-backend-1.0.0.jar"]
