import os
import math
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import html

import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from openai import OpenAI
import ffmpeg

# Configurações
app = FastAPI(title="Ai Infinitus Transcript")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PASTA_TEMP = Path("temp")
PASTA_TEMP.mkdir(exist_ok=True)

# A API de transcrição da OpenAI aceita no máximo 25MB por requisição; usa 24MB como margem
MAX_AUDIO_API_BYTES = 24 * 1024 * 1024

# Templates
templates = Jinja2Templates(directory="templates")

# Funções existentes (reutilizadas)
def _parse_json_safe(conteudo: str) -> Dict[str, Any]:
    try:
        return json.loads(conteudo)
    except json.JSONDecodeError:
        return {}

def gerar_conteudo_social(
    transcricao: str,
    plataforma: str = "Instagram",
    tom: str = "engajador",
    tamanho_legenda: str = "média",
    qtd_hashtags: int = 15,
    cta: str = "",
) -> Dict[str, Any]:
    if not isinstance(transcricao, str):
        raise ValueError("transcricao inválida")
    texto = transcricao.strip()
    if not texto:
        raise ValueError("transcricao vazia")
    limite = 8000
    if len(texto) > limite:
        texto = texto[:limite]
    plataformas_validas = [
        "Instagram", "TikTok", "YouTube Shorts", "LinkedIn", "Facebook", "X/Twitter", "Threads"
    ]
    if plataforma not in plataformas_validas:
        plataforma = "Instagram"
    if tamanho_legenda not in ["curta", "média", "longa"]:
        tamanho_legenda = "média"
    if not isinstance(qtd_hashtags, int) or qtd_hashtags < 3:
        qtd_hashtags = 10
    if qtd_hashtags > 30:
        qtd_hashtags = 30
    cta_texto = cta.strip()
    instrucao = (
        "Gere conteúdo para redes sociais em pt-BR com base na transcrição fornecida. "
        "Adapte ao contexto da plataforma, mantendo alto potencial de engajamento e clareza. "
        "Respeite o tamanho da legenda solicitado e a quantidade de hashtags. "
        "Retorne exclusivamente um objeto JSON com as chaves: "
        "titulo (string), legenda (string), hashtags (array de strings). "
        f"plataforma={plataforma}; tom={tom}; tamanho_legenda={tamanho_legenda}; qtd_hashtags={qtd_hashtags}. "
        "Use hashtags relevantes, em minúsculas e sem acentos, com prefixo '#', sem espaços. "
        "Evite clickbait enganoso; foque no benefício e na curiosidade legítima. "
        + (f"Inclua uma chamada para ação coerente com: '{cta_texto}'. " if cta_texto else "")
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

def transcreve_audio(arquivo, prompt: str = "") -> str:
    try:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=arquivo,
            language="pt",
            response_format="text",
            prompt=prompt,
        )
        return transcript
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na transcrição: {str(e)}")

def extrair_audio_com_ffmpeg(video_path: str, audio_path: str) -> tuple[bool, str]:
    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec="mp3", audio_bitrate="48k", ac=1, ar=16000)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return True, ""
    except ffmpeg.Error as e:
        return False, e.stderr.decode() if e.stderr else str(e)

def duracao_midia(caminho: str) -> float:
    try:
        probe = ffmpeg.probe(caminho)
        return float(probe.get("format", {}).get("duration", 0))
    except Exception:
        return 0.0

def dividir_audio_ffmpeg(caminho_audio: str, pasta: Path, duracao_segmento: float) -> List[Path]:
    padrao = str(pasta / "chunk_%04d.mp3")
    (
        ffmpeg
        .input(caminho_audio)
        .output(padrao, f="segment", segment_time=duracao_segmento, acodec="copy")
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )
    return sorted(pasta.glob("chunk_*.mp3"))

