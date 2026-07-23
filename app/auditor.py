"""Auditor de site de prospect → score + tier + diagnóstico (motor-site, prospecção).

Dado a URL de um prospect, checa sinais OBJETIVOS (HTTPS, mobile, WhatsApp, formulário,
SEO, schema.org, sitemap/robots, FAQ/AEO), pontua 0-100 e sugere o tier do plano.
Gera um diagnóstico específico (achados reais) pra abordagem comercial. Sem site → Tier 1.

Chamado: CLI `python -m app.auditor prospects.csv [--out out/auditoria.md]`.
Retorna (auditar): dict com sinais/score/tier/diagnostico. Puro stdlib (urllib),
determinístico, R$0 — NÃO usa LLM. Performance real (Core Web Vitals) fica de fora:
exige Lighthouse; aqui só há um proxy de tempo/tamanho, marcado como não-oficial.
"""
from __future__ import annotations

import csv
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

_UA = "Mozilla/5.0 (compatible; NoemiAuditor/1.0)"
_TIMEOUT = 12

# peso de cada sinal no score (soma 100). Conversão pesa mais — é o que vende.
_PESOS = {
    "whatsapp": 15, "formulario": 15,           # Conversão (30)
    "title": 8, "description": 8, "jsonld": 8, "h1": 6,  # SEO (30)
    "viewport": 20,                              # Mobile (20)
    "sitemap": 5, "robots": 5, "aeo": 10,        # Descoberta/AEO (20)
}
# score → tier (edite à vontade). Sem site é tratado à parte (Tier 1).
_TIERS = [(40, 2), (70, 3), (101, 4)]  # <40→2, <70→3, senão→4


