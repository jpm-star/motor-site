"""Hero 360° por SEQUÊNCIA DE FOTOS — para sites tipo "loja" (produto físico).

FRAMEWORK DO MOTOR (resposta definitiva, pra ninguém perguntar de novo):
o Motor Site gera **HTML estático puro**, montado por f-string em Python. Não há
Next.js, React, Vite nem build de JS. Logo: nada de React Three Fiber, nada de
import de módulo npm — o que sair daqui é HTML + CSS + JS vanilla inline.

POR QUE SPRITE-SEQUENCE E NÃO 3D:
foto real do produto bate modelo sintético. Quem compra vê o que vai receber, não
uma aproximação renderizada — e some o custo de gerar um GLB por SKU. Three.js só
se justifica quando JÁ existe GLB (via `generate_3d` do Motor B); gerar 3D só pra
ter hero não fecha contra trocar imagem por índice.

PESO: zero JS de terceiros. O viewer inteiro é ~1,5 KB e só é emitido quando o
cliente é "loja" E tem sequência — T1/T2 sem sequência não pagam nada por isso.
"""
from __future__ import annotations

import html
import json

# Mínimo pra ilusão de rotação funcionar. Abaixo disso o giro "pula" e lê como
# slideshow, que é pior que uma foto boa parada.
MIN_FRAMES = 24


def tem_sequencia(produto: dict) -> bool:
    """Só há viewer se houver sequência de verdade. Meia sequência é pior que
    nenhuma: o dedo arrasta e o produto trava no meio da volta."""
    return len(produto.get("sequencia_360") or []) >= MIN_FRAMES


def css() -> str:
    return """
.v360{position:relative;aspect-ratio:1;width:100%;max-width:640px;margin-inline:auto;
  background:var(--bg-suave,#f4f4f5);border-radius:var(--raio,14px);overflow:hidden;
  touch-action:pan-y;cursor:grab;user-select:none}
.v360:active{cursor:grabbing}
.v360 img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;
  opacity:0;transition:opacity .05s linear;pointer-events:none}
.v360 img.on{opacity:1}
.v360__dica{position:absolute;left:0;right:0;bottom:6%;text-align:center;margin:0;
  font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;opacity:.55;
  transition:opacity .4s ease;pointer-events:none}
.v360.mexeu .v360__dica{opacity:0}
.v360__carga{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
  font-size:.8rem;opacity:.6}
@media (prefers-reduced-motion: reduce){.v360 img{transition:none}}"""


def html_bloco(produto: dict, alt: str = "") -> str:
    """O viewer. Emite os <img> no HTML (não em JS) pra que sem JavaScript o
    visitante ainda veja o primeiro quadro — degrada pra foto, nunca pra vazio."""
    frames = produto.get("sequencia_360") or []
    if len(frames) < MIN_FRAMES:
        return ""
    nome = html.escape(str(produto.get("nome", "produto")))
    imgs = "\n".join(
        f'<img src="{html.escape(f)}" alt="{html.escape(alt) if i == 0 else ""}" '
        f'class="{"on" if i == 0 else ""}" loading="{"eager" if i == 0 else "lazy"}" '
        f'decoding="async" draggable="false">'
        for i, f in enumerate(frames))
    return f"""
<div class="v360" data-v360 data-total="{len(frames)}" role="img"
     aria-label="{nome} — vista 360 graus, arraste para girar">
  {imgs}
  <p class="v360__carga" data-carga>carregando 360°…</p>
  <p class="v360__dica" data-dica>arraste para girar</p>
</div>"""


def js() -> str:
    """Vanilla, inline, sem dependência.

    Detalhes que decidem se parece produto ou brinquedo:
    - PRÉ-CARREGA tudo antes de liberar o gesto. Sem isso, o dedo arrasta e cai num
      quadro ainda não baixado — o produto "pisca" e a ilusão morre.
    - `touch-action: pan-y` no CSS: o giro horizontal é nosso, a rolagem vertical
      continua do navegador. Sem isso o viewer sequestra o scroll e o visitante
      fica preso no hero — é o erro clássico de carrossel em celular.
    - Índice por posição ABSOLUTA do arrasto, não por delta acumulado: soltar e
      pegar de novo continua de onde parou, em vez de dar um salto.
    """
    return """
(function(){
  for (const v of document.querySelectorAll('[data-v360]')) {
    const imgs = v.querySelectorAll('img'), total = imgs.length;
    const carga = v.querySelector('[data-carga]');
    let atual = 0, base = 0, x0 = null, pronto = false, faltam = total;

    const mostrar = (i) => {
      const n = ((i % total) + total) % total;
      if (n === atual) return;
      imgs[atual].classList.remove('on'); imgs[n].classList.add('on'); atual = n;
    };
    // libera o gesto só quando TODO quadro está em cache
    const conta = () => { if (--faltam <= 0) { pronto = true; carga.remove(); } };
    imgs.forEach((im) => im.complete ? conta() : (im.onload = im.onerror = conta));

    const px = (e) => (e.touches ? e.touches[0].clientX : e.clientX);
    const inicio = (e) => { if (!pronto) return; x0 = px(e); base = atual; v.classList.add('mexeu'); };
    const move = (e) => {
      if (x0 === null || !pronto) return;
      // uma tela de arrasto = uma volta completa; sensibilidade previsível em
      // qualquer largura, do celular ao monitor
      const passo = (px(e) - x0) / v.clientWidth;
      mostrar(Math.round(base + passo * total));
      if (e.cancelable && e.touches) e.preventDefault();
    };
    const fim = () => { x0 = null; };

    v.addEventListener('mousedown', inicio); addEventListener('mousemove', move); addEventListener('mouseup', fim);
    v.addEventListener('touchstart', inicio, {passive:true});
    v.addEventListener('touchmove', move, {passive:false});
    v.addEventListener('touchend', fim);
    // teclado: seta gira um quadro. Sem isto o viewer é inacessível a quem não
    // usa mouse nem toque, e ele carrega informação de produto.
    v.tabIndex = 0;
    v.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight') mostrar(atual + 1);
      else if (e.key === 'ArrowLeft') mostrar(atual - 1);
      else return;
      e.preventDefault();
    });
  }
})();"""


def peso() -> dict:
    c, j = css(), js()
    return {"css_bytes": len(c.encode()), "js_bytes": len(j.encode()),
            "total_kb": round((len(c.encode()) + len(j.encode())) / 1024, 2)}


if __name__ == "__main__":
    vazio = {"nome": "X", "sequencia_360": [f"/f/{i}.webp" for i in range(10)]}
    cheio = {"nome": "Chinelo", "sequencia_360": [f"/f/{i}.webp" for i in range(32)]}
    assert not tem_sequencia(vazio) and html_bloco(vazio) == "", "sequência curta tem que ser recusada"
    assert tem_sequencia(cheio)
    b = html_bloco(cheio, alt="Chinelo girando")
    assert b.count("<img") == 32 and 'class="on"' in b and 'loading="eager"' in b
    assert "touch-action:pan-y" in css(), "sem isso o viewer sequestra o scroll do celular"
    p = peso()
    assert p["total_kb"] < 5, p
    print(f"viewer360 OK — {p['css_bytes']}B css + {p['js_bytes']}B js = {p['total_kb']} KB, "
          f"zero dependência, recusa sequência < {MIN_FRAMES} frames")
