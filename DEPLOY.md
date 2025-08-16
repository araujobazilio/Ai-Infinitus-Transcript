# Deploy no Streamlit Cloud

## Problemas Resolvidos: audioop e pyaudioop

Os erros `No module named 'audioop'` e `No module named 'pyaudioop'` ocorrem porque o Python 3.13 removeu estes módulos que eram usados pelo `pydub` e `streamlit_webrtc`.

## Solução Implementada

### 1. Versão Simplificada da Aplicação
- **Removida funcionalidade de microfone** (que dependia de audioop/pyaudioop)
- **Mantidas funcionalidades principais**: transcrição de arquivos de áudio e vídeo
- **Dependências reduzidas**: removido `pydub`, `streamlit_webrtc`, `ipykernel`

### 2. Arquivos de Configuração
- **`.python-version`**: Especifica Python 3.11
- **`runtime.txt`**: Define Python 3.11 para o Streamlit Cloud
- **`packages.txt`**: Instala ffmpeg para processamento de vídeo
- **`requirements.txt`**: Dependências mínimas compatíveis

## Funcionalidades Disponíveis

✅ **Transcrição de Arquivos de Áudio** (.mp3, .wav, .m4a, .ogg)  
✅ **Transcrição de Vídeos** (.mp4, .mov, .avi) - extrai áudio automaticamente  
❌ **Gravação de Microfone** - removida temporariamente devido a incompatibilidades

## Configuração da API Key

No Streamlit Cloud, adicione a variável de ambiente:
- **Nome**: `OPENAI_API_KEY`
- **Valor**: Sua chave API da OpenAI

## Deploy

1. Faça commit e push dos arquivos atualizados
2. No Streamlit Cloud, configure a variável de ambiente `OPENAI_API_KEY`
3. O deploy deve funcionar sem erros de módulos ausentes
