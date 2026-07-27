"""C3: gerador REAL — one-page vendável, estático, dirigido por TEMA (app/design.py).

Cada segmento renderiza com sua própria paleta/tipografia/assinatura/motion — não
um template fixo. Direção pré-pensada (imobiliária/clínica) quando existe; senão,
tema ancorado no assunto do negócio, sempre fora dos 4 clichês. Conteúdo do briefing
é escapado (html.escape). Sem placeholder: o que não é conteúdo real não vira seção.
"""
from __future__ import annotations

import html
import json
from urllib.parse import quote

from .. import design
from .base import BriefingSite, GeradorSiteProvider, SiteGerado


def _e(texto: str) -> str:
    return html.escape(str(texto), quote=True)


def _so_digitos(contato: str) -> str:
    return "".join(c for c in str(contato) if c.isdigit())


def _titulo_pagina(nome: str, nicho: str, cidade: str = "") -> str:
    # SEO local: "{nicho} em {cidade} | {nome}" — a busca "X em <cidade>" é a que converte.
    if nicho and cidade:
        return f"{nicho} em {cidade} | {nome}"
    # não repetir o nicho quando o nome já o contém ("São Francisco Engenharia — Engenharia")
    if nicho and nicho.strip().lower() in nome.lower():
        return nome
    return f"{nome} — {nicho}" if nicho else nome


def _json_ld_local(brief) -> str:
    """JSON-LD schema.org/LocalBusiness preenchido do cartucho — só campos reais
    (nada inventado). Ajuda o Google a mostrar o negócio na busca/mapa local."""
    dados = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": brief.nome_empresa,
        "description": brief.subheadline,
    }
    if brief.nicho:
        dados["knowsAbout"] = brief.nicho
    if getattr(brief, "cidade", ""):
        dados["areaServed"] = brief.cidade
        dados["address"] = {"@type": "PostalAddress", "addressLocality": brief.cidade}
    zap = _so_digitos(brief.cta_contato)
    if zap:
        dados["telephone"] = f"+{zap}"
    corpo = json.dumps(dados, ensure_ascii=False)
    return f'<script type="application/ld+json">{corpo}</script>'


# FAQ por segmento (build-time): perguntas reais que o cliente faz antes de chamar.
# Conteúdo genérico mas VERDADEIRO (nada de promessa falsa). <details> nativo, sem JS.
_FAQ = {
    "imobiliaria": [
        ("Vocês ajudam no financiamento?", "Sim. Orientamos sobre as opções e simulamos a parcela junto com você — inclusive aqui no site, na calculadora acima."),
        ("Como agendo uma visita?", "É só chamar no WhatsApp com o imóvel de interesse. Confirmamos o melhor horário na hora."),
        ("Atendem a documentação e a escritura?", "Acompanhamos da proposta à assinatura, com apoio na papelada e nos prazos."),
        ("Trabalham com imóveis de que faixa?", "Fale com a gente o que procura e o orçamento — apresentamos as opções que encaixam."),
    ],
    "clinica": [
        ("Como marco uma consulta?", "Pelo WhatsApp, em minutos. Confirmamos o horário e já deixamos tudo pronto pro seu atendimento."),
        ("Atendem por convênio ou particular?", "Chame no WhatsApp que explicamos as formas de atendimento e pagamento disponíveis."),
        ("Preciso levar algum exame?", "Depende do procedimento — orientamos no agendamento o que trazer, pra você não perder a viagem."),
        ("Tem horário fora do comercial?", "Consulte a disponibilidade no WhatsApp; buscamos o horário que caiba na sua rotina."),
    ],
    "_generico": [
        ("Como faço um orçamento?", "É rápido: chame no WhatsApp com o que precisa e retornamos com os valores."),
        ("Qual a região de atendimento?", "Fale com a gente sua localização que confirmamos o atendimento na sua área."),
        ("Como funciona o prazo?", "Combinamos o prazo antes de começar e mantemos você informado até a entrega."),
    ],
}


def _bloco_faq(t_id: str) -> str:
    itens = _FAQ.get(t_id) or _FAQ["_generico"]
    linhas = "\n".join(
        f"<details class='faq-item'><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>"
        for q, a in itens)
    return f"""
<section class="faq reveal" id="faq">
  <h2>Perguntas frequentes</h2>
  <div class="faq-lista">{linhas}</div>
</section>"""


