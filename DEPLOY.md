# Deploy no Streamlit Cloud

## Problema Resolvido: pyaudioop

O erro `No module named 'pyaudioop'` ocorre porque o Python 3.13 removeu este módulo que é usado pelo `pydub`.

## Solução Implementada

1. **`.python-version`** - Especifica Python 3.11 para o ambiente
2. **`runtime.txt`** - Define a versão exata do Python (3.11.9) 
3. **`packages.txt`** - Instala ffmpeg necessário para processamento de áudio

## Arquivos de Configuração Criados

- `.python-version`: Força uso do Python 3.11
- `runtime.txt`: Versão específica para deploy
- `packages.txt`: Dependências do sistema (ffmpeg)

## Configuração da API Key

No Streamlit Cloud, adicione a variável de ambiente:
- **Nome**: `OPENAI_API_KEY`
- **Valor**: Sua chave API da OpenAI

## Deploy

1. Faça commit e push dos novos arquivos
2. No Streamlit Cloud, configure a variável de ambiente
3. O deploy deve funcionar com Python 3.11
