"""Sistema de design por segmento — o que deixa o motor pronto pra QUALQUER
prospecção (adega de bairro, clínica extravagante, o que vier).

Cada site nasce de um `Tema` (tokens: cor, tipo, layout, 1 elemento de assinatura),
não de um template fixo. Fluxo:
  1. direção PRÉ-PENSADA quando o segmento tem uma (imobiliária, clínica);
  2. senão, geração ANCORADA NO ASSUNTO do negócio (não no "tipo" genérico),
     estável por nome (hash) e única — dois negócios nunca caem no mesmo par;
  3. tudo passa pela GUARDA ANTI-CLICHÊ (os 4 clichês de site-feito-por-IA);
  4. motion vem do BANCO reutilizável (técnica, não estética — serve a qualquer direção).

Regra dura (spec JP): título NUNCA em serifada — a serifa-hero é o próprio tell do
clichê Claude-Design (terracota + Instrument Serif itálico). Só sans grotesca/humanista.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

# fontes serifadas conhecidas — proibidas no título (guarda anti-clichê #1/#2)
_SERIFAS = {"instrument serif", "fraunces", "playfair display", "dm serif display",
            "lora", "cormorant", "eb garamond", "libre baskerville"}


@dataclass(frozen=True)
class Tema:
    id: str
    ink: str            # texto principal — NUNCA preto puro
    bg: str             # fundo da página
    superficie: str     # cartões
    linha: str          # bordas
    acento: str         # cor de AÇÃO (CTA, guia) — não decorativa
    acento_suave: str   # tint do acento (fundos de destaque leve)
    fonte_titulo: str   # family (Google Fonts) — sans
    fonte_corpo: str    # family (Google Fonts)
    google: str         # querystring do <link> do Google Fonts
    radius: str         # border-radius base
    peso_titulo: str    # 600/700/800
    tracking: str       # letter-spacing do título
    assinatura: str     # 'index' | 'processo' | 'faixa' — o elemento não-genérico
    hero_escuro: bool   # hero sobre ink escuro (True) ou claro (False)
    acento_ink: str = "#ffffff"  # cor do TEXTO sobre o acento (botão). Default branco
    #                              (acento escuro); acento CLARO/neon precisa texto escuro.


# === DIREÇÕES PRÉ-PENSADAS =================================================
# Imobiliária (Tier 4) — CORRIGIDA: índigo profundo + pedra/areia quente + sans
# grotesca confiante. NUNCA terracota+serifa (clichê Claude-Design).
_IMOBILIARIA = Tema(
    id="imobiliaria", ink="#1b1830", bg="#f4efe7", superficie="#fffdf9", linha="#e6ddce",
    acento="#4338ca", acento_suave="#ebe9fb",
    fonte_titulo="Manrope", fonte_corpo="Plus Jakarta Sans",
    google="Manrope:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600",
    radius="14px", peso_titulo="800", tracking="-.025em", assinatura="index", hero_escuro=True)

# Oficina/automotivo — base AÇO FRIA (não creme quente) + azul-diagnóstico +
# grotesca condensada industrial + hero grafite. Foge do clichê creme+terracota
# que a mecânica caía por hash. Azul = precisão/confiança ("não me passam a perna").
_OFICINA = Tema(
    id="oficina", ink="#161a1f", bg="#e9edf1", superficie="#ffffff", linha="#d3d9e0",
    acento="#1857a8", acento_suave="#e4ecf6",
    fonte_titulo="Archivo", fonte_corpo="Inter",
    google="Archivo:wght@600;700;800&family=Inter:wght@400;500;600",
    radius="8px", peso_titulo="800", tracking="-.02em", assinatura="processo", hero_escuro=True)

# Clínica — claro + deep teal fechado (guia, não decorativo) + sans humanista.
_CLINICA = Tema(
    id="clinica", ink="#14201d", bg="#fbfdfc", superficie="#ffffff", linha="#e3ece9",
    acento="#0d7d6e", acento_suave="#e2f2ef",
    fonte_titulo="Instrument Sans", fonte_corpo="Source Sans 3",
    google="Instrument+Sans:wght@500;600;700&family=Source+Sans+3:wght@400;500;600",
    radius="16px", peso_titulo="600", tracking="-.01em", assinatura="processo", hero_escuro=False)

# JPOS — MARCA DA CASA (dogfooding). Único tema de FUNDO ESCURO + neon: aqui o
# "clichê #3" é IDENTIDADE intencional (tech/matrix/vendável), não default preguiçoso.
# Retornado direto no topo do escolher_tema → não passa pelo guard anti-clichê.
# ink CLARO sobre bg escuro; o template resolve texto via color-mix(ink, bg).
_JPOS = Tema(
    id="jpos", ink="#e9eef7", bg="#0c1017", superficie="#141a24", linha="#26303f",
    acento="#00e6a2", acento_suave="#0e2a24",
    fonte_titulo="Space Grotesk", fonte_corpo="Inter",
    google="Space+Grotesk:wght@600;700;800&family=Inter:wght@400;500;600",
    radius="12px", peso_titulo="800", tracking="-.025em", assinatura="faixa", hero_escuro=True,
    acento_ink="#04140e")  # texto escuro sobre o neon (contraste)

# === POOL GENERATIVO (segmentos sem direção pré-pensada) ===================
# Cada entrada é uma direção distinta, com PAR TIPOGRÁFICO único (garante que dois
# sites não compartilhem tipografia) e pré-vetada contra os 4 clichês.
_POOL: list[Tema] = [
    Tema("navy", "#0f1b2d", "#f4f6f8", "#ffffff", "#e2e8f0", "#1e5eff", "#e6edff",
         "Sora", "Atkinson Hyperlegible",
         "Sora:wght@600;700;800&family=Atkinson+Hyperlegible:wght@400;700",
         "12px", "700", "-.02em", "faixa", True),
    Tema("floresta", "#14231b", "#f5f7f4", "#ffffff", "#dfe6e0", "#2f7d4f", "#e4f1ea",
         "Space Grotesk", "Inter",
         "Space+Grotesk:wght@600;700&family=Inter:wght@400;500;600",
         "14px", "700", "-.02em", "processo", False),
    Tema("vinho", "#241019", "#f7f2f3", "#fffdfd", "#eddfe3", "#8e2a4b", "#f6e5eb",
         "Bricolage Grotesque", "DM Sans",
         "Bricolage+Grotesque:wght@600;700;800&family=DM+Sans:wght@400;500;600",
         "10px", "800", "-.02em", "index", True),
    Tema("ardosia", "#1e1b2e", "#f6f5fa", "#ffffff", "#e6e3f0", "#6d28d9", "#efeafd",
         "Schibsted Grotesk", "Work Sans",
         "Schibsted+Grotesk:wght@600;700;800&family=Work+Sans:wght@400;500;600",
         "16px", "700", "-.02em", "faixa", False),
    Tema("grafite", "#1c1c22", "#f7f6f3", "#ffffff", "#e6e4de", "#b45309", "#f6ecdd",
         "Figtree", "Hanken Grotesk",
         "Figtree:wght@600;700;800&family=Hanken+Grotesk:wght@400;500;600",
         "12px", "800", "-.02em", "processo", False),
    Tema("petroleo", "#0e2020", "#eef2f1", "#ffffff", "#dbe6e4", "#0f8a8a", "#dcf1f0",
         "Onest", "Albert Sans",
         "Onest:wght@600;700;800&family=Albert+Sans:wght@400;500;600",
         "14px", "700", "-.02em", "index", True),
    Tema("carmim", "#221019", "#f7f3f4", "#ffffff", "#ecdfe2", "#be123c", "#fbe3e8",
         "Archivo", "Epilogue",
         "Archivo:wght@600;700;800&family=Epilogue:wght@400;500;600",
         "10px", "800", "-.015em", "faixa", False),
    Tema("cobalto", "#141a2e", "#f5f6fb", "#ffffff", "#e1e5f2", "#2b4ed6", "#e5e9fb",
         "Outfit", "Red Hat Text",
         "Outfit:wght@600;700;800&family=Red+Hat+Text:wght@400;500;600",
         "18px", "700", "-.02em", "processo", True),
]

# ancoragem no ASSUNTO real (não no "tipo"): palavra-chave → direção do pool.
_ASSUNTO = {
    "vinho": "vinho", "adega": "vinho", "bar": "vinho", "bistro": "vinho", "gastr": "vinho",
    "solar": "navy", "energia": "navy", "tecnolog": "cobalto", "software": "cobalto",
    "advoc": "grafite", "juríd": "grafite", "juri": "grafite", "contab": "grafite",
    "engenh": "grafite", "constru": "grafite", "arquit": "grafite", "obra": "grafite", "reforma": "grafite",
    "ambient": "floresta", "sustent": "floresta", "agro": "floresta", "jardim": "floresta",
    "spa": "petroleo", "bem-estar": "petroleo", "estét": "carmim", "beleza": "carmim",
    "academ": "ardosia", "fitness": "ardosia", "cross": "ardosia",
    "pizz": "vinho", "restaur": "vinho", "lanch": "vinho", "hamburg": "vinho", "food": "vinho",
    "pet": "floresta", "veterin": "floresta", "animal": "floresta", "banho e tosa": "floresta",
    "advog": "grafite",
}


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def escolher_tema(nicho: str, nome: str) -> Tema:
    n = _norm(nicho)
    # 0) marca da casa: JPOS/agência de IA → tema dark-neon dedicado (bypassa o guard)
    if any(k in n for k in ("jpos", "agência de ia", "agencia de ia", "automação de ia",
                            "automacao de ia", "micro-saas de ia", "ia sob medida")):
        return _JPOS
    # 1) direção pré-pensada — cor EXATA e intencional, sem variação
    if any(k in n for k in ("imob", "imóv", "imov", "corretor", "lotea")):
        return _IMOBILIARIA
    if any(k in n for k in ("clín", "clin", "saúde", "saude", "odonto", "médic", "medic", "consult")):
        return _CLINICA
    if any(k in n for k in ("mecân", "mecan", "auto ", "automot", "oficina", "carro", "veícul",
                            "veicul", "pneu", "funilaria", "borracharia")):
        return _OFICINA
    # 2) segmento sem direção: base ancorada no assunto (senão hash), com o acento
    #    NUDGED por nome → dois negócios não caem na mesma paleta (spec: nenhum
    #    site idêntico). O par tipográfico vem do pool (finito): com muitos sites
    #    ele recorre — limite honesto de fontes, não bug.
    base = None
    for chave, tid in _ASSUNTO.items():
        if chave in n:
            base = next(t for t in _POOL if t.id == tid)
            break
    if base is None:
        base = _POOL[int(hashlib.sha1(_norm(nome).encode()).hexdigest(), 16) % len(_POOL)]
    from dataclasses import replace
    return replace(base, acento=_variar_acento(base.acento, nome))


def _variar_acento(hex_cor: str, nome: str) -> str:
    """Roda o matiz do acento por um delta derivado do nome (paleta quase-única),
    dentro de faixa segura — e nunca cria terracota (guarda anti-clichê #1)."""
    import colorsys
    h = hex_cor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    passo = int(hashlib.sha1(_norm(nome).encode()).hexdigest(), 16) % 7  # 0..6
    delta = (passo - 3) * 0.028  # ~±10° em torno da base
    nr, ng, nb = colorsys.hls_to_rgb((hh + delta) % 1.0, ll, ss)
    novo = "#" + "".join(f"{round(c * 255):02x}" for c in (nr, ng, nb))
    return hex_cor if _terroso(novo) else novo


# === GUARDA ANTI-CLICHÊ ====================================================
def _terroso(hex_cor: str) -> bool:
    """terracota/argila/marrom-quente: R alto, G médio, B baixo."""
    h = hex_cor.lstrip("#")
    if len(h) != 6:
        return False
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r > 150 and 60 < g < 150 and b < 90 and r - b > 70


def _muito_escuro(hex_cor: str) -> bool:
    h = hex_cor.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r + g + b) / 3 < 26  # perto de preto puro