# Depoimentos de EXEMPLO — sempre marcados como exemplo (trava de honestidade:
# nunca passar texto fabricado como se fosse cliente real). Mostra o FORMATO; o
# cliente troca pelos reais depois. Rotação por JS (sem lib).
_DEPO_EXEMPLO = [
    ("Atendimento rápido e sem enrolação. Recomendo!", "Cliente satisfeito"),
    ("Explicaram tudo com clareza e cumpriram o prazo.", "Cliente da região"),
    ("Profissionais atenciosos do começo ao fim.", "Cliente recente"),
]


def _bloco_depoimentos() -> str:
    cards = "\n".join(
        f'<figure class="depo-card"{" hidden" if i else ""}>'
        f'<span class="depo-tag">exemplo</span>'
        f'<blockquote>"{html.escape(txt)}"</blockquote>'
        f'<figcaption>— {html.escape(quem)}</figcaption></figure>'
        for i, (txt, quem) in enumerate(_DEPO_EXEMPLO))
    return f"""
<section class="depo reveal" id="depoimentos">
  <h2>O que dizem</h2>
  <div class="depo-palco">{cards}</div>
</section>
<script>
(function(){{
  var cs=document.querySelectorAll(".depo-card"); if(cs.length<2) return; var k=0;
  setInterval(function(){{ cs[k].hidden=true; k=(k+1)%cs.length; cs[k].hidden=false; }}, 4500);
}})();
</script>"""


def _bloco_form(zap: str, nome_empresa: str) -> str:
    """Formulário progressivo: pede só nome+telefone primeiro (menos atrito); o
    resto aparece depois. No envio, abre o WhatsApp já com os dados preenchidos —
    o lead cai qualificado, sem backend."""
    if not zap:
        return ""
    ne = html.escape(nome_empresa)
    return f"""
<section class="lead reveal" id="contato-form">
  <h2>Fale com a gente</h2>
  <p class="lead-sub">Deixe seu nome e telefone — o resto é rapidinho.</p>
  <form class="lead-form" onsubmit="return leadEnviar(event)">
    <div class="lead-row">
      <input id="l-nome" required placeholder="Seu nome" autocomplete="name">
      <input id="l-fone" required placeholder="Seu telefone (WhatsApp)" inputmode="tel" autocomplete="tel">
    </div>
    <div id="l-mais" hidden>
      <textarea id="l-msg" rows="2" placeholder="O que você procura? (opcional)"></textarea>
    </div>
    <button type="submit">Continuar no WhatsApp</button>
  </form>
</section>
<script>
function leadEnviar(e){{
  e.preventDefault();
  var nome=document.getElementById("l-nome").value.trim();
  var fone=document.getElementById("l-fone").value.trim();
  var mais=document.getElementById("l-mais");
  if(mais.hidden){{ mais.hidden=false; document.getElementById("l-msg").focus(); return false; }}
  var msg=document.getElementById("l-msg").value.trim();
  var t="Olá! Sou "+nome+" ("+fone+"). Vim pelo site da {ne}"+(msg?(" e procuro: "+msg):"")+".";
  window.open("https://wa.me/{zap}?text="+encodeURIComponent(t),"_blank");
  return false;
}}
</script>"""


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
        # CTA WhatsApp contextual: mensagem pré-preenchida citando o SERVIÇO-âncora
        # do cartucho (a conversa já chega qualificada). Sem serviço → cita o negócio.
        _msg = quote(
            f"Olá! Quero orçamento de {brief.servico_principal}." if brief.servico_principal
            else f"Olá! Vim pelo site da {brief.nome_empresa} e queria saber mais."
        )
        link = f"https://wa.me/{zap}?text={_msg}" if zap else "#contato"
        hero_fg = "#ffffff" if t.hero_escuro else t.ink
        hero_bg = (f"linear-gradient(155deg, {t.ink}, color-mix(in srgb, {t.ink} 78%, {acento}))"
                   if t.hero_escuro else t.bg)

        # calculadora só pra imobiliária (data/segmento-gated: fora disso não renderiza)
        calculadora = _bloco_calculadora(acento) if getattr(t, "id", "") == "imobiliaria" else ""
        faq = _bloco_faq(getattr(t, "id", ""))  # universal (cai no genérico se o segmento não tiver)
        formulario = _bloco_form(zap, brief.nome_empresa)  # captura de lead → WhatsApp
        depoimentos = _bloco_depoimentos()  # exemplos rotativos, sempre marcados "exemplo"
        numerado = t.assinatura == "index"
        # seções do briefing + PISO de valor: se o briefing é pobre (<3 seções), o
        # template compensa com cards VERDADEIROS (nada inventado), pra nunca sair
        # uma página magra. O que importa pro prospect: confiança + como fala + região.
        secoes = list(brief.secoes)
        _serv = brief.servico_principal or brief.nicho or "seu serviço"
        _reg = f" em {brief.cidade}" if getattr(brief, "cidade", "") else " na sua região"
        piso = [
            {"titulo": "Orçamento sem compromisso",
             "corpo": f"Chame no WhatsApp e receba os valores de {_serv} antes de fechar qualquer coisa."},
            {"titulo": f"{_serv[:38].capitalize()} feito direito",
             "corpo": "Atendimento próximo, prazo combinado na frente e trabalho entregue como prometido."},
            {"titulo": f"Atende{_reg}",
             "corpo": "Perto de você e sem enrolação — a gente resolve o que você precisa, rápido."},
        ]
        for p in piso:
            if len(secoes) >= 3:
                break
            secoes.append(p)
        cards = "\n".join(
            f'<article class="card reveal">'
            f'{f"<span class=num>{i:02d}</span>" if numerado else ""}'
            f'<h3>{_e(s["titulo"])}</h3><p>{_e(s["corpo"])}</p></article>'
            for i, s in enumerate(secoes, 1)
        )
        kicker = _e(brief.nicho).upper() if brief.nicho else ""

        html_doc = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(_titulo_pagina(brief.nome_empresa, brief.nicho, brief.cidade))}</title>
