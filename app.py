from pathlib import Path
import streamlit as st
import openai
from dotenv import load_dotenv, find_dotenv
import os
import tempfile
import subprocess
import shutil
import math
import json
import html
from typing import Any, Dict, List

# Carrega as variáveis de ambiente
_ = load_dotenv(find_dotenv())

PASTA_TEMP = Path(__file__).parent / 'temp'
PASTA_TEMP.mkdir(exist_ok=True)
ARQUIVO_AUDIO_TEMP = PASTA_TEMP / 'audio.mp3'

# A API de transcrição da OpenAI aceita no máximo 25MB por requisição; usa 24MB como margem
LIMITE_API_AUDIO = 24 * 1024 * 1024

# Inicializa o cliente OpenAI com a chave API
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("❌ Chave API da OpenAI não encontrada! Verifique o arquivo .env")
    st.stop()

client = openai.OpenAI(api_key=api_key)

def _parse_json_safe(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except Exception:
        start = s.find('{')
        end = s.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start:end+1])
            except Exception:
                pass
        return {}

def gerar_conteudo_social(
    transcricao: str,
    plataforma: str = "Instagram",
    tom: str = "engajador",
    tamanho_legenda: str = "média",
    qtd_hashtags: int = 15,
) -> Dict[str, Any]:
    if not isinstance(transcricao, str):
        raise ValueError("transcricao inválida")
    texto = transcricao.strip()
    if not texto:
        raise ValueError("transcricao vazia")
    limite = 8000
    if len(texto) > limite:
        texto = texto[:limite]
    plataformas_validas: List[str] = [
        "Instagram",
        "TikTok",
        "YouTube Shorts",
        "LinkedIn",
        "Facebook",
        "X/Twitter",
        "Threads",
    ]
    if plataforma not in plataformas_validas:
        plataforma = "Instagram"
    if tamanho_legenda not in ["curta", "média", "media", "longa"]:
        tamanho_legenda = "média"
    if tamanho_legenda == "media":
        tamanho_legenda = "média"
    if not isinstance(qtd_hashtags, int) or qtd_hashtags < 3:
        qtd_hashtags = 10
    if qtd_hashtags > 30:
        qtd_hashtags = 30
    instrucao = (
        "Gere conteúdo para redes sociais em pt-BR com base na transcrição fornecida. "
        "Adapte ao contexto da plataforma, mantendo alto potencial de engajamento e clareza. "
        "Respeite o tamanho da legenda solicitado e a quantidade de hashtags. "
        "Retorne exclusivamente um objeto JSON com as chaves: "
        "titulo (string), legenda (string), hashtags (array de strings). "
        "Regras: "
        f"plataforma={plataforma}; tom={tom}; tamanho_legenda={tamanho_legenda}; qtd_hashtags={qtd_hashtags}. "
        "Use hashtags relevantes, em minúsculas e sem acentos, com prefixo '#', sem espaços. "
        "Evite clickbait enganoso; foque no benefício e na curiosidade legítima."
    )
    modelo = os.getenv("OPENAI_CONTENT_MODEL", "gpt-4o-mini")
    resp = client.chat.completions.create(
        model=modelo,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": instrucao},
            {"role": "user", "content": f"Transcrição:\n{texto}"},
        ],
        temperature=0.7,
        max_tokens=600,
    )
    conteudo = (
        resp.choices[0].message.content
        if getattr(resp, "choices", None)
        and getattr(resp.choices[0], "message", None)
        and resp.choices[0].message.content
        else ""
    )
    data = _parse_json_safe(conteudo)
    titulo = str(data.get("titulo", "")).strip()
    legenda = str(data.get("legenda", "")).strip()
    hashtags_raw = data.get("hashtags", [])
    hashtags_list: List[str] = []
    if isinstance(hashtags_raw, str):
        partes = [p.strip() for p in hashtags_raw.replace(",", " ").split()]
        hashtags_list = [p if p.startswith("#") else f"#{p}" for p in partes if p]
    elif isinstance(hashtags_raw, list):
        limpos: List[str] = []
        for h in hashtags_raw:
            if not isinstance(h, str):
                continue
            h2 = h.strip().replace(" ", "")
            if not h2:
                continue
            if not h2.startswith("#"):
                h2 = f"#{h2}"
            limpos.append(h2)
        hashtags_list = limpos
    vistos = set()
    unicos: List[str] = []
    for h in hashtags_list:
        k = h.lower()
        if k not in vistos:
            vistos.add(k)
            unicos.append(h)
    hashtags_final = unicos[:qtd_hashtags]
    if not titulo:
        titulo = "Título sugerido"
    if not legenda:
        legenda = "Legenda sugerida."
    return {"titulo": titulo, "legenda": legenda, "hashtags": hashtags_final}

