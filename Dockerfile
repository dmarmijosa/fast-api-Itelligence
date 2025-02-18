# Usa la imagen oficial de Python
FROM python:3.10

# Instalar dependencias necesarias para Ollama
RUN apt update && apt install -y curl && \
    curl -fsSL https://ollama.ai/install.sh | sh

# Crear y establecer el directorio de trabajo
WORKDIR /app

# Iniciar Ollama en segundo plano y luego descargar el modelo
RUN ollama serve & sleep 5 && ollama pull deepseek-r1:7b

# Copiar archivos al contenedor
COPY . .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto de FastAPI
EXPOSE 8000

# Iniciar Ollama en segundo plano y luego ejecutar la API
CMD ollama serve & uvicorn main:app --host 0.0.0.0 --port 8000 --reload