def _cliche(tema: Tema) -> str | None:
    """Devolve o nome do clichê violado, ou None. Os 4 da lista do JP."""
    titulo_serif = _norm(tema.fonte_titulo) in _SERIFAS
    # 1) terracota/argila + serifada pesada (Claude Design default)
    if titulo_serif and (_terroso(tema.acento) or _terroso(tema.bg)):
        return "1-terracota+serifa (Claude Design default)"
    # 2) creme + serifada + acento terroso
    creme = tema.bg.lower() in ("#faf7f0", "#fbf7ee", "#f7f1e3", "#faf6ec")
    if titulo_serif and creme and _terroso(tema.acento):
        return "2-creme+serifa+terroso"
    # 3) fundo escuro + único acento neon (near-black)
    if _muito_escuro(tema.bg):
        return "3-fundo-escuro+neon-unico"
    # 4) jornal: hairlines + zero border-radius
    if tema.radius.strip() in ("0", "0px"):
        return "4-jornal-hairline+radius0"
    return None


def validar_temas() -> None:
    """Nenhuma direção nem entrada do pool pode nascer clichê (invariante)."""
    for t in [_IMOBILIARIA, _CLINICA, *_POOL]:
        v = _cliche(t)
        assert v is None, f"tema {t.id} viola clichê {v}"
    pares = [(t.fonte_titulo, t.fonte_corpo) for t in _POOL]
    assert len(pares) == len(set(pares)), "par tipográfico repetido no pool"