def _conteudo_para_texto(conteudo: Dict[str, Any]) -> str:
    titulo = str(conteudo.get("titulo", "")).strip()
    legenda = str(conteudo.get("legenda", "")).strip()
    hashtags = conteudo.get("hashtags", [])
    if isinstance(hashtags, list):
        hashtags_str = " ".join([str(h) for h in hashtags if isinstance(h, str)])
    else:
        hashtags_str = str(hashtags)
    partes: List[str] = []
    if titulo:
        partes.append(f"Título: {titulo}")
    if legenda:
        partes.append("Legenda:")
        partes.append(legenda)
    if hashtags_str:
        partes.append("")
        partes.append("Hashtags:")
        partes.append(hashtags_str)
    return "\n".join(partes)

def render_copy_download(conteudo: Dict[str, Any], key_suffix: str, file_name: str) -> None:
    texto = _conteudo_para_texto(conteudo)
    escapado = html.escape(texto)
    text_id = f"copy_text_{key_suffix}"
    status_id = f"copy_status_{key_suffix}"
    btn_id = f"copy_btn_{key_suffix}"
    st.markdown(
        f'''
<div>
  <textarea id="{text_id}" style="position:absolute; left:-10000px; top:-10000px;">{escapado}</textarea>
  <button id="{btn_id}">Copiar</button>
  <span id="{status_id}" style="margin-left:8px;"></span>
</div>
<script>
(function() {{
  const btn = document.getElementById('{btn_id}');
  const txt = document.getElementById('{text_id}');
  const st = document.getElementById('{status_id}');
  if (btn && txt) {{
    btn.addEventListener('click', async () => {{
      try {{
        await navigator.clipboard.writeText(txt.value);
        if (st) st.textContent = 'Copiado!';
      }} catch (e) {{
        try {{
          txt.select(); document.execCommand('copy'); if (st) st.textContent = 'Copiado!';
        }} catch(_) {{ if (st) st.textContent = 'Falha ao copiar'; }}
      }}
    }});
  }}
}})();
</script>
''',
        unsafe_allow_html=True,
    )
    st.download_button(
        label="Download .txt",
        data=texto.encode("utf-8"),
        file_name=file_name,
        mime="text/plain",
    )

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

def duracao_midia_ffprobe(caminho):
    """Retorna a duração em segundos de um arquivo de mídia via ffprobe"""
    if not shutil.which('ffprobe'):
        return 0.0
    resultado = subprocess.run(
        [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            caminho,
        ],
        capture_output=True,
        text=True,
    )
    try:
        return float(resultado.stdout.strip())
    except Exception:
        return 0.0

def transcreve_arquivo_audio(caminho_audio, prompt):
    """Transcreve arquivo de áudio, dividindo em partes se exceder o limite da API"""
    tamanho = os.path.getsize(caminho_audio)
    if tamanho <= LIMITE_API_AUDIO:
        with open(caminho_audio, 'rb') as arquivo:
            return transcreve_audio(arquivo, prompt)

    duracao = duracao_midia_ffprobe(caminho_audio)
    if duracao <= 0:
        raise RuntimeError('Não foi possível determinar a duração do áudio')

    n_partes = math.ceil(tamanho / (LIMITE_API_AUDIO * 0.9))
    duracao_segmento = duracao / n_partes
    pasta = Path(caminho_audio).parent
    padrao = str(pasta / 'chunk_%04d.mp3')
    subprocess.run(
        [
            'ffmpeg', '-i', caminho_audio,
            '-f', 'segment',
            '-segment_time', str(duracao_segmento),
            '-acodec', 'copy',
            '-y', padrao,
        ],
        capture_output=True,
        check=True,
    )
    partes = sorted(pasta.glob('chunk_*.mp3'))
    textos = []
    for i, parte in enumerate(partes):
        contexto = prompt if i == 0 else textos[-1][-200:]
        with open(parte, 'rb') as arquivo:
            textos.append(transcreve_audio(arquivo, contexto))
        os.unlink(parte)
    return ' '.join(t.strip() for t in textos if t)

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
            '-ab', '48k',  # Bitrate reduzido (suficiente para fala)
            '-ac', '1',  # Mono
            '-ar', '16000',  # Sample rate (Whisper resamplea para 16kHz)
            '-y',  # Sobrescrever arquivo se existir
            caminho_audio
        ]
        
        # Executa o comando
        resultado = subprocess.run(
            comando, 
            capture_output=True, 
            text=True,
            timeout=1800  # Timeout de 30 minutos para arquivos grandes
        )
        
        if resultado.returncode == 0:
            return True, "Áudio extraído com sucesso"
        else:
            return False, f"Erro FFmpeg: {resultado.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Timeout: Vídeo muito longo para processar (limite: 30 minutos)"
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"

