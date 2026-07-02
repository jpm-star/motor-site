"""C3: gerador REAL — one-page vendável (~R$800), estático, zero dependência.

Um arquivo HTML com CSS embutido: hero, diferenciais em cards, seção de conteúdo,
CTA de WhatsApp fixo, SEO/OG meta, responsivo, cor de marca configurável pelo
briefing (`cor_primaria`). Conteúdo do usuário é escapado (html.escape) — o LLM
ou o JP podem escrever qualquer coisa no briefing sem quebrar/injetar HTML."""
from __future__ import annotations

import html

from .base import BriefingSite, GeradorSiteProvider, SiteGerado

_COR_DEFAULT = "#0f766e"  # teal sóbrio — neutro pra qualquer nicho


def _e(texto: str) -> str:
    return html.escape(str(texto), quote=True)


def _so_digitos(contato: str) -> str:
    return "".join(c for c in str(contato) if c.isdigit())


class GeradorTemplate(GeradorSiteProvider):
    name = "template"

    def gerar(self, brief: BriefingSite, slug: str) -> SiteGerado:
        cor = brief.cor_primaria or _COR_DEFAULT
        zap = _so_digitos(brief.cta_contato)
        link_zap = f"https://wa.me/{zap}" if zap else "#contato"
        cards = "\n".join(
            f'<article class="card"><h3>{_e(s["titulo"])}</h3><p>{_e(s["corpo"])}</p></article>'
            for s in brief.secoes
        )
        html_doc = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(brief.nome_empresa)} — {_e(brief.nicho)}</title>
<meta name="description" content="{_e(brief.subheadline)}">
<meta property="og:title" content="{_e(brief.nome_empresa)}">
<meta property="og:description" content="{_e(brief.headline)}">
<meta property="og:type" content="website">
<style>
:root {{ --cor: {cor}; --ink: #1c1917; --bg: #fafaf9; --muted: #57534e; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       color: var(--ink); background: var(--bg); line-height: 1.6; }}
.hero {{ background: linear-gradient(160deg, var(--cor), color-mix(in srgb, var(--cor) 60%, #000));
        color: #fff; padding: 5rem 1.5rem 4rem; text-align: center; }}
.hero h1 {{ font-size: clamp(1.8rem, 5vw, 3rem); font-weight: 800; max-width: 52rem;
           margin: 0 auto .75rem; letter-spacing: -.02em; }}
.hero p {{ font-size: clamp(1rem, 2.5vw, 1.25rem); opacity: .92; max-width: 40rem; margin: 0 auto 2rem; }}
.btn {{ display: inline-block; background: #fff; color: var(--cor); font-weight: 700;
       padding: .9rem 2.2rem; border-radius: 999px; text-decoration: none;
       box-shadow: 0 4px 14px rgb(0 0 0 / .25); transition: transform .15s; }}
.btn:hover {{ transform: translateY(-2px); }}
main {{ max-width: 64rem; margin: 0 auto; padding: 3.5rem 1.5rem; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.25rem; }}
.card {{ background: #fff; border: 1px solid #e7e5e4; border-radius: 1rem; padding: 1.5rem;
        box-shadow: 0 1px 3px rgb(0 0 0 / .06); }}
.card h3 {{ color: var(--cor); margin-bottom: .5rem; font-size: 1.05rem; }}
.card p {{ color: var(--muted); font-size: .95rem; }}
.cta-final {{ text-align: center; padding: 3.5rem 1.5rem 4.5rem; }}
.cta-final h2 {{ font-size: clamp(1.4rem, 4vw, 2rem); margin-bottom: 1.5rem; }}
.cta-final .btn {{ background: var(--cor); color: #fff; }}
footer {{ text-align: center; padding: 1.5rem; color: var(--muted); font-size: .85rem;
         border-top: 1px solid #e7e5e4; }}
.zap-fixo {{ position: fixed; right: 1.25rem; bottom: 1.25rem; width: 3.5rem; height: 3.5rem;
            border-radius: 50%; background: #25d366; display: flex; align-items: center;
            justify-content: center; box-shadow: 0 4px 14px rgb(0 0 0 / .3); z-index: 10; }}
.zap-fixo svg {{ width: 1.9rem; height: 1.9rem; fill: #fff; }}
</style>
</head>
<body>
<header class="hero">
  <h1>{_e(brief.headline)}</h1>
  <p>{_e(brief.subheadline)}</p>
  <a class="btn" href="{link_zap}">{_e(brief.cta_texto)}</a>
</header>
<main>
  <div class="grid">
{cards}
  </div>
</main>
<section class="cta-final" id="contato">
  <h2>Pronto pra começar?</h2>
  <a class="btn" href="{link_zap}">{_e(brief.cta_texto)}</a>
</section>
<footer>© {_e(brief.nome_empresa)} · {_e(brief.nicho)}</footer>
<a class="zap-fixo" href="{link_zap}" aria-label="WhatsApp">
  <svg viewBox="0 0 32 32"><path d="M16 3C9.4 3 4 8.4 4 15c0 2.6.8 5 2.3 7L4 29l7.2-2.2c1.9 1 4 1.6 6.2 1.6h.6c6.6 0 12-5.4 12-12S22.6 3 16 3zm5.9 17c-.3.8-1.6 1.5-2.3 1.6-.6.1-1.3.2-3.8-.8-3.2-1.3-5.2-4.5-5.4-4.7-.2-.2-1.3-1.7-1.3-3.2s.8-2.3 1.1-2.6c.3-.3.6-.4.8-.4h.6c.2 0 .5-.1.7.5l1 2.4c.1.2.1.4 0 .6l-.4.6-.6.7c-.2.2-.4.4-.2.8.2.4 1 1.6 2.1 2.6 1.5 1.3 2.7 1.7 3.1 1.9.4.2.6.2.8-.1l1-1.2c.2-.3.5-.2.8-.1l2.2 1c.3.2.5.3.6.4.1.3.1.9-.2 1.6z"/></svg>
</a>
</body>
</html>
"""
        return SiteGerado(arquivos={"index.html": html_doc}, slug=slug)
