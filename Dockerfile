# Usa imagem oficial Python 3.12 slim
FROM python:3.12-slim

# Define ambiente não interativo
ENV DEBIAN_FRONTEND=noninteractive

# Instala FFmpeg e dependências de sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Define workdir
WORKDIR /app

# Copia requirements e instala deps Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o app
COPY main.py .
COPY templates/ templates/

# Cria pasta /temp com permissões
RUN mkdir -p /temp && chmod 777 /temp

# Expõe porta
EXPOSE 8000

# Comando para rodar o FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
