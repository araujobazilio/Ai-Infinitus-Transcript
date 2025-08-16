from pathlib import Path
import streamlit as st
import openai
from dotenv import load_dotenv, find_dotenv
import os
import tempfile
import subprocess
import shutil

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

def extrair_audio_com_ffmpeg(caminho_video, caminho_audio):
    """Extrai áudio de vídeo usando FFmpeg"""
    try:
        # Verifica se FFmpeg está disponível
        if not shutil.which('ffmpeg'):
            return False, "FFmpeg não encontrado no sistema"
        
        # Comando FFmpeg para extrair áudio
        comando = [
            'ffmpeg',
            '-i', caminho_video,
            '-vn',  # Sem vídeo
            '-acodec', 'mp3',  # Codec de áudio MP3
            '-ab', '192k',  # Bitrate
            '-ar', '44100',  # Sample rate
            '-y',  # Sobrescrever arquivo se existir
            caminho_audio
        ]
        
        # Executa o comando
        resultado = subprocess.run(
            comando, 
            capture_output=True, 
            text=True,
            timeout=300  # Timeout de 5 minutos
        )
        
        if resultado.returncode == 0:
            return True, "Áudio extraído com sucesso"
        else:
            return False, f"Erro FFmpeg: {resultado.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Timeout: Vídeo muito longo para processar"
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"

def transcreve_tab_video():
    """Aba para transcrição de vídeos"""
    st.info("📹 Faça upload de um arquivo de vídeo para extrair o áudio e transcrever automaticamente")
    
    prompt_input = st.text_input('(opcional) Digite um prompt para melhorar a transcrição', key='input_video')
    arquivo_video = st.file_uploader('Selecione um arquivo de vídeo', type=['mp4', 'mov', 'avi', 'mkv', 'webm'])
    
    if arquivo_video is not None:
        # Verifica tamanho do arquivo (limite de 200MB)
        tamanho_mb = len(arquivo_video.getvalue()) / (1024 * 1024)
        if tamanho_mb > 200:
            st.error(f"❌ Arquivo muito grande ({tamanho_mb:.1f}MB). Limite: 200MB")
            return
        
        with st.spinner('🎬 Processando vídeo e extraindo áudio...'):
            try:
                # Cria arquivos temporários
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                    temp_video.write(arquivo_video.getvalue())
                    temp_video_path = temp_video.name
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
                    temp_audio_path = temp_audio.name
                
                # Extrai áudio usando FFmpeg
                sucesso, mensagem = extrair_audio_com_ffmpeg(temp_video_path, temp_audio_path)
                
                if sucesso:
                    st.success("✅ Áudio extraído com sucesso!")
                    
                    # Transcreve o áudio
                    with st.spinner('🎵 Transcrevendo áudio...'):
                        with open(temp_audio_path, 'rb') as audio_file:
                            transcricao = transcreve_audio(audio_file, prompt_input)
                        
                        st.success("✅ Transcrição concluída!")
                        st.write("### Resultado:")
                        st.write(transcricao)
                        
                        # Opção para download do áudio extraído
                        with open(temp_audio_path, 'rb') as audio_file:
                            st.download_button(
                                label="📥 Download do áudio extraído",
                                data=audio_file.read(),
                                file_name=f"audio_{arquivo_video.name}.mp3",
                                mime="audio/mpeg"
                            )
                else:
                    st.error(f"❌ Erro ao extrair áudio: {mensagem}")
                    st.info("💡 Tente converter o vídeo online e usar a aba de áudio:")
                    st.markdown("""
                    - [Online Audio Converter](https://online-audio-converter.com/)
                    - [CloudConvert](https://cloudconvert.com/mp4-to-mp3)
                    """)
                
                # Limpa arquivos temporários
                try:
                    os.unlink(temp_video_path)
                    os.unlink(temp_audio_path)
                except:
                    pass
                    
            except Exception as e:
                st.error(f"❌ Erro ao processar vídeo: {str(e)}")

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
