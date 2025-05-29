# Usa una imagen base ligera de Python
FROM python:3.11-slim

# Instala dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libreoffice \
    fonts-dejavu-core \
    fonts-dejavu \
    ttf-dejavu \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia primero los requerimientos y luego el resto del código
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expone el puerto que usará Flask
EXPOSE 8080

# Comando para iniciar la app (ajusta la ruta si tu app.py está en una subcarpeta)
CMD ["python", "qr-web-app/app.py"]
