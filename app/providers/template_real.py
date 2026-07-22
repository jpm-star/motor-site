"""C3: gerador REAL — one-page vendável, estático, dirigido por TEMA (app/design.py).

Cada segmento renderiza com sua própria paleta/tipografia/assinatura/motion — não
um template fixo. Direção pré-pensada (imobiliária/clínica) quando existe; senão,
tema ancorado no assunto do negócio, sempre fora dos 4 clichês. Conteúdo do briefing
é escapado (html.escape). Sem placeholder: o que não é conteúdo real não vira seção.
"""
from __future__ import annotations

import html
from urllib.parse import quote

from .. import design
from .base import BriefingSite, GeradorSiteProvider, SiteGerado


def _e(texto: str) -> str:
    return html.escape(str(texto), quote=True)


def _so_digitos(contato: str) -> str:
    return "".join(c for c in str(contato) if c.isdigit())


def _titulo_pagina(nome: str, nicho: str) -> str:
    # não repetir o nicho quando o nome já o contém ("São Francisco Engenharia — Engenharia")
    if nicho and nicho.strip().lower() in nome.lower():
        return nome
    return f"{nome} — {nicho}" if nicho else nome


def _bloco_calculadora(acento: str) -> str:
    """Calculadora de financiamento inline (imobiliária). Simula a parcela (tabela
    Price) no próprio site — o lead brinca com os números e já chega quente no
    WhatsApp. Puro HTML+JS, sem backend."""
    return f"""
<section class="calc reveal" id="simular">
  <h2>Simule seu financiamento</h2>
  <p class="calc-sub">Uma ideia da parcela em segundos. Sem compromisso.</p>
  <div class="calc-grid">
    <label>Valor do imóvel<input id="c-valor" type="number" value="350000" min="0" step="1000"></label>
    <label>Entrada<input id="c-entrada" type="number" value="70000" min="0" step="1000"></label>
    <label>Juros (% ao ano)<input id="c-juros" type="number" value="10.5" min="0" step="0.1"></label>
    <label>Prazo (anos)<input id="c-prazo" type="number" value="30" min="1" max="35" step="1"></label>
  </div>
  <div class="calc-out"><span>Parcela estimada</span><strong id="c-parcela">—</strong></div>
  <p class="calc-nota">Estimativa (tabela Price, juros fixos). Valores reais dependem do banco e da análise de crédito.</p>
</section>
<script>
(function(){{
  var ids=["c-valor","c-entrada","c-juros","c-prazo"].map(function(i){{return document.getElementById(i)}});
  function fmt(v){{return v.toLocaleString("pt-BR",{{style:"currency",currency:"BRL",maximumFractionDigits:0}})}}
  function calc(){{
    var pv=(+ids[0].value)-(+ids[1].value), i=(+ids[2].value)/100/12, n=(+ids[3].value)*12;
    var out=document.getElementById("c-parcela");
    if(pv<=0||n<=0){{out.textContent="—";return}}
    var p = i>0 ? pv*i/(1-Math.pow(1+i,-n)) : pv/n;
    out.textContent=fmt(Math.round(p));
  }}
  ids.forEach(function(el){{el.addEventListener("input",calc)}}); calc();
}})();
</script>"""


class GeradorTemplate(GeradorSiteProvider):
    name = "template"

    def gerar(self, brief: BriefingSite, slug: str) -> SiteGerado:
        t = design.escolher_tema(brief.nicho, brief.nome_empresa)
        acento = brief.cor_primaria or t.acento  # marca do cliente vence o acento; resto do tema fica
        zap = _so_digitos(brief.cta_contato)
        # CTA WhatsApp contextual: mensagem pré-preenchida citando o negócio (a
        # conversa já chega qualificada, sem o cliente digitar do zero).
        _msg = quote(f"Olá! Vim pelo site da {brief.nome_empresa} e queria saber mais.")
        link = f"https://wa.me/{zap}?text={_msg}" if zap else "#contato"
        hero_fg = "#ffffff" if t.hero_escuro else t.ink
        hero_bg = (f"linear-gradient(155deg, {t.ink}, color-mix(in srgb, {t.ink} 78%, {acento}))"
                   if t.hero_escuro else t.bg)

        # calculadora só pra imobiliária (data/segmento-gated: fora disso não renderiza)
        calculadora = _bloco_calculadora(acento) if getattr(t, "id", "") == "imobiliaria" else ""
        numerado = t.assinatura == "index"
        cards = "\n".join(
            f'<article class="card reveal">'
            f'{f"<span class=num>{i:02d}</span>" if numerado else ""}'
            f'<h3>{_e(s["titulo"])}</h3><p>{_e(s["corpo"])}</p></article>'
            for i, s in enumerate(brief.secoes, 1)
        )
        kicker = _e(brief.nicho).upper() if brief.nicho else ""

        html_doc = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(_titulo_pagina(brief.nome_empresa, brief.nicho))}</title>
