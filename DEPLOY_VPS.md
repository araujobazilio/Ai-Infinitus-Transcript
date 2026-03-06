# Deploy na VPS via Docker

## Pré-requisitos
- Docker e docker-compose instalados na VPS.
- Acesso SSH à VPS.
- Chave da OpenAI (`OPENAI_API_KEY`).

## Passos

### 1. Preparar a VPS
```bash
# Instalar Docker (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
# Re-inicie sessão ou rode: newgrp docker
```

### 2. Clonar o repositório
```bash
git clone <URL-DO-SEU-REPO>
cd Ai-Infinitus-Transcript
```

### 3. Criar o arquivo .env
```bash
cp .env.example .env
# Edite .env e preencha sua OPENAI_API_KEY
nano .env
```
Conteúdo mínimo de `.env`:
```ini
OPENAI_API_KEY=sua_chave_aqui
OPENAI_CONTENT_MODEL=gpt-4o-mini
```

### 4. Subir o container
```bash
docker-compose up -d
```

### 5. Verificar logs (se necessário)
```bash
docker-compose logs -f
```

### 6. Acessar o app
- URL: `http://<IP_DA_VPS>:8501`
- O upload de até 1 GB estará disponível (configurado em `.streamlit/config.toml`).

## Proxy reverso (opcional)
Para HTTPS e domínio personalizado, configure nginx ou Caddy apontando para `http://localhost:8501`.

## Manutenção
- Parar: `docker-compose down`
- Rebuild após mudanças: `docker-compose up -d --build`
- Limpar imagens antigas: `docker image prune -f`