def _baixar(url: str) -> tuple[str, dict]:
    """(html, info) da URL. Levanta urllib.error/timeout se não carregar."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
        corpo = r.read(1_500_000)  # teto: não engole página gigante
        html = corpo.decode(r.headers.get_content_charset() or "utf-8", "replace")
        info = {"status": r.status, "url_final": r.geturl(),
                "ms": round((time.monotonic() - t0) * 1000),
                "kb": round(len(corpo) / 1024)}
    return html, info


def _existe(url_base: str, caminho: str) -> bool:
    """True se url_base/caminho responde 200 (sitemap/robots). Best-effort."""
    try:
        req = urllib.request.Request(urljoin(url_base, caminho),
                                     headers={"User-Agent": _UA}, method="HEAD")
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            return r.status == 200
    except Exception:
        return False


def _sinais(html: str, info: dict, url: str) -> dict:
    """Cada sinal objetivo do site → bool. Regex simples (não precisa de parser)."""
    h = html.lower()
    base = f"{urlparse(info['url_final']).scheme}://{urlparse(info['url_final']).netloc}"
    return {
        "https": info["url_final"].startswith("https"),
        "viewport": 'name="viewport"' in h or "name='viewport'" in h,
        "whatsapp": bool(re.search(r"wa\.me|api\.whatsapp|whatsapp", h)),
        "formulario": "<form" in h,
        "title": bool(re.search(r"<title>\s*\S", h)),
        "description": 'name="description"' in h,
        "jsonld": "application/ld+json" in h,
        "h1": "<h1" in h,
        "aeo": "faqpage" in h or "<details" in h or "perguntas frequentes" in h,
        "sitemap": _existe(base, "/sitemap.xml"),
        "robots": _existe(base, "/robots.txt"),
    }


def _score(sinais: dict) -> tuple[int, dict]:
    """Score 0-100 + subtotais por categoria, a partir dos sinais e dos pesos."""
    pontos = {k: (_PESOS[k] if sinais.get(k) else 0) for k in _PESOS}
    total = sum(pontos.values())
    cat = {
        "Conversão": pontos["whatsapp"] + pontos["formulario"],
        "SEO": pontos["title"] + pontos["description"] + pontos["jsonld"] + pontos["h1"],
        "Mobile": pontos["viewport"],
        "Descoberta/AEO": pontos["sitemap"] + pontos["robots"] + pontos["aeo"],
    }
    return total, cat


def _tier(tem_site: bool, score: int) -> int:
    if not tem_site:
        return 1
    return next(t for limite, t in _TIERS if score < limite)


_ROTULO_FALTA = {
    "https": "não usa HTTPS (cadeado)", "viewport": "não é adaptado pra celular",
    "whatsapp": "não tem botão de WhatsApp", "formulario": "não tem formulário de contato",
    "title": "sem título de página (SEO)", "description": "sem descrição pro Google",
    "jsonld": "sem dados estruturados (schema.org)", "h1": "sem título principal (H1)",
    "aeo": "sem FAQ estruturada pra respostas de IA", "sitemap": "sem sitemap.xml",
    "robots": "sem robots.txt",
}


def _diagnostico(nome: str, tem_site: bool, score: int, sinais: dict, info: dict, tier: int) -> str:
    """Diagnóstico específico (achados reais) pra abordagem comercial."""
    if not tem_site:
        return (f"{nome} não tem site ativo. Hoje quem busca no Google não te acha — "
                f"o concorrente com uma página simples leva o cliente. Recomendação: Plano {tier} "
                f"(colocar um site que converte no ar).")
    faltas = [_ROTULO_FALTA[k] for k in _ROTULO_FALTA if not sinais.get(k)]
    corpo = f"O site de {nome} pontuou {score}/100. "
    if info.get("ms"):
        corpo += f"Carrega em ~{info['ms'] / 1000:.1f}s. "
    if faltas:
        corpo += "Pontos que travam contato e busca: " + "; ".join(faltas[:5]) + ". "
    corpo += (f"Corrigindo isso, você melhora a experiência e abre mais oportunidades de contato. "
              f"Recomendação: Plano {tier}.")
    return corpo


def auditar(url: str, nome: str = "") -> dict:
    """Audita 1 site. URL vazia/inacessível → sem site (Tier 1). Nunca levanta."""
    nome = nome or (urlparse(url).netloc or url or "prospect")
    if not url or not urlparse(url).netloc:
        return _resultado(nome, url, False, {}, {}, 0)
    if not url.startswith("http"):
        url = "https://" + url
    try:
        html, info = _baixar(url)
    except Exception as e:
        # não carregou → trata como sem site utilizável (oportunidade)
        return {**_resultado(nome, url, False, {}, {"erro": str(e)[:100]}, 0)}
    sinais = _sinais(html, info, url)
    score, cat = _score(sinais)
    return _resultado(nome, url, True, sinais, info, score, cat)


def _resultado(nome, url, tem_site, sinais, info, score, cat=None) -> dict:
    tier = _tier(tem_site, score)
    return {"nome": nome, "url": url, "tem_site": tem_site, "score": score,
            "categorias": cat or {}, "sinais": sinais, "info": info, "tier": tier,
            "diagnostico": _diagnostico(nome, tem_site, score, sinais, info, tier)}


# -- CLI --------------------------------------------------------------------
def _prospects(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _relatorio_md(resultados: list[dict]) -> str:
    # ranqueia por OPORTUNIDADE: sem site primeiro, depois menor score (mais a ganhar)
    resultados.sort(key=lambda r: (r["tem_site"], r["score"]))
    linhas = [f"# Auditoria de prospects ({len(resultados)})", "",
              "| Prospect | Site | Score | Tier | Diagnóstico |", "|---|---|---|---|---|"]
    for r in resultados:
        site = "❌ sem site" if not r["tem_site"] else f"{r['score']}/100"
        linhas.append(f"| **{r['nome']}** | {site} | {r['score']} | **{r['tier']}** | {r['diagnostico']} |")
    return "\n".join(linhas) + "\n"


def rodar(caminho: Path, out: Path) -> list[dict]:
    resultados = []
    prospects = _prospects(caminho)
    for i, row in enumerate(prospects, 1):
        nome = (row.get("nome") or row.get("nome_empresa") or "").strip()
        url = (row.get("url") or row.get("site") or "").strip()
        try:
            r = auditar(url, nome)
        except Exception as e:  # um prospect quebrado não derruba o lote
            r = {"nome": nome or f"linha {i}", "url": url, "tem_site": False, "score": 0,
                 "tier": 1, "diagnostico": f"(erro na auditoria: {str(e)[:80]})", "sinais": {}, "info": {}, "categorias": {}}
        resultados.append(r)
        print(f"[{i}/{len(prospects)}] {r['nome']}: score {r['score']} → Tier {r['tier']}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_relatorio_md(resultados), encoding="utf-8")
    return resultados


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print("uso: python -m app.auditor prospects.csv [--out out/auditoria.md]")
        print("  CSV: colunas nome[,url]  (sem url = trata como sem site → Tier 1)")
        return 2
    caminho = Path(argv[0])
    if not caminho.is_file():
        print(f"arquivo não encontrado: {caminho}")
        return 2
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else Path("out/auditoria.md")
    res = rodar(caminho, out)
    tiers = {}
    for r in res:
        tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    print(f"\n=== {len(res)} prospects auditados → {out} ===")
    print("por tier: " + " | ".join(f"Tier {t}: {n}" for t, n in sorted(tiers.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