def transcreve_tab_video():
    """Aba para transcrição de vídeos"""
    st.info("📹 Faça upload de um arquivo de vídeo para extrair o áudio e transcrever automaticamente")
    
    prompt_input = st.text_input('(opcional) Digite um prompt para melhorar a transcrição', key='input_video')
    arquivo_video = st.file_uploader('Selecione um arquivo de vídeo', type=['mp4', 'mov', 'avi', 'mkv', 'webm'])
    
    if arquivo_video is not None:
        # Verifica tamanho do arquivo (limite de 25MB - Streamlit Cloud)
        tamanho_mb = len(arquivo_video.getvalue()) / (1024 * 1024)
        if tamanho_mb > 25:
            st.error(f"❌ Arquivo muito grande ({tamanho_mb:.1f}MB). Limite: 25MB")
            
            # Mostra soluções alternativas para arquivos > 25MB
            st.markdown("### 🛠️ Soluções para arquivos grandes (acima de 25MB):")
            
            st.markdown("""
            👉 **Opção 1: Comprimir o vídeo drasticamente ou usar apenas o áudio.**
            
            👉 **Opção 2: Extrair o áudio e fazer upload na aba 'Transcrever Áudio'.**
            
            👉 **Opção 3: Dividir o vídeo em clipes menores (cada um com menos de 25MB).**
            
            Devido a uma limitação da plataforma Streamlit Cloud, o tamanho máximo de upload é de 25MB.
            """)
            
            return
        
        # Aviso para arquivos grandes (entre 10MB e 25MB)
        if tamanho_mb > 10:
            st.warning(f"⚠️ Arquivo grande ({tamanho_mb:.1f}MB). O processamento pode demorar alguns minutos.")
        
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
                        transcricao = transcreve_arquivo_audio(temp_audio_path, prompt_input)
                        
                        st.success("✅ Transcrição concluída!")
                        st.write("### Resultado:")
                        st.write(transcricao)
                        with st.spinner('🧠 Gerando título, legenda e hashtags...'):
                            try:
                                conteudo = gerar_conteudo_social(str(transcricao))
                                st.write("### Conteúdo para redes sociais")
                                st.write(f"Título: {conteudo.get('titulo', '')}")
                                st.write("Legenda:")
                                st.write(conteudo.get('legenda', ''))
                                hashtags = conteudo.get('hashtags', [])
                                if isinstance(hashtags, list) and hashtags:
                                    st.write("Hashtags:")
                                    st.write(' '.join(hashtags))
                            except Exception as e:
                                st.warning(f"Não foi possível gerar conteúdo social: {str(e)}")
                        if 'conteudo' in locals():
                            fname = f"conteudo_{arquivo_video.name}.txt" if hasattr(arquivo_video, 'name') else "conteudo_video.txt"
                            render_copy_download(conteudo, "video_init", fname)
                        
                        st.write("#### Personalizar conteúdo")
                        colv1, colv2, colv3, colv4 = st.columns(4)
                        plataformas_v = ["Instagram", "TikTok", "YouTube Shorts", "LinkedIn", "Facebook", "X/Twitter", "Threads"]
                        with colv1:
                            plataforma_sel_v = st.selectbox("Plataforma", plataformas_v, index=0, key='plataforma_video')
                        with colv2:
                            tom_sel_v = st.selectbox("Tom", ["engajador", "informativo", "profissional", "humorístico", "persuasivo"], index=0, key='tom_video')
                        with colv3:
                            tamanho_sel_v = st.selectbox("Tamanho da legenda", ["curta", "média", "longa"], index=1, key='tamanho_legenda_video')
                        with colv4:
                            qtd_sel_v = st.slider("Qtd hashtags", 5, 30, 15, key='qtd_hashtags_video')
                        if st.button("Regenerar", key='regen_video'):
                            with st.spinner('🧠 Regenerando...'):
                                try:
                                    conteudo_v = gerar_conteudo_social(str(transcricao), plataforma_sel_v, tom_sel_v, tamanho_sel_v, int(qtd_sel_v))
                                    st.write("### Conteúdo para redes sociais (personalizado)")
                                    st.write(f"Título: {conteudo_v.get('titulo', '')}")
                                    st.write("Legenda:")
                                    st.write(conteudo_v.get('legenda', ''))
                                    hashtags_v = conteudo_v.get('hashtags', [])
                                    if isinstance(hashtags_v, list) and hashtags_v:
                                        st.write("Hashtags:")
                                        st.write(' '.join(hashtags_v))
                                except Exception as e:
                                    st.warning(f"Não foi possível regenerar conteúdo social: {str(e)}")
                            if 'conteudo_v' in locals():
                                fname_v = f"conteudo_{arquivo_video.name}_personalizado.txt" if hasattr(arquivo_video, 'name') else "conteudo_video_personalizado.txt"
                                render_copy_download(conteudo_v, "video_regen", fname_v)

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
        # Verifica tamanho do arquivo (limite de 25MB - Streamlit Cloud)
        tamanho_mb = len(arquivo_audio.getvalue()) / (1024 * 1024)
        if tamanho_mb > 25:
            st.error(f"❌ Arquivo muito grande ({tamanho_mb:.1f}MB). Limite: 25MB")
            st.info("💡 Comprima o áudio ou divida em partes menores. Arquivos MP3 geralmente são menores que vídeos.")
            return
        
        # Aviso para arquivos grandes (entre 10MB e 25MB)
        if tamanho_mb > 10:
            st.warning(f"⚠️ Arquivo grande ({tamanho_mb:.1f}MB). O processamento pode demorar alguns minutos.")
        
        with st.spinner('🎵 Transcrevendo áudio...'):
            try:
                transcricao = transcreve_audio(arquivo_audio, prompt_input)
                st.success("✅ Transcrição concluída!")
                st.write("### Resultado:")
                st.write(transcricao)
                with st.spinner('🧠 Gerando título, legenda e hashtags...'):
                    try:
                        conteudo = gerar_conteudo_social(str(transcricao))
                        st.write("### Conteúdo para redes sociais")
                        st.write(f"Título: {conteudo.get('titulo', '')}")
                        st.write("Legenda:")
                        st.write(conteudo.get('legenda', ''))
                        hashtags = conteudo.get('hashtags', [])
                        if isinstance(hashtags, list) and hashtags:
                            st.write("Hashtags:")
                            st.write(' '.join(hashtags))
                    except Exception as e:
                        st.warning(f"Não foi possível gerar conteúdo social: {str(e)}")
                if 'conteudo' in locals():
                    fname_a = f"conteudo_{arquivo_audio.name}.txt" if hasattr(arquivo_audio, 'name') else "conteudo_audio.txt"
                    render_copy_download(conteudo, "audio_init", fname_a)
                st.write("#### Personalizar conteúdo")
                col1, col2, col3, col4 = st.columns(4)
                plataformas = ["Instagram", "TikTok", "YouTube Shorts", "LinkedIn", "Facebook", "X/Twitter", "Threads"]
                with col1:
                    plataforma_sel = st.selectbox("Plataforma", plataformas, index=0, key='plataforma_audio')
                with col2:
                    tom_sel = st.selectbox("Tom", ["engajador", "informativo", "profissional", "humorístico", "persuasivo"], index=0, key='tom_audio')
                with col3:
                    tamanho_sel = st.selectbox("Tamanho da legenda", ["curta", "média", "longa"], index=1, key='tamanho_legenda_audio')
                with col4:
                    qtd_sel = st.slider("Qtd hashtags", 5, 30, 15, key='qtd_hashtags_audio')
                if st.button("Regenerar", key='regen_audio'):
                    with st.spinner('🧠 Regenerando...'):
                        try:
                            conteudo2 = gerar_conteudo_social(str(transcricao), plataforma_sel, tom_sel, tamanho_sel, int(qtd_sel))
                            st.write("### Conteúdo para redes sociais (personalizado)")
                            st.write(f"Título: {conteudo2.get('titulo', '')}")
                            st.write("Legenda:")
                            st.write(conteudo2.get('legenda', ''))
                            hashtags2 = conteudo2.get('hashtags', [])
                            if isinstance(hashtags2, list) and hashtags2:
                                st.write("Hashtags:")
                                st.write(' '.join(hashtags2))
                        except Exception as e:
                            st.warning(f"Não foi possível regenerar conteúdo social: {str(e)}")
                    if 'conteudo2' in locals():
                        fname_a2 = f"conteudo_{arquivo_audio.name}_personalizado.txt" if hasattr(arquivo_audio, 'name') else "conteudo_audio_personalizado.txt"
                        render_copy_download(conteudo2, "audio_regen", fname_a2)
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