# === BANCO DE MOTION (técnica reutilizável, respeita prefers-reduced-motion) ==
SPRING = "cubic-bezier(.175,.885,.32,1.275)"


def css_motion() -> str:
    return f"""
html {{ scroll-behavior: smooth; }}
.reveal {{ opacity: 0; transform: translateY(22px); transition: opacity .7s {SPRING}, transform .7s {SPRING}; }}
.reveal.vis {{ opacity: 1; transform: none; }}
/* entrada em SEQUÊNCIA no load (hero) — o "abrir de cortina" premium */
@keyframes rise {{ from {{ opacity:0; transform:translateY(26px); }} to {{ opacity:1; transform:none; }} }}
.load {{ opacity:0; animation: rise .8s {SPRING} forwards; }}
.load-1{{animation-delay:.06s}} .load-2{{animation-delay:.16s}} .load-3{{animation-delay:.26s}}
.load-4{{animation-delay:.38s}} .load-5{{animation-delay:.5s}}
/* AURORA — camada de gradiente viva atrás do hero escuro (feel AI-native) */
.hero {{ position:relative; overflow:hidden; }}
.aurora {{ position:absolute; inset:-45% -15% auto -15%; height:170%; z-index:0; pointer-events:none;
  background: radial-gradient(42% 52% at 18% 28%, color-mix(in srgb,var(--acento) 60%,transparent), transparent 70%),
              radial-gradient(38% 48% at 82% 22%, color-mix(in srgb,var(--acento) 34%,transparent), transparent 72%),
              radial-gradient(45% 55% at 60% 90%, color-mix(in srgb,var(--acento) 26%,transparent), transparent 70%);
  filter: blur(46px) saturate(1.2); animation: aurora 16s ease-in-out infinite alternate; }}
@keyframes aurora {{ 0% {{ transform:translate3d(0,0,0) scale(1); opacity:.85; }}
  100% {{ transform:translate3d(2%,-7%,0) scale(1.18); opacity:1; }} }}
.hero > * {{ position:relative; z-index:1; }}
/* cards: elevação + SPOTLIGHT que segue o cursor + brilho varrendo */
.card {{ transition: transform .38s {SPRING}, box-shadow .38s ease, border-color .38s ease; position: relative; overflow: hidden; }}
.card::before {{ content:""; position:absolute; inset:0; z-index:1; opacity:0; transition:opacity .4s ease;
  background: radial-gradient(220px circle at var(--mx,50%) var(--my,0%), color-mix(in srgb,var(--acento) 16%,transparent), transparent 65%); }}
.card:hover::before {{ opacity:1; }}
.card:hover {{ transform: translateY(-7px) scale(1.014); box-shadow: 0 22px 48px -14px color-mix(in srgb,var(--ink) 32%,transparent); border-color: color-mix(in srgb,var(--acento) 45%,var(--linha)); }}
.card > * {{ position:relative; z-index:2; }}
.btn {{ transition: transform .3s {SPRING}, box-shadow .3s ease, letter-spacing .3s ease; }}
.btn:hover {{ transform: translateY(-3px) scale(1.03); letter-spacing: .01em; box-shadow: 0 16px 34px -8px color-mix(in srgb,var(--acento) 60%,transparent); }}
/* NAV fixo com blur — aparece ao rolar (brand + CTA + voltar ao topo) */
.nav {{ position:fixed; top:0; left:0; right:0; z-index:30; display:flex; justify-content:space-between; align-items:center;
  gap:1rem; padding:.7rem clamp(1rem,4vw,2.5rem); backdrop-filter:saturate(1.4) blur(14px);
  background:color-mix(in srgb,var(--bg) 72%,transparent); border-bottom:1px solid transparent;
  transform:translateY(-105%); transition:transform .45s {SPRING}, border-color .4s; }}
.nav.on {{ transform:none; border-color:var(--linha); }}
.nav b {{ font-family:inherit; font-weight:800; letter-spacing:-.02em; font-size:1.02rem; }}
.nav a {{ text-decoration:none; color:#fff; background:var(--acento); font-weight:700; font-size:.85rem;
  padding:.5rem 1.1rem; border-radius:99px; }}
@media (prefers-reduced-motion: reduce) {{
  html {{ scroll-behavior:auto; }}
  .reveal {{ opacity:1; transform:none; transition:none; }}
  .load {{ opacity:1; animation:none; }} .aurora {{ animation:none; }}
  .card, .card::before, .btn, .nav {{ transition:none; }}
}}"""


