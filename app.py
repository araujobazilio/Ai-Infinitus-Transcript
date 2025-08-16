from pathlib import Path
import streamlit as st
import openai
from dotenv import load_dotenv, find_dotenv
import os
import tempfile

# Carrega as variáveis de ambiente
_ = load_dotenv(find_dotenv())

PASTA_TEMP = Path(__file__).parent / 'temp'
PASTA_TEMP.mkdir(exist_ok=True)
ARQUIVO_AUDIO_TEMP = PASTA_TEMP / 'audio.mp3'

# Inicializa o cliente OpenAI com a chave API
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("❌ Chave API da OpenAI não encontrada! Verifique o arquivo .env")
    st.stop()

client = openai.OpenAI(api_key=api_key)

def transcreve_audio(arquivo_audio, prompt):
    """Transcreve áudio usando a API da OpenAI"""
    transcricao = client.audio.transcriptions.create(
        model='whisper-1',
        language='pt',
        response_format='text',
        file=arquivo_audio,
        prompt=prompt,
    )
    return transcricao

def transcreve_tab_video():
    """Aba para orientações sobre vídeos"""
    st.info("📹 Para transcrever vídeos, primeiro extraia o áudio usando um conversor online")
    
    st.markdown("""
    ### Como transcrever vídeos:
    
    1. **Extraia o áudio do vídeo** usando uma dessas opções:
       - [Online Audio Converter](https://online-audio-converter.com/)
       - [CloudConvert](https://cloudconvert.com/mp4-to-mp3)
       - [Convertio](https://convertio.co/mp4-mp3/)
    
    2. **Faça upload do arquivo de áudio** na aba "🎵 Áudio"
    
    3. **Aguarde a transcrição** ser processada
    """)
    
    st.warning("⚠️ A funcionalidade de processamento automático de vídeo foi temporariamente desabilitada para garantir compatibilidade com o ambiente de deploy.")

# TRANSCREVE AUDIO =====================================
def transcreve_tab_audio():
    """Aba para transcrição de arquivos de áudio"""
    st.info("🎵 Faça upload de um arquivo de áudio (.mp3, .wav, .m4a) para transcrição")
    
    prompt_input = st.text_input('(opcional) Digite um prompt para melhorar a transcrição', key='input_audio')
    arquivo_audio = st.file_uploader('Selecione um arquivo de áudio', type=['mp3', 'wav', 'm4a', 'ogg'])
    
    if arquivo_audio is not None:
        with st.spinner('🎵 Transcrevendo áudio...'):
            try:
                transcricao = transcreve_audio(arquivo_audio, prompt_input)
                st.success("✅ Transcrição concluída!")
                st.write("### Resultado:")
                st.write(transcricao)
            except Exception as e:
                st.error(f"❌ Erro ao transcrever áudio: {str(e)}")

# MAIN =====================================
def main():
    st.set_page_config(
        page_title="Ai Infinitus Transcript",
        page_icon="🎙️",
        layout="wide"
    )
    
    st.header('Bem-vindo ao Ai Infinitus Transcript 🎙️', divider=True)
    st.markdown('#### Transcreva áudio de vídeos e arquivos de áudio usando IA')
    
    # Removemos a aba de microfone para evitar problemas com audioop/pyaudioop
    tab_video, tab_audio = st.tabs(['📹 Vídeo', '🎵 Áudio'])
    
    with tab_video:
        transcreve_tab_video()
    with tab_audio:
        transcreve_tab_audio()

if __name__ == '__main__':
    main()
