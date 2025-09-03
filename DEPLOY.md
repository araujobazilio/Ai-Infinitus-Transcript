# Deploy no Streamlit Cloud

## Problemas Resolvidos

### 1. Módulos Removidos no Python 3.13
- `No module named 'audioop'`
- `No module named 'pyaudioop'` 
- Problemas com `MoviePy` no ambiente de deploy

### 2. Erro inotify watch limit reached
- **Problema**: `OSError: [Errno 28] inotify watch limit reached`
- **Causa**: Limite de monitoramento de arquivos no Streamlit Cloud
- **Solução**: Configurações otimizadas no `.streamlit/config.toml`

### 3. Soluções Implementadas
- **Extração de áudio usando FFmpeg diretamente**
- **Dependências mínimas**: `openai`, `streamlit`, `python-dotenv`
- **Processamento robusto de vídeos**
- **Configuração otimizada para Streamlit Cloud**

## Arquivos de Configuração

- **`.python-version`**: Python 3.11
- **`runtime.txt`**: Python 3.11 para Streamlit Cloud
- **`requirements.txt`**: Streamlit >=1.38.0 + dependências essenciais
- **`packages.txt`**: ffmpeg (essencial para extração de áudio)
- **`.streamlit/config.toml`**: Configurações otimizadas para Cloud
- **`.gitignore`**: Otimizado para reduzir arquivos monitorados

## Configuração Streamlit Cloud (.streamlit/config.toml)

```toml
[server]
fileWatcherType = "none"  # Desabilita monitoramento de arquivos
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[global]
developmentMode = false
```

## Funcionalidades Disponíveis

✅ **Transcrição de Arquivos de Áudio** (.mp3, .wav, .m4a, .ogg)  
✅ **Processamento Automático de Vídeo** (.mp4, .mov, .avi, .mkv, .webm)  
✅ **Download do Áudio Extraído** - bonus feature  
❌ **Gravação de Microfone** - removido devido a incompatibilidades

## Como Funciona o Processamento de Vídeo

1. **Upload do vídeo** (limite: 1GB)
2. **Extração automática de áudio** usando FFmpeg
3. **Transcrição do áudio** via OpenAI Whisper
4. **Opção de download** do áudio extraído

## Configuração da API Key

No Streamlit Cloud:
- **Nome**: `OPENAI_API_KEY`
- **Valor**: Sua chave API da OpenAI

## Deploy

1. Commit e push dos arquivos atualizados (incluindo `.streamlit/config.toml`)
2. Configure a variável `OPENAI_API_KEY` no Streamlit Cloud
3. Deploy deve funcionar sem erro de inotify watch limit

## Versão Completa

Esta versão oferece **funcionalidade completa** de transcrição de áudio e vídeo, com otimizações específicas para o Streamlit Cloud que resolvem problemas de compatibilidade e limites do sistema.
