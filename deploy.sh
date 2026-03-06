#!/bin/bash
set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Deploy Ai Infinitus Transcript ===${NC}"

# 1. Atualizar e instalar Docker/docker-compose
echo -e "${YELLOW}Instalando Docker e docker-compose...${NC}"
apt-get update
apt-get install -y docker.io docker-compose curl
systemctl enable docker
systemctl start docker

# 2. Clonar repositório (substitua URL abaixo se necessário)
REPO_URL="https://github.com/araujobazilio/Ai-Infinitus-Transcript.git"
if [ -d "Ai-Infinitus-Transcript" ]; then
  echo -e "${YELLOW}Repositório já existe, pulando clone...${NC}"
  cd Ai-Infinitus-Transcript
  git pull
else
  echo -e "${YELLOW}Clonando repositório...${NC}"
  git clone "$REPO_URL"
  cd Ai-Infinitus-Transcript
fi

# 3. Criar .env se não existir
if [ ! -f .env ]; then
  echo -e "${YELLOW}Criando .env...${NC}"
  cat > .env <<EOF
OPENAI_API_KEY=
OPENAI_CONTENT_MODEL=gpt-4o-mini
EOF
  echo -e "${RED}EDITE .env E COLE SUA OPENAI_API_KEY ANTES DE CONTINUAR!${NC}"
  echo -e "${YELLOW}Ex: nano .env${NC}"
  read -p "Pressione Enter após editar .env..."
fi

# 4. Subir container
echo -e "${YELLOW}Construindo e subindo container...${NC}"
docker-compose up -d --build

# 5. Verificar
echo -e "${YELLOW}Verificando status...${NC}"
sleep 10
if curl -f http://localhost:8501/_stcore/health >/dev/null 2>&1; then
  echo -e "${GREEN}✅ App no ar! Acesse: http://$(curl -s ifconfig.me):8501${NC}"
else
  echo -e "${RED}❌ App pode não estar no ar. Verifique logs: docker-compose logs -f${NC}"
fi

echo -e "${GREEN}=== Deploy concluído ===${NC}"