<meta name="description" content="{_e(brief.subheadline)}">
<meta property="og:title" content="{_e(brief.nome_empresa)}">
<meta property="og:description" content="{_e(brief.subheadline)}">
<meta property="og:type" content="website">
<link rel="icon" href="{design.favicon(brief.nome_empresa, acento)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={t.google}&display=swap">
<style>
:root {{ --acento: {acento}; --acento-suave: {t.acento_suave}; --ink: {t.ink};
  --bg: {t.bg}; --superficie: {t.superficie}; --linha: {t.linha}; --radius: {t.radius}; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: "{t.fonte_corpo}", system-ui, -apple-system, sans-serif;
  color: var(--ink); background: var(--bg); line-height: 1.65; -webkit-font-smoothing: antialiased; }}
h1, h2, h3, .kicker, .num {{ font-family: "{t.fonte_titulo}", system-ui, sans-serif; }}
.hero {{ background: {hero_bg}; color: {hero_fg}; padding: 6rem 1.5rem 4.5rem; text-align: center; }}
.kicker {{ display:inline-block; font-size:.72rem; font-weight:700; letter-spacing:.22em;
  padding:.4rem .9rem; border-radius:99px; margin-bottom:1.4rem;
  color: {acento if not t.hero_escuro else '#fff'};
  background: {('color-mix(in srgb,'+acento+' 16%,transparent)') if not t.hero_escuro else 'rgba(255,255,255,.14)'};
  border:1px solid {('color-mix(in srgb,'+acento+' 30%,transparent)') if not t.hero_escuro else 'rgba(255,255,255,.22)'}; }}
.hero h1 {{ font-size: clamp(2rem, 5.5vw, 3.5rem); font-weight: {t.peso_titulo}; max-width: 52rem;
  margin: 0 auto .9rem; letter-spacing: {t.tracking}; line-height: 1.08; }}
.hero p {{ font-size: clamp(1.05rem, 2.4vw, 1.3rem); opacity: .9; max-width: 40rem; margin: 0 auto 2.2rem; }}
.btn {{ display:inline-block; background: var(--acento); color:#fff; font-weight:700;
  padding:.95rem 2.3rem; border-radius:99px; text-decoration:none; font-family:"{t.fonte_titulo}",sans-serif;
  box-shadow: 0 6px 18px -4px color-mix(in srgb, var(--acento) 60%, transparent); }}
.hero .btn {{ background: {('#fff' if t.hero_escuro else 'var(--acento)')};
  color: {(acento if t.hero_escuro else '#fff')}; }}
main {{ max-width: 66rem; margin: 0 auto; padding: 4rem 1.5rem 1rem; }}
.grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.3rem; }}
.card {{ background: var(--superficie); border:1px solid var(--linha); border-radius: var(--radius);
  padding: 1.7rem 1.6rem; }}
.card .num {{ display:block; font-size:1.6rem; font-weight:800; color: color-mix(in srgb,var(--acento) 55%,var(--linha)); margin-bottom:.5rem; letter-spacing:{t.tracking}; }}
.card h3 {{ color: var(--ink); margin-bottom:.5rem; font-size:1.12rem; font-weight:{t.peso_titulo}; letter-spacing:{t.tracking}; }}
.card p {{ color: color-mix(in srgb, var(--ink) 78%, var(--bg)); font-size:.97rem; }}
.faixa {{ max-width:66rem; margin: 2.5rem auto 0; padding: 2rem 1.5rem; text-align:center;
  background: var(--acento-suave); border-radius: var(--radius); }}
.faixa strong {{ font-family:"{t.fonte_titulo}",sans-serif; color: var(--ink); font-size: clamp(1.2rem,3vw,1.6rem); letter-spacing:{t.tracking}; }}
.cta-final {{ text-align:center; padding: 4rem 1.5rem 5rem; }}
.cta-final h2 {{ font-size: clamp(1.5rem, 4vw, 2.1rem); margin-bottom:1.6rem; letter-spacing:{t.tracking}; }}
footer {{ text-align:center; padding:1.6rem; color: color-mix(in srgb,var(--ink) 55%,var(--bg));
  font-size:.85rem; border-top:1px solid var(--linha); }}
