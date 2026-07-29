"""Tier 2 SEO — composer do <head>. Junta meta tags + JSON-LD (schema.py) + GA4
(ga4.py) num bloco só pro gerador injetar. Entrada única: seo_head(negocio, ga4_id).

`negocio` dict: nome, nicho, cidade, uf, whatsapp, endereco, url,
servicos (list[str]), faq (list[{'q','a'}]). Funções puras, stdlib só.
"""
import html
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))  # roda como script E como módulo do pacote
import ga4  # noqa: E402
import schema  # noqa: E402


def _c(v) -> str:
    return v.strip() if isinstance(v, str) else ("" if v is None else str(v))


def meta_tags(negocio: dict) -> str:
    """<title>/description/Open Graph. Sempre retorna algo (title mínimo)."""
    n = negocio or {}
    nome = _c(n.get("nome")) or "Site"
    nicho, local = _c(n.get("nicho")), " ".join(p for p in [_c(n.get("cidade")), _c(n.get("uf"))] if p)
    title = " | ".join([nome] + [p for p in (nicho, local) if p])
    desc = ". ".join(dict.fromkeys(p for p in [f"{nicho} em {local}".strip() if nicho and local else nicho, nome] if p)) or nome
    e = html.escape
    linhas = [f"<title>{e(title)}</title>",
              f'<meta name="description" content="{e(desc)}">',
              f'<meta property="og:title" content="{e(title)}">',
              f'<meta property="og:description" content="{e(desc)}">',
              '<meta property="og:type" content="website">']
    if _c(n.get("url")):
        linhas.append(f'<meta property="og:url" content="{e(_c(n.get("url")))}">')
    return "\n".join(linhas)


def seo_head(negocio: dict, ga4_id: str = "") -> str:
    """Bloco completo pro <head>: meta + JSON-LD (schema.py, um @graph só) + GA4.
    Pula o que estiver vazio. Uma chamada resolve o Tier 2 do <head>."""
    return "\n".join(b for b in (meta_tags(negocio), schema.json_ld(negocio),
                                 ga4.gtag_snippet(ga4_id)) if b)


if __name__ == "__main__":  # self-check
    neg = {"nome": "Mármores Silva", "nicho": "Marmoraria", "cidade": "Campinas", "uf": "SP",
           "url": "https://marmoressilva.com.br", "whatsapp": "+5519999998888",
           "faq": [{"q": "Fazem entrega?", "a": "Sim, na região."}]}
    mt = meta_tags(neg)
    assert "<title>Mármores Silva | Marmoraria | Campinas SP</title>" in mt, mt
    assert "og:url" in mt
    assert "<title>Site</title>" in meta_tags({})  # mínimo sempre
    assert "&amp;" in meta_tags({"nome": "A & B"})  # escaping real
    h = seo_head(neg, "G-XYZ")
    # 1 só bloco JSON-LD (schema.py com @graph), GA4 presente, title presente
    assert h.count("application/ld+json") == 1, "não pode ter 2 JSON-LD (nós conflitantes)"
    assert "G-XYZ" in h and "<title>" in h and "@graph" in h
    assert "googletagmanager" not in seo_head(neg, "")  # sem GA = sem snippet
    print("head.py OK")
