"""Sequência 360 SINTÉTICA para teste — nada de foto de cliente.

O viewer só liga com 24+ quadros (viewer360.MIN_FRAMES), então testá-lo de verdade
exige uma sequência de verdade. Gerar aqui em SVG resolve três problemas de uma vez:
o teste não depende de asset de nenhuma conta, roda offline, e cada quadro é
VISUALMENTE distinto — o que permite afirmar que o arrasto trocou de quadro em vez
de só conferir que uma classe CSS mudou.

O objeto é uma caneca genérica de encomenda: produto de exemplo, sem marca.
"""
from __future__ import annotations

import math

QUADROS = 32


def svg(i: int, total: int = QUADROS) -> str:
    """Quadro `i` da volta. A alça gira em torno do corpo e o número do quadro fica
    impresso — é ele que o teste lê pra provar qual quadro está visível."""
    ang = 2 * math.pi * i / total
    # alça some quando passa por trás: é o que dá a leitura de rotação
    x = 120 + 46 * math.cos(ang)
    atras = math.cos(ang) < 0
    tom = 60 + int(40 * (1 + math.sin(ang)) / 2)
    alca = (f'<ellipse cx="{x:.1f}" cy="118" rx="17" ry="26" fill="none" '
            f'stroke="hsl(212 55% {tom}%)" stroke-width="9"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="240" height="240">'
        f'<rect width="240" height="240" fill="#f4f4f5"/>'
        # alça atrás do corpo em metade da volta, na frente na outra
        f'{alca if atras else ""}'
        f'<rect x="74" y="72" width="92" height="112" rx="12" fill="hsl(212 55% {tom}%)"/>'
        f'<ellipse cx="120" cy="72" rx="46" ry="12" fill="hsl(212 40% {min(tom + 18, 96)}%)"/>'
        f'{"" if atras else alca}'
        f'<text x="120" y="214" text-anchor="middle" font-family="monospace" '
        f'font-size="20" fill="#111" data-quadro="{i}">{i:02d}</text>'
        f"</svg>"
    )


def escrever(destino) -> list[str]:
    """Grava os quadros e devolve os caminhos relativos, prontos pro produto."""
    destino.mkdir(parents=True, exist_ok=True)
    caminhos = []
    for i in range(QUADROS):
        nome = f"q{i:02d}.svg"
        (destino / nome).write_text(svg(i), encoding="utf-8")
        caminhos.append(f"giro/{nome}")
    return caminhos


if __name__ == "__main__":
    a, b = svg(0), svg(QUADROS // 2)
    assert a != b, "quadros opostos da volta têm que ser diferentes"
    assert 'data-quadro="0"' in a and f'data-quadro="{QUADROS // 2}"' in b
    print(f"frames_exemplo OK — {QUADROS} quadros SVG distintos, sem asset de cliente")