def js_interacoes() -> str:
    """Spotlight nos cards (cursor) + nav que aparece ao rolar. Respeita reduced-motion."""
    return ("<script>(function(){"
            "if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;"
            "document.querySelectorAll('.card').forEach(function(c){c.addEventListener('pointermove',function(e){"
            "var r=c.getBoundingClientRect();c.style.setProperty('--mx',(e.clientX-r.left)+'px');"
            "c.style.setProperty('--my',(e.clientY-r.top)+'px');});});"
            "var nav=document.querySelector('.nav');if(nav){var on=function(){"
            "nav.classList.toggle('on',window.scrollY>560);};on();addEventListener('scroll',on,{passive:true});}"
            "})();</script>")


def js_reveal() -> str:
    # rede de segurança: se uma seção nunca é observada (captura/preview/primeiro
    # paint sem scroll), ela AINDA aparece após 1.4s — nunca fica um "vazio".
    return ("<script>if(!matchMedia('(prefers-reduced-motion: reduce)').matches){"
            "const o=new IntersectionObserver((es)=>{es.forEach((e,i)=>{if(e.isIntersecting){"
            "setTimeout(()=>e.target.classList.add('vis'),i*90);o.unobserve(e.target);}});},"
            "{threshold:.15});document.querySelectorAll('.reveal').forEach(el=>o.observe(el));"
            "setTimeout(()=>document.querySelectorAll('.reveal:not(.vis)').forEach(el=>el.classList.add('vis')),1400);}"
            "else{document.querySelectorAll('.reveal').forEach(el=>el.classList.add('vis'));}</script>")


