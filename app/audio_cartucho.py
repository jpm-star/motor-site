"""Áudio (WhatsApp) → cartucho JSON (motor-site, Bloco 1.1).

Transcreve o áudio via Whisper Groq e extrai os campos do cartucho com um LLM;
campo que o áudio não mencionou fica `null` e entra em `faltando[]`. NÃO inventa dado.
Reusa GROQ_API_KEY (env ou sdr-motor/.env). Só stdlib (urllib) — zero dependência nova.

Chamado: CLI `python -m app.audio_cartucho audio.ogg`. Retorna (audio_para_cartucho):
{"cartucho": {...}, "faltando": [campos null]}.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
# WAF do Groq bloqueia o UA default do urllib (Python-urllib → 403). UA de app resolve.
_UA = "noemi-motor-site/1.0"
_STT_MODEL = "whisper-large-v3-turbo"
_CHAT_MODEL = "llama-3.3-70b-versatile"

# campos do cartucho que a fala do dono costuma preencher (schema v1)
_CAMPOS = ["nome_empresa", "vertical", "escopo", "regioes_atendidas",
           "whatsapp_dono", "politica_preco", "politica_visita", "horario"]


def _chave() -> str:
    if k := os.environ.get("GROQ_API_KEY", "").strip():
        return k
    env = Path(os.environ.get("RR_ENV_PATH", "/root/sdr-motor/.env"))
    if env.is_file():
        for l in env.read_text().splitlines():
            if l.strip().startswith("GROQ_API_KEY="):
                return l.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("GROQ_API_KEY não encontrada (env nem sdr-motor/.env).")


def _multipart(campos: dict, arquivo: tuple[str, bytes]) -> tuple[bytes, str]:
    """Corpo multipart/form-data (stdlib, sem requests). arquivo=(nome, bytes)."""
    b = "----noemiAudioCartucho7f3a"
    linhas = []
    for k, v in campos.items():
        linhas += [f"--{b}", f'Content-Disposition: form-data; name="{k}"', "", str(v)]
    nome, dados = arquivo
    linhas += [f"--{b}",
               f'Content-Disposition: form-data; name="file"; filename="{nome}"',
               "Content-Type: application/octet-stream", ""]
    corpo = "\r\n".join(linhas).encode() + b"\r\n" + dados + f"\r\n--{b}--\r\n".encode()
    return corpo, f"multipart/form-data; boundary={b}"


def transcrever(audio: bytes, chave: str, nome: str = "audio.ogg") -> str:
    corpo, ctype = _multipart(
        {"model": _STT_MODEL, "response_format": "text", "language": "pt"}, (nome, audio))
    req = urllib.request.Request(_STT_URL, data=corpo, method="POST",
        headers={"Authorization": f"Bearer {chave}", "Content-Type": ctype, "User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8", "replace").strip()


_PROMPT = (
    "Você extrai o cartucho de um negócio a partir da fala do dono. Responda SOMENTE "
    "em JSON com estas chaves: " + ", ".join(_CAMPOS) + ". regioes_atendidas é lista. "
    "Use null (não invente) em qualquer campo que a fala NÃO mencionar claramente. "
    "vertical = o ramo (ex.: marmoraria, clinica, contabilidade). "
    "escopo = produtos/serviços que ele oferece (ex.: 'granito, quartzo, mármore')."
)


def extrair(transcricao: str, chave: str) -> dict:
    body = json.dumps({
        "model": _CHAT_MODEL, "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": _PROMPT},
                     {"role": "user", "content": transcricao[:8000]}],
    }).encode()
    req = urllib.request.Request(_CHAT_URL, data=body, method="POST",
        headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json", "User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read())
    bruto = json.loads(resp["choices"][0]["message"]["content"])
    # normaliza: só as chaves do schema, faltando o que veio null/vazio
    return {c: (bruto.get(c) if bruto.get(c) not in ("", [], {}) else None) for c in _CAMPOS}


def faltando(cartucho: dict) -> list[str]:
    """Campos que ficaram null/ausentes — o que ainda precisa perguntar ao dono."""
    return [c for c in _CAMPOS if cartucho.get(c) in (None, "", [], {})]


def audio_para_cartucho(caminho: Path, chave: str | None = None) -> dict:
    chave = chave or _chave()
    transcricao = transcrever(caminho.read_bytes(), chave, caminho.name)
    cart = extrair(transcricao, chave)
    return {"cartucho": cart, "faltando": faltando(cart), "transcricao": transcricao}


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print("uso: python -m app.audio_cartucho audio.ogg")
        return 2
    caminho = Path(argv[0])
    if not caminho.is_file():
        print(f"áudio não encontrado: {caminho}")
        return 2
    r = audio_para_cartucho(caminho)
    print(json.dumps({"cartucho": r["cartucho"], "faltando": r["faltando"]},
                     ensure_ascii=False, indent=2))
    if r["faltando"]:
        print(f"\n⚠️ faltam {len(r['faltando'])} campos: {', '.join(r['faltando'])}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
