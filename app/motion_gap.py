"""Motion-gap → asset Higgsfield (regra PERMANENTE do pipeline de design).

Diferencial da casa: a maioria dos sites-isca do mercado é ESTÁTICA. Quando um
vídeo de referência mostra um efeito de movimento/transição que o motor NÃO
consegue replicar nativamente (CSS/motion comum), em vez de forçar (fica feio)
ou pular (perde o diferencial), o motor GERA UM PROMPT específico descrevendo o
efeito — pro JP criar o asset (vídeo/animação via Higgsfield) e o site incorporar
isso como transição/feature REAL do produto, não decoração.

Fluxo no pipeline de design (quando os vídeos de referência chegam):
  radar-visão extrai o efeito → `classificar()` decide replicável? →
    sim  → o template faz em CSS (lista NATIVO abaixo)
    não  → `prompt_higgsfield()` emite a ordem de trabalho do asset
"""
from __future__ import annotations

# O que o template JÁ faz nativamente (CSS/JS leve). A extração de design compara
# o efeito do vídeo contra isto: se cai aqui, é replicável — não precisa de asset.
NATIVO = [
    "scroll-reveal (fade + translateY on-view, IntersectionObserver + spring)",
    "stagger de entrada (delay por índice)",
    "aurora/gradiente animado no hero",
    "spotlight/hover glow nos cards",
    "parallax leve (translate no scroll)",
    "fade / slide / scale simples entre estados",
    "contador/números animados",
    "acordeão (FAQ) com transição de altura",
    "sticky nav + shrink no scroll",
    # entraram com a stack pesada (2026-08-11) — app/stack_pesada.py:
    "seção pinada com sequência encadeada no scroll (GSAP ScrollTrigger)",
    "campo de fundo orgânico/fluido em tempo real (Three.js, shader)",
    "morphing de formas por domain warping no shader",
]

# Efeitos que CSS comum não entrega bem → viram asset Higgsfield (lista viva).
#
# ENCOLHEU EM 2026-08-11. GSAP e Three.js entraram no motor, e três itens que
# custavam um vídeo Higgsfield por cliente viraram render em tempo real: morphing
# orgânico, fluido/partículas e distorção/liquify. O que sobra aqui é o que shader
# de fundo genuinamente não faz — cena com câmera, motion-blur cinematográfico e
# personagem animado, que precisam de conteúdo autoral, não de técnica.
#
# Manter item resolvido nesta lista custa dinheiro de verdade: o motor pediria um
# asset pago pra um efeito que ele já renderiza de graça.
FORA_DO_CSS = [
    "câmera 3D atravessando cena (fly-through)",
    "transição cinematográfica com motion-blur real",
    "personagem/produto animado quadro-a-quadro",
]


def classificar(efeito: str, replicavel: bool | None = None) -> dict:
    """Decide se o efeito é nativo. `replicavel` vem da extração de design (LLM/visão)
    que compara contra NATIVO; se None, heurística por palavra-chave contra FORA_DO_CSS.
    Devolve {nativo, acao} — 'css' (o template faz) ou 'asset' (gera prompt Higgsfield)."""
    if replicavel is None:
        e = (efeito or "").lower()
        # A lista encolheu junto com FORA_DO_CSS (2026-08-11). Saíram "3d",
        # "partícul", "fluido", "fumaça", "morph", "blob" e "liquify": o shader do
        # campo faz todos. O que sobrou tem em comum não ser questão de técnica e
        # sim de CONTEÚDO AUTORAL — câmera precisa de cena, quadro-a-quadro precisa
        # de personagem. Nenhum shader inventa isso.
        pesado = any(k in e for k in ("quadro-a-quadro", "quadro a quadro", "personagem",
                                      "fly", "motion-blur", "motion blur",
                                      "câmera", "camera"))
        replicavel = not pesado
    return {"efeito": efeito, "nativo": bool(replicavel),
            "acao": "css" if replicavel else "asset"}


def prompt_higgsfield(efeito: str, *, marca: str = "JPOS", contexto: str = "") -> dict:
    """Ordem de trabalho do asset: prompt pronto pro Higgsfield + como o site incorpora.
    O asset é FEATURE (transição/hero/loop de produto), não enfeite."""
    prompt = (
        f"{efeito}. Estilo visual da marca {marca}: tech/dark, acento neon verde-água "
        f"(#00e6a2) sobre fundo quase-preto (#0c1017), estética limpa e premium (não "
        f"cartunesca). Loop perfeito (primeiro e último frame idênticos), fundo "
        f"transparente ou preto sólido pra key, 4-6s, 1080p vertical ou quadrado. "
        f"Sem texto na cena (o texto é HTML por cima)."
        + (f" Contexto: {contexto}." if contexto else "")
    )
    return {
        "efeito": efeito,
        "prompt_higgsfield": prompt,
        "como_incorporar": ("Exporta MP4/WebM com alpha (ou preto pra multiply/screen). "
                            "O site embute como <video autoplay muted loop playsinline> na "
                            "seção alvo (hero de fundo, transição entre seções, ou loop de "
                            "produto) — CSS mix-blend-mode: screen pra fundir com o dark."),
        "papel": "transição/feature real (não decoração)",
    }


if __name__ == "__main__":  # self-check: nativo vs asset + prompt bem-formado
    assert classificar("scroll-reveal com fade")["acao"] == "css"
    # ERA "asset" até 2026-08-11. Com Three.js no motor, isto é o shader do campo —
    # pedir um vídeo pago pra um efeito que o site renderiza sozinho era o custo que
    # a stack pesada veio eliminar.
    assert classificar("morphing de blob 3D com fluido")["acao"] == "css"
    assert classificar("câmera atravessando um túnel")["acao"] == "asset"
    assert classificar("personagem animado quadro-a-quadro")["acao"] == "asset"
    r = prompt_higgsfield("câmera 3D atravessando um túnel de dados neon", contexto="hero")
    assert "Higgsfield" not in r["prompt_higgsfield"] and "#00e6a2" in r["prompt_higgsfield"]
    assert r["papel"].startswith("transição")
    assert "video" in r["como_incorporar"] and len(NATIVO) >= 6
    print("motion_gap OK — classifica nativo/asset, gera prompt Higgsfield da marca")
