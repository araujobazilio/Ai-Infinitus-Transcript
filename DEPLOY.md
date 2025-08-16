# Deploy no Streamlit Cloud

## Problemas Resolvidos

### 1. Módulos Removidos no Python 3.13
- `No module named 'audioop'`
- `No module named 'pyaudioop'` 
- Problemas com `MoviePy` no ambiente de deploy

### 2. Solução: FFmpeg para Processamento de Vídeo
- **Extração de áudio usando FFmpeg diretamente**
- **Dependências mínimas**: `openai`, `streamlit`, `python-dotenv`
- **Processamento robusto de vídeos**

## Arquivos de Configuração

- **`.python-version`**: Python 3.11
- **`runtime.txt`**: Python 3.11 para Streamlit Cloud
- **`requirements.txt`**: 3 dependências essenciais
- **`packages.txt`**: ffmpeg (essencial para extração de áudio)

## Funcionalidades Disponíveis

✅ **Transcrição de Arquivos de Áudio** (.mp3, .wav, .m4a, .ogg)  
✅ **Processamento Automático de Vídeo** (.mp4, .mov, .avi, .mkv, .webm)  
✅ **Download do Áudio Extraído** - bonus feature  
❌ **Gravação de Microfone** - removido devido a incompatibilidades

## Como Funciona o Processamento de Vídeo

1. **Upload do vídeo** (limite: 200MB)
2. **Extração automática de áudio** usando FFmpeg
3. **Transcrição do áudio** via OpenAI Whisper
4. **Opção de download** do áudio extraído

## Configuração da API Key

No Streamlit Cloud:
- **Nome**: `OPENAI_API_KEY`
- **Valor**: Sua chave API da OpenAI

## Deploy

1. Commit e push dos arquivos atualizados
2. Configure a variável `OPENAI_API_KEY` no Streamlit Cloud
3. Deploy deve funcionar com processamento completo de vídeo

## Versão Completa

Esta versão oferece **funcionalidade completa** de transcrição de áudio e vídeo, mantendo compatibilidade com o ambiente do Streamlit Cloud através do uso direto do FFmpeg.
