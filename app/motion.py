"""Camada de MOTION tokenizada — o "ritmo" do site, parametrizado por segmento.

Por que tokens e não CSS fixo: o que faz um site parecer caro não são as cenas 3D
(essas são peça única, feitas à mão, e ficam FORA do gerador). É o ritmo — duração,
atraso entre entradas, curva de easing, o quanto as formas fogem do retângulo. Isso
é parametrizável, então vira token e varia por segmento: uma clínica não se move
como uma oficina.

OS 5 TOKENS
  duracao    (s)   quanto dura cada entrada
  stagger    (s)   atraso ENTRE elementos vizinhos — é o que lê como "dirigido"
  easing     (cb)  a curva; spring dá peso físico, ease-out dá sobriedade
  curvatura  (0-1) o quanto as máscaras fogem do retângulo (0 = canto reto)
  semente    (int) forma da curva do traço SVG que costura as seções

O QUE NÃO ENTRA AQUI: WebGL/Three.js. Cena 3D narrativa é peça única cobrada à
parte — num gerador ela sairia idêntica pra clínica, academia e advogado, e deixa
de ser diferencial no primeiro cliente que vir o site do outro.

Orçamento: esta camada inteira (CSS+JS) tem que caber em ~15 KB por página.
`orcamento()` mede e é verificado no self-check.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

# Curvas nomeadas. `spring` passa do alvo e volta — é o "peso" que o olho lê como
# caro; `saida` é sóbria, pra segmento que não pode parecer brincalhão (jurídico,
# saúde séria). Nomear em vez de espalhar cubic-bezier pelo CSS mantém o token legível.
EASINGS = {
    "spring": "cubic-bezier(.175,.885,.32,1.275)",
    "saida": "cubic-bezier(.22,.61,.36,1)",
    "suave": "cubic-bezier(.4,0,.2,1)",
}


@dataclass(frozen=True)
class Motion:
    duracao: float = 0.7
    stagger: float = 0.1
    easing: str = "spring"
    curvatura: float = 0.0
    semente: int = 0

    @property
    def curva(self) -> str:
        return EASINGS.get(self.easing, EASINGS["spring"])

    def raio(self) -> str:
        """border-radius assimétrico derivado da curvatura.

        Quatro cantos IGUAIS lêem como caixa arredondada — genérico. O que dá
        aparência de peça desenhada é a assimetria, e ela precisa ser estável por
        semente, senão dois sites do mesmo segmento saem diferentes sem motivo.
        """
        if self.curvatura <= 0:
            return "var(--raio, 14px)"
        base = 8 + self.curvatura * 46
        h = _ruido(self.semente)
        cantos = [round(base * (0.35 + (h(i) * 0.65)), 1) for i in range(4)]
        return " ".join(f"{c}% {100 - c}% {100 - c}% {c}% / {c}% {c}% {100 - c}% {100 - c}%"
                        for c in [cantos[0]])  # 1 forma; variar por card viraria ruído


def _ruido(semente: int):
    """Gerador determinístico 0..1. `random` daria forma diferente a cada build —
    o mesmo site precisa sair igual duas vezes."""
    def f(i: int) -> float:
        d = hashlib.sha256(f"{semente}:{i}".encode()).digest()
        return d[0] / 255
    return f


# Presets por segmento. Não é enfeite: é o único lugar onde "clínica" e "oficina"
# se movem diferente sem alguém editar CSS à mão.
PRESETS = {
    "clinica":     Motion(0.75, 0.10, "saida",  0.55, 11),
    "odonto":      Motion(0.72, 0.09, "saida",  0.50, 23),
    "estetica":    Motion(0.85, 0.13, "spring", 0.75, 37),
    "fisio":       Motion(0.68, 0.08, "suave",  0.40, 41),
    "salao":       Motion(0.90, 0.14, "spring", 0.80, 53),
    "psico":       Motion(0.95, 0.12, "suave",  0.35, 67),
    "imobiliaria": Motion(0.70, 0.10, "saida",  0.30, 71),
    "oficina":     Motion(0.55, 0.06, "suave",  0.15, 83),
    "jpos":        Motion(0.80, 0.11, "spring", 0.60, 97),
}
PADRAO = Motion()


def para(segmento: str) -> Motion:
    """Preset do segmento. Casa por SUBSTRING, não igualdade.

    O nicho chega como texto livre do briefing ("clínica odontológica em Bauru"),
    nunca como a chave exata. Com igualdade, 9 em cada 10 sites caíam no padrão —
    curvatura 0, traço reto — e a camada inteira ficava inerte sem ninguém notar,
    porque nada quebra: só fica genérico.
    """
    s = _sem_acento((segmento or "").strip().lower())
    if s in PRESETS:
        return PRESETS[s]
    # chave mais LONGA primeiro: "imobiliaria" antes de "obra" em "imobiliaria e obras"
    for chave in sorted(PRESETS, key=len, reverse=True):
        if chave in s:
            return PRESETS[chave]
    return PADRAO


def _sem_acento(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def css(m: Motion | None = None) -> str:
    """CSS da camada tokenizada. Complementa `design.css_motion*`, não substitui.

    Só o que NÃO existia lá: máscara orgânica e traço SVG. Reescrever o que já
    funciona (reveal, stagger, cortina, título palavra a palavra) seria trocar
    código testado por código novo pelo mesmo resultado.
    """
    m = m or PADRAO
    return f"""
