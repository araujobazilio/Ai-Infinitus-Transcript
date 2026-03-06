# Usa imagem oficial Python 3.12 (compatível com Streamlit e FFmpeg)
FROM python:3.12-slim

# Define ambiente não interativo para evitar prompts
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
COPY app.py .

# Cria pasta /temp com permissões
RUN mkdir -p /temp && chmod 777 /temp

# Expõe porta do Streamlit
EXPOSE 8501

# Comando para rodar o app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.fileWatcherType=none"]