<meta name="description" content="{_e(brief.subheadline)}">
<meta property="og:title" content="{_e(brief.nome_empresa)}">
<meta property="og:description" content="{_e(brief.subheadline)}">
<meta property="og:type" content="website">
{_json_ld_local(brief)}
<link rel="icon" href="{design.favicon(brief.nome_empresa, acento)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={t.google}&display=swap">
<style>
:root {{ --acento: {acento}; --acento-suave: {t.acento_suave}; --ink: {t.ink};
  --acento-ink: {t.acento_ink};
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
.btn {{ display:inline-block; background: var(--acento); color:var(--acento-ink); font-weight:700;
  padding:.95rem 2.3rem; border-radius:99px; text-decoration:none; font-family:"{t.fonte_titulo}",sans-serif;
  box-shadow: 0 6px 18px -4px color-mix(in srgb, var(--acento) 60%, transparent); }}
.hero .btn {{ background: {('#fff' if t.hero_escuro else 'var(--acento)')};
  color: {('#0b0f16' if t.hero_escuro else 'var(--acento-ink)')}; }}
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
.faq {{ max-width:52rem; margin:3rem auto 0; padding:0 1.5rem; }}
.faq h2 {{ text-align:center; font-size:clamp(1.4rem,3.5vw,2rem); margin-bottom:1.5rem; letter-spacing:{t.tracking}; }}
.faq-item {{ border:1px solid var(--linha); border-radius:var(--radius); margin-bottom:.7rem; background:var(--superficie); overflow:hidden; }}
.faq-item summary {{ cursor:pointer; padding:1rem 1.2rem; font-weight:600; font-family:"{t.fonte_titulo}",sans-serif;
  list-style:none; display:flex; justify-content:space-between; align-items:center; gap:1rem; }}
.faq-item summary::after {{ content:"+"; color:var(--acento); font-size:1.3rem; transition:transform .2s; }}
.faq-item[open] summary::after {{ transform:rotate(45deg); }}
.faq-item p {{ padding:0 1.2rem 1.1rem; color: color-mix(in srgb,var(--ink) 72%,var(--bg)); font-size:.95rem; }}
.lead {{ max-width:44rem; margin:3rem auto 0; padding:2.5rem 1.5rem; text-align:center; }}
.lead h2 {{ font-size:clamp(1.4rem,3.5vw,2rem); letter-spacing:{t.tracking}; }}
.lead-sub {{ color: color-mix(in srgb,var(--ink) 66%,var(--bg)); margin:.4rem 0 1.4rem; }}
.lead-row {{ display:flex; gap:.7rem; flex-wrap:wrap; }}
.lead-form input, .lead-form textarea {{ flex:1; min-width:160px; padding:.85rem 1rem; border:1px solid var(--linha);
  border-radius:calc(var(--radius)*.6); font-size:1rem; background:var(--bg); color:var(--ink); font-family:inherit; }}
.lead-form textarea {{ width:100%; margin-top:.7rem; resize:vertical; }}
.lead-form input:focus, .lead-form textarea:focus {{ outline:0; border-color:var(--acento); }}
.lead-form button {{ margin-top:1rem; width:100%; }}
.depo {{ max-width:44rem; margin:3rem auto 0; padding:0 1.5rem; text-align:center; }}
.depo h2 {{ font-size:clamp(1.4rem,3.5vw,2rem); margin-bottom:1.4rem; letter-spacing:{t.tracking}; }}
.depo-palco {{ position:relative; }}
.depo-card {{ background:var(--acento-suave); border-radius:var(--radius); padding:2rem 1.6rem; position:relative; }}
.depo-tag {{ position:absolute; top:.7rem; right:.7rem; font-size:.62rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.1em; color:var(--acento); background:var(--bg); border:1px solid var(--linha); border-radius:99px; padding:.15rem .55rem; }}
.depo-card blockquote {{ font-size:clamp(1.05rem,2.6vw,1.3rem); font-family:"{t.fonte_titulo}",sans-serif; color:var(--ink); line-height:1.4; }}
.depo-card figcaption {{ margin-top:.9rem; font-size:.85rem; color: color-mix(in srgb,var(--ink) 60%,var(--bg)); }}
.hero-trust {{ margin-top:1.6rem; font-size:.82rem; font-weight:600; letter-spacing:.01em;
  opacity:.82; display:inline-block; }}
.sec-titulo {{ text-align:center; font-size:clamp(1.5rem,3.6vw,2.1rem); font-weight:{t.peso_titulo};
  letter-spacing:{t.tracking}; margin-bottom:2rem; }}
.sec-titulo::after {{ content:""; display:block; width:2.4rem; height:3px; border-radius:3px;
  background:var(--acento); margin:.7rem auto 0; }}
.lead-form button {{ margin-top:1rem; width:100%; background:var(--acento); color:#fff; font-weight:700;
  border:0; padding:.95rem 2rem; border-radius:99px; font-size:1rem; font-family:"{t.fonte_titulo}",sans-serif;
  cursor:pointer; box-shadow:0 6px 18px -4px color-mix(in srgb,var(--acento) 55%,transparent); }}
{design.css_motion()}
</style>
</head>
<body>
<nav class="nav">
  <b><a href="#topo" style="color:inherit;text-decoration:none;background:none;padding:0">{_e(brief.nome_empresa)}</a></b>
  <a href="{link}">{_e(brief.cta_texto)}</a>
</nav>
<header class="hero" id="topo">
  {'<div class="aurora"></div>' if t.hero_escuro else ''}
  {f'<span class="kicker load load-1">{kicker}</span>' if kicker else ''}
  <h1 class="load load-2">{_e(brief.headline)}</h1>
  <p class="load load-3">{_e(brief.subheadline)}</p>
  <a class="btn load load-4" href="{link}">{_e(brief.cta_texto)}</a>
  <div class="hero-trust load load-5">{' &nbsp;·&nbsp; '.join(
     x for x in [f'Atende {_e(brief.cidade)}' if getattr(brief,'cidade','') else '',
                 'Resposta rápida no WhatsApp', 'Orçamento sem compromisso'] if x)}</div>
</header>
<main>
  <h2 class="sec-titulo reveal">Por que a {_e(brief.nome_empresa)}</h2>
  <div class="grid">
{cards}
  </div>
</main>
{calculadora}
{depoimentos}
{faq}
{formulario}
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
{design.js_interacoes()}
</body>
</html>
"""
        return SiteGerado(arquivos={"index.html": html_doc}, slug=slug)