:root {{
  --mo-dur: {m.duracao}s; --mo-stagger: {m.stagger}s; --mo-ease: {m.curva};
}}
/* Escalonamento por índice: o atraso vira token, então o "ritmo" muda por
   segmento sem tocar no HTML. `--i` é posto no elemento pelo template. */
[data-mo-seq] > * {{ animation-delay: calc(var(--i, 0) * var(--mo-stagger)); }}
/* MÁSCARA ORGÂNICA — a diferença entre "tem imagem" e "foi desenhado". Cantos
   assimétricos derivados da curvatura+semente do segmento. */
.mo-organico {{ border-radius: {m.raio()}; overflow: hidden; }}
.mo-organico > img, .mo-organico > picture > img {{ display:block; width:100%; height:100%; object-fit:cover; }}
/* TRAÇO que costura as seções. Desenha conforme a página rola; sem suporte a
   scroll-timeline ele simplesmente aparece inteiro — nunca some. */
.mo-traco {{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; z-index:0; overflow:visible; }}
.mo-traco path {{ fill:none; stroke:var(--acento); stroke-width:{2 + m.curvatura * 5:.1f}; stroke-linecap:round;
  opacity:.5; stroke-dasharray:1400; stroke-dashoffset:0; }}
@supports (animation-timeline: view()) {{
  @media (prefers-reduced-motion: no-preference) {{
    .mo-traco path {{ stroke-dashoffset:1400; animation: mo-desenha linear both; animation-timeline: view(); animation-range: entry 5% cover 60%; }}
    @keyframes mo-desenha {{ to {{ stroke-dashoffset: 0; }} }}
  }}
}}
@media (prefers-reduced-motion: reduce) {{
  [data-mo-seq] > * {{ animation-delay: 0s !important; }}
  .mo-traco path {{ stroke-dashoffset: 0; animation: none; }}
}}"""


def svg_traco(m: Motion | None = None, largura: int = 1200, altura: int = 600) -> str:
    """O traço em si. Curva estável por semente: o mesmo segmento gera sempre a
    mesma assinatura, segmentos diferentes geram assinaturas diferentes."""
    m = m or PADRAO
    h = _ruido(m.semente)
    pts = []
    for i in range(4):
        x = largura * (i / 3)
        y = altura * (0.25 + h(i) * 0.5)
        pts.append((x, y))
    d = f"M {pts[0][0]:.0f} {pts[0][1]:.0f}"
    for i in range(1, 4):
        cx = (pts[i - 1][0] + pts[i][0]) / 2
        d += f" C {cx:.0f} {pts[i-1][1]:.0f}, {cx:.0f} {pts[i][1]:.0f}, {pts[i][0]:.0f} {pts[i][1]:.0f}"
    return (f'<svg class="mo-traco" viewBox="0 0 {largura} {altura}" preserveAspectRatio="none" '
            f'aria-hidden="true" focusable="false"><path d="{d}"/></svg>')


def orcamento(m: Motion | None = None) -> dict:
    """Peso desta camada. O self-check falha se estourar — orçamento que ninguém
    mede vira orçamento que ninguém respeita."""
    c = css(m)
    s = svg_traco(m)
    return {"css_bytes": len(c.encode()), "svg_bytes": len(s.encode()),
            "js_bytes": 0,  # esta camada é CSS puro: scroll-timeline nativo, sem JS
            "total_kb": round((len(c.encode()) + len(s.encode())) / 1024, 2)}


if __name__ == "__main__":
    for seg in ("clinica", "estetica", "oficina"):
        mm = para(seg)
        o = orcamento(mm)
        assert o["total_kb"] < 15, (seg, o)
        assert "cubic-bezier" in css(mm) and "<path" in svg_traco(mm)
        print(f"{seg:10} dur={mm.duracao}s stagger={mm.stagger}s {mm.easing:6} "
              f"curv={mm.curvatura} | {o['total_kb']} KB")
    # determinismo: mesma semente, mesmo traço (build reprodutível)
    assert svg_traco(para("clinica")) == svg_traco(para("clinica"))
    assert svg_traco(para("clinica")) != svg_traco(para("estetica"))
    # nicho vem como texto livre do briefing — o casamento tem que sobreviver a isso
    assert para("clinica odontologica em Bauru").curvatura == PRESETS["clinica"].curvatura
    assert para("Estética Avançada").easing == "spring"
    assert para("salão de beleza").stagger == PRESETS["salao"].stagger
    assert para("coisa que nao existe") == PADRAO
    print("motion OK — 5 tokens, CSS puro, determinístico, dentro do orçamento")