def transcreve_arquivo(caminho: Path, prompt: str = "") -> str:
    tamanho = caminho.stat().st_size
    if tamanho <= MAX_AUDIO_API_BYTES:
        with open(caminho, "rb") as f:
            return transcreve_audio(f, prompt)

    duracao = duracao_midia(str(caminho))
    if duracao <= 0:
        raise HTTPException(status_code=500, detail="Não foi possível determinar a duração do áudio.")

    n_partes = math.ceil(tamanho / (MAX_AUDIO_API_BYTES * 0.9))
    duracao_segmento = duracao / n_partes
    pasta_chunks = caminho.parent / "chunks"
    pasta_chunks.mkdir(exist_ok=True)
    try:
        partes = dividir_audio_ffmpeg(str(caminho), pasta_chunks, duracao_segmento)
    except ffmpeg.Error as e:
        raise HTTPException(status_code=500, detail=f"Erro ao dividir o áudio: {e.stderr.decode() if e.stderr else e}")

    transcricoes: List[str] = []
    for i, parte in enumerate(partes):
        contexto = prompt if i == 0 else transcricoes[-1][-200:]
        with open(parte, "rb") as f:
            transcricoes.append(transcreve_audio(f, contexto))
    return " ".join(t.strip() for t in transcricoes if t)

def baixar_arquivo_url(url: str, destino: Path) -> bool:
    try:
        import requests
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(destino, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Erro ao baixar {url}: {e}")
        return False

# Rotas
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/transcrever")
async def transcrever(
    arquivo: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    prompt: str = Form(""),
    plataforma: str = Form("Instagram"),
    tom: str = Form("engajador"),
    tamanho_legenda: str = Form("média"),
    qtd_hashtags: int = Form(15),
    cta: str = Form(""),
):
    if not arquivo and not url:
        raise HTTPException(status_code=400, detail="Envie um arquivo ou uma URL.")
    
    temp_dir = tempfile.mkdtemp(dir=PASTA_TEMP)
    try:
        # Determinar tipo e caminho do arquivo
        if arquivo:
            # Upload direto
            if arquivo.size and arquivo.size > 1024 * 1024 * 1024:  # 1GB
                raise HTTPException(status_code=413, detail="Arquivo maior que 1GB.")
            suffix = Path(arquivo.filename).suffix if arquivo.filename else ".tmp"
            arquivo_path = Path(temp_dir) / f"upload{suffix}"
            with open(arquivo_path, "wb") as f:
                shutil.copyfileobj(arquivo.file, f)
        else:
            # Download por URL
            if not url or not url.startswith(("http://", "https://")):
                raise HTTPException(status_code=400, detail="URL inválida.")
            # Tentar inferir sufixo pela URL
            suffix = ".mp4"  # padrão
            if any(ext in url.lower() for ext in [".mp3", ".wav", ".m4a", ".ogg"]):
                suffix = ".mp3"
            elif any(ext in url.lower() for ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]):
                suffix = ".mp4"
            arquivo_path = Path(temp_dir) / f"download{suffix}"
            if not baixar_arquivo_url(url, arquivo_path):
                raise HTTPException(status_code=400, detail="Falha ao baixar arquivo da URL.")
        
        # Verificar se é vídeo ou áudio
        ext = arquivo_path.suffix.lower()
        if ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
            # Vídeo: extrair áudio
            audio_path = Path(temp_dir) / "audio.mp3"
            sucesso, erro = extrair_audio_com_ffmpeg(str(arquivo_path), str(audio_path))
            if not sucesso:
                raise HTTPException(status_code=500, detail=f"Erro ao extrair áudio: {erro}")
            arquivo_transcrever = audio_path
        elif ext in [".mp3", ".wav", ".m4a", ".ogg"]:
            # Áudio direto: recomprime se exceder o limite da API
            if arquivo_path.stat().st_size > MAX_AUDIO_API_BYTES:
                audio_comprimido = Path(temp_dir) / "audio_comprimido.mp3"
                sucesso, erro = extrair_audio_com_ffmpeg(str(arquivo_path), str(audio_comprimido))
                if not sucesso:
                    raise HTTPException(status_code=500, detail=f"Erro ao comprimir áudio: {erro}")
                arquivo_transcrever = audio_comprimido
            else:
                arquivo_transcrever = arquivo_path
        else:
            raise HTTPException(status_code=400, detail="Formato não suportado.")
        
        # Transcrever (divide em partes se ainda exceder o limite da API)
        transcricao = transcreve_arquivo(arquivo_transcrever, prompt)
        
        # Gerar conteúdo social
        conteudo_social = gerar_conteudo_social(
            transcricao,
            plataforma,
            tom,
            tamanho_legenda,
            qtd_hashtags,
            cta,
        )
        
        return {
            "transcricao": transcricao,
            "conteudo_social": conteudo_social,
        }
    finally:
        # Limpar temp
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
