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
]

# Efeitos que CSS comum não entrega bem → viram asset Higgsfield (lista viva).
FORA_DO_CSS = [
    "morphing orgânico de formas/blobs 3D",
    "simulação de fluido/partículas/fumaça reativa",
    "câmera 3D atravessando cena (fly-through)",
    "transição cinematográfica com motion-blur real",
    "personagem/produto animado quadro-a-quadro",
    "distorção/liquify de imagem em tempo real",
]


def classificar(efeito: str, replicavel: bool | None = None) -> dict:
    """Decide se o efeito é nativo. `replicavel` vem da extração de design (LLM/visão)
    que compara contra NATIVO; se None, heurística por palavra-chave contra FORA_DO_CSS.
    Devolve {nativo, acao} — 'css' (o template faz) ou 'asset' (gera prompt Higgsfield)."""
    if replicavel is None:
        e = (efeito or "").lower()
        pesado = any(k in e for k in ("3d", "partícul", "particul", "fluido", "fumaça", "fumaca",
                                      "morph", "blob", "liquify", "quadro-a-quadro", "fly", "motion-blur",
                                      "motion blur", "câmera", "camera"))
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
    assert classificar("morphing de blob 3D com fluido")["acao"] == "asset"
    r = prompt_higgsfield("câmera 3D atravessando um túnel de dados neon", contexto="hero")
    assert "Higgsfield" not in r["prompt_higgsfield"] and "#00e6a2" in r["prompt_higgsfield"]
    assert r["papel"].startswith("transição")
    assert "video" in r["como_incorporar"] and len(NATIVO) >= 6
    print("motion_gap OK — classifica nativo/asset, gera prompt Higgsfield da marca")