.zap-fixo {{ position:fixed; right:1.25rem; bottom:1.25rem; width:3.6rem; height:3.6rem; border-radius:50%;
  background:#25d366; display:flex; align-items:center; justify-content:center;
  box-shadow:0 6px 18px rgb(0 0 0 / .3); z-index:10; }}
.zap-fixo svg {{ width:2rem; height:2rem; fill:#fff; }}
.calc {{ max-width:66rem; margin:3rem auto 0; padding:2.5rem 1.5rem; background:var(--superficie);
  border:1px solid var(--linha); border-radius:var(--radius); text-align:center; }}
.calc h2 {{ font-size:clamp(1.4rem,3.5vw,2rem); letter-spacing:{t.tracking}; }}
.calc-sub {{ color: color-mix(in srgb,var(--ink) 66%,var(--bg)); margin:.4rem 0 1.6rem; }}
.calc-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:1rem; text-align:left; }}
.calc-grid label {{ display:flex; flex-direction:column; gap:.35rem; font-size:.82rem; font-weight:600;
  color: color-mix(in srgb,var(--ink) 78%,var(--bg)); }}
.calc-grid input {{ padding:.7rem .8rem; border:1px solid var(--linha); border-radius:calc(var(--radius)*.6);
  font-size:1rem; background:var(--bg); color:var(--ink); font-family:inherit; }}
.calc-grid input:focus {{ outline:0; border-color:var(--acento); }}
.calc-out {{ margin:1.8rem 0 .4rem; display:flex; flex-direction:column; gap:.2rem; }}
.calc-out span {{ font-size:.85rem; color: color-mix(in srgb,var(--ink) 66%,var(--bg)); }}
.calc-out strong {{ font-family:"{t.fonte_titulo}",sans-serif; font-size:clamp(2rem,6vw,2.8rem);
  color:var(--acento); letter-spacing:{t.tracking}; }}
.calc-nota {{ font-size:.75rem; color: color-mix(in srgb,var(--ink) 55%,var(--bg)); max-width:34rem; margin:.6rem auto 0; }}
{design.css_motion()}
</style>
</head>
<body>
<header class="hero">
  {f'<span class="kicker">{kicker}</span>' if kicker else ''}
  <h1>{_e(brief.headline)}</h1>
  <p>{_e(brief.subheadline)}</p>
  <a class="btn" href="{link}">{_e(brief.cta_texto)}</a>
</header>
<main>
  <div class="grid">
{cards}
  </div>
</main>
{calculadora}
<div class="faixa reveal"><strong>{_e(brief.nome_empresa)} · {_e(brief.subheadline)}</strong></div>
<section class="cta-final reveal" id="contato">
  <h2>Pronto pra começar?</h2>
  <a class="btn" href="{link}">{_e(brief.cta_texto)}</a>
</section>
<footer>© {_e(brief.nome_empresa)}{f' · {_e(brief.nicho)}' if brief.nicho else ''}</footer>
<a class="zap-fixo" href="{link}" aria-label="WhatsApp">
  <svg viewBox="0 0 32 32"><path d="M16 3C9.4 3 4 8.4 4 15c0 2.6.8 5 2.3 7L4 29l7.2-2.2c1.9 1 4 1.6 6.2 1.6h.6c6.6 0 12-5.4 12-12S22.6 3 16 3zm5.9 17c-.3.8-1.6 1.5-2.3 1.6-.6.1-1.3.2-3.8-.8-3.2-1.3-5.2-4.5-5.4-4.7-.2-.2-1.3-1.7-1.3-3.2s.8-2.3 1.1-2.6c.3-.3.6-.4.8-.4h.6c.2 0 .5-.1.7.5l1 2.4c.1.2.1.4 0 .6l-.4.6-.6.7c-.2.2-.4.4-.2.8.2.4 1 1.6 2.1 2.6 1.5 1.3 2.7 1.7 3.1 1.9.4.2.6.2.8-.1l1-1.2c.2-.3.5-.2.8-.1l2.2 1c.3.2.5.3.6.4.1.3.1.9-.2 1.6z"/></svg>
</a>
{design.js_reveal()}
</body>
</html>
"""
        return SiteGerado(arquivos={"index.html": html_doc}, slug=slug)
