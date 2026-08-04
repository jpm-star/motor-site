"""Orquestrador real (C1): Groq escreve a copy de conversão POR-CLIENTE.

Substitui a copy determinística do StubOrquestrador (headline templada + subheadline
fixa + corpo "{nome} entrega isso no dia a dia" repetido em toda seção) por copy
específica do negócio, escrita por LLM a partir do briefing. É o caminho ÚNICO de
produção (builder_web liga SITE_ORQUESTRADOR=llm); o stub fica só pra teste offline.

Reusa o encanamento Groq do repo (mesma GROQ_API_KEY / UA anti-WAF do audio_cartucho,
só stdlib). Falha-alto: sem chave ou Groq indisponível levanta — montar_site vira
BLOQUEADA na fila, nunca site com copy ruim no ar (contrato do pipeline). Uso:
SITE_ORQUESTRADOR=llm."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .base import AnguloAnalise, BriefingSite, OrquestradorProvider, prova_social_texto

_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
_UA = "noemi-motor-site/1.0"   # WAF do Groq bloqueia o UA default do urllib (→403)
_MODEL = "llama-3.3-70b-versatile"
_ANGULOS = ["diferenciacao", "publico_alvo", "prova_social"]

_SYS = (
    "Você é copywriter sênior de landing pages de conversão no Brasil. Escreve copy "
    "ESPECÍFICA do negócio — nunca frase genérica reaproveitável. PROIBIDO: clichê "
    "('referência em', 'qualidade e compromisso', 'entrega isso no dia a dia', "
    "'resultado que fala por si'), repetir a mesma frase/ideia em seções diferentes, e "
    "inventar fato que o briefing não deu. Responda SOMENTE em JSON com as chaves: "
    "headline (string curta, promessa concreta e específica), subheadline (string, 1 "
    "frase que amplia a headline), secoes (lista de 3 a 5 objetos {titulo, corpo}; cada "
    "corpo = 1-2 frases persuasivas e DISTINTAS entre si, ancoradas nos diferenciais/"
    "serviços reais do briefing), cta_texto (string curta, verbo de ação)."
)


def _chave() -> str:
    """GROQ_API_KEY do env, SITE_LLM_API_KEY, ou sdr-motor/.env. "" se ausente."""
    for var in ("GROQ_API_KEY", "SITE_LLM_API_KEY"):
        if k := os.environ.get(var, "").strip():
            return k
    env = Path(os.environ.get("RR_ENV_PATH", "/root/sdr-motor/.env"))
    if env.is_file():
        for l in env.read_text().splitlines():
            if l.strip().startswith("GROQ_API_KEY="):
                return l.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _groq_json(prompt_sys: str, prompt_user: str, chave: str, temperatura: float = 0.6) -> dict:
    """1 chamada chat JSON-mode. Levanta RuntimeError em falha de rede (falha-alto)."""
    body = json.dumps({
        "model": _MODEL, "temperature": temperatura,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": prompt_sys},
                     {"role": "user", "content": prompt_user[:6000]}],
    }).encode()
    req = urllib.request.Request(_CHAT_URL, data=body, method="POST", headers={
        "Authorization": f"Bearer {chave}", "Content-Type": "application/json", "User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())
    except (urllib.error.URLError, TimeoutError, OSError) as e:  # rede/timeout/HTTP
        raise RuntimeError(f"Groq indisponível ao gerar copy do site: {e}") from e
    return json.loads(resp["choices"][0]["message"]["content"])


def _txt(v: Any) -> str:
    return v.strip() if isinstance(v, str) else ""


def _limpar_secoes(secoes: Any, nome: str, nicho: str, difs: list[str]) -> list[dict[str, str]]:
    """Valida/sanitiza as seções do LLM + filtra corpo repetido (o defeito do stub).
    Sem seção válida → esqueleto dos diferenciais reais, nunca placeholder repetido."""
    out: list[dict[str, str]] = []
    vistos: set[str] = set()
    if isinstance(secoes, list):
        for s in secoes[:5]:
            if not isinstance(s, dict):
                continue
            t, c = _txt(s.get("titulo")), _txt(s.get("corpo"))
            if t and c and c.lower() not in vistos:   # anti-repetição de corpo
                out.append({"titulo": t, "corpo": c})
                vistos.add(c.lower())
    if not out:
        out = [{"titulo": d, "corpo": f"{d} é parte central do que a {nome} entrega em {nicho}."}
               for d in difs] or [{"titulo": f"Sobre a {nome}",
                                   "corpo": f"{nome} atua em {nicho} com atendimento próximo."}]
    return out


class LLMOrquestrador(OrquestradorProvider):
    name = "llm"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or _chave()

    def analisar(self, briefing: dict[str, Any]) -> list[AnguloAnalise]:
        # Ângulos = lentes fixas que guiam a síntese; o trabalho real (a copy) é 1 call
        # Groq em sintetizar — não gasta 2 chamadas por site. Sem LLM aqui = sem custo.
        nicho = briefing.get("nicho", "negócio")
        return [AnguloAnalise(angulo=a, insight=f"lente '{a}' sobre {nicho}") for a in _ANGULOS]

    def sintetizar(self, briefing: dict[str, Any], angulos: list[AnguloAnalise]) -> BriefingSite:
        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY/SITE_LLM_API_KEY ausente — orquestrador llm não configurado "
                "(exporte a chave ou use SITE_ORQUESTRADOR=stub).")
        nome = briefing.get("nome_empresa", "Sua Empresa")
        nicho = briefing.get("nicho", "negócio")
        difs = [d.strip() for d in briefing.get("diferenciais", []) if str(d).strip()]
        contexto = json.dumps({
            "nome": nome, "nicho": nicho, "diferenciais": difs,
            "publico": briefing.get("publico", "").strip(),
            "cidade": briefing.get("cidade", "").strip(),
            "servico_principal": briefing.get("servico_principal", "").strip(),
            "prova_social": prova_social_texto(briefing.get("prova_social")),  # list-safe
        }, ensure_ascii=False)
        dados = _groq_json(_SYS, f"Briefing do negócio:\n{contexto}", self.api_key)
        return BriefingSite(
            nome_empresa=nome,
            nicho=nicho,
            headline=_txt(dados.get("headline")) or nome,
            subheadline=_txt(dados.get("subheadline")),
            secoes=_limpar_secoes(dados.get("secoes"), nome, nicho, difs),
            cta_texto=_txt(dados.get("cta_texto")) or "Fale com a gente",
            cta_contato=briefing.get("whatsapp", "(a combinar)"),
            angulos_usados=angulos,
            cor_primaria=briefing.get("cor_primaria"),
            produtos=briefing.get("produtos") or [],
            cidade=briefing.get("cidade", "").strip(),
            servico_principal=briefing.get("servico_principal", "").strip(),
            ancora_preco=briefing.get("ancora_preco") or {},   # padrões do Radar (vazio = sem seção)
            antes_depois=briefing.get("prova_social") or [],
            logo_svg=briefing.get("logo_svg", ""),
            catalogo=briefing.get("catalogo") or [],
            # assets/copy do cliente (PROMPT 2) — passam direto pro gerador (vazio = fallback de hoje)
            hero_imagem=briefing.get("hero_imagem", ""),
            hero_video=briefing.get("hero_video", ""),
            copy_livre=briefing.get("copy_livre", ""),
            # estrutura variável: ordem das seções vem do briefing (vazio = default de sempre)
            receita_ordem=briefing.get("receita_ordem") or [],
            receita_hero=briefing.get("receita_hero", ""),
        )


if __name__ == "__main__":  # self-check offline: valida shape + anti-repetição, sem rede
    globals()["_groq_json"] = lambda *a, **k: {
        "headline": "Contabilidade sem susto pra sua PME",
        "subheadline": "Fecha o mês no prazo, sem multa e sem surpresa.",
        "secoes": [{"titulo": "Ágil", "corpo": "Resposta no mesmo dia útil."},
                   {"titulo": "Ágil", "corpo": "Resposta no mesmo dia útil."},   # dup → filtra
                   {"titulo": "Digital", "corpo": "Documento e guia direto no app."}],
        "cta_texto": "Falar com um contador"}
    o = LLMOrquestrador(api_key="x")
    b = o.sintetizar({"nome_empresa": "Silva", "nicho": "contabilidade",
                      "diferenciais": ["Ágil", "Digital"], "whatsapp": "551499"}, o.analisar({}))
    corpos = [s["corpo"] for s in b.secoes]
    assert len(corpos) == len(set(corpos)), "corpo repetido não foi filtrado"
    assert b.subheadline and "referência em" not in b.headline.lower()
    assert b.cta_contato == "551499" and len(o.analisar({})) == 3
    print("llm_orquestrador OK — copy específica, anti-repetição, 1 call/site, sem rede")