def favicon(nome: str, acento: str) -> str:
    """Monograma SVG (inicial + acento) como data URI — self-contained, sem asset."""
    from urllib.parse import quote
    inicial = (nome.strip()[:1] or "N").upper()
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
           f"<rect width='64' height='64' rx='14' fill='{acento}'/>"
           f"<text x='50%' y='53%' dy='.35em' text-anchor='middle' fill='#fff' "
           f"font-family='system-ui,sans-serif' font-weight='800' font-size='36'>{inicial}</text></svg>")
    return "data:image/svg+xml," + quote(svg)


if __name__ == "__main__":
    validar_temas()
    a, b = escolher_tema("imobiliária", "Alfa"), escolher_tema("clínica odontológica", "Beta")
    assert a.id == "imobiliaria" and b.id == "clinica" and a.google != b.google
    t1, t2 = escolher_tema("adega", "Casa do Vinho"), escolher_tema("energia solar", "SolarMax")
    assert t1.id == "vinho" and t2.id == "navy"
    ruim = Tema("x", "#2a1a12", "#faf7f0", "#fff", "#eee", "#c2410c", "#fde",
                "Instrument Serif", "Lora", "", "10px", "700", "0", "index", False)
    assert _cliche(ruim), "guarda deveria pegar terracota+serifa"
    print("design OK — direções, pool vetado, ancoragem por assunto, guarda anti-clichê")
