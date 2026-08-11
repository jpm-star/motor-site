"""Hero 360 no navegador de verdade — arrasto, teclado e degradação.

POR QUE E2E E NÃO SÓ UNIT: `viewer360.py` já tem self-check, mas ele prova que a
STRING sai certa. O que decide se o produto gira é o navegador: o gesto chega, o
índice avança, o quadro certo aparece. Nada disso é visível de dentro do Python —
e foi exatamente esse tipo de falha que passou batido antes (filtro de cor no ar
sem esconder card nenhum, botão preto no preto).

Cada teste afirma o QUADRO VISÍVEL, lido do <text data-quadro> do SVG. Conferir só
"a classe .on mudou" passaria mesmo se o viewer mostrasse o quadro errado.

Roda com: <venv-com-playwright>/python -m pytest tests/test_viewer360_e2e.py
Sem playwright instalado, a suíte pula em vez de quebrar o CI do motor.
"""
from __future__ import annotations

import http.server
import pathlib
import socket
import tempfile
import threading

import pytest

pytest.importorskip("playwright.sync_api",
                    reason="playwright ausente — teste E2E pulado (unit segue valendo)")

from playwright.sync_api import sync_playwright  # noqa: E402

from app import viewer360  # noqa: E402
from tests import frames_exemplo  # noqa: E402

PAGINA = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<style>{css}</style></head><body>{html}<script>{js}</script></body></html>"""


@pytest.fixture(scope="module")
def site():
    """Serve uma página com o viewer e a sequência sintética. Servidor em porta
    efêmera: fixar porta faz o teste brigar com qualquer coisa já rodando na VPS —
    já perdi uma rodada por um http.server esquecido de outra sessão."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="v360-"))
    caminhos = frames_exemplo.escrever(tmp / "giro")
    produto = {"nome": "Caneca de encomenda", "sequencia_360": caminhos}
    (tmp / "index.html").write_text(PAGINA.format(
        css=viewer360.css(),
        html=viewer360.html_bloco(produto, alt="Caneca girando"),
        js=viewer360.js()), encoding="utf-8")

    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    porta = s.getsockname()[1]
    s.close()

    srv = http.server.ThreadingHTTPServer(
        ("127.0.0.1", porta),
        lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(tmp), **k))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{porta}/"
    srv.shutdown()


def _quadro_visivel(pg) -> int:
    """Qual quadro está na tela AGORA, lido do próprio SVG renderizado."""
    return pg.evaluate("""(async () => {
      const im = document.querySelector('.v360 img.on');
      const txt = await (await fetch(im.getAttribute('src'))).text();
      return parseInt(txt.match(/data-quadro="(\\d+)"/)[1], 10);
    })()""")


def _pronto(pg):
    """O viewer só aceita gesto depois de pré-carregar tudo (some o aviso)."""
    pg.wait_for_selector(".v360 [data-carga]", state="detached", timeout=15000)


@pytest.fixture(scope="module")
def navegador():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def test_primeiro_quadro_aparece_sem_gesto(navegador, site):
    """Antes de qualquer interação o produto já tem que estar visível — degradar
    pra vazio seria pior que uma foto parada."""
    pg = navegador.new_page(viewport={"width": 900, "height": 900})
    pg.goto(site, wait_until="load")
    _pronto(pg)
    assert _quadro_visivel(pg) == 0
    assert pg.locator(".v360 img").count() == frames_exemplo.QUADROS
    pg.close()


def test_arrastar_gira_o_produto(navegador, site):
    """O teste que justifica o E2E: arrastar meia tela tem que avançar ~meia volta.

    Uma tela de arrasto = uma volta (viewer360.js). Meia tela em 32 quadros ≈ 16,
    com folga porque o arredondamento depende do pixel exato onde o mouse parou.
    """
    pg = navegador.new_page(viewport={"width": 900, "height": 900})
    pg.goto(site, wait_until="load")
    _pronto(pg)
    caixa = pg.locator(".v360").bounding_box()
    y = caixa["y"] + caixa["height"] / 2
    pg.mouse.move(caixa["x"] + caixa["width"] * 0.15, y)
    pg.mouse.down()
    pg.mouse.move(caixa["x"] + caixa["width"] * 0.65, y, steps=12)
    pg.mouse.up()
    pg.wait_for_timeout(150)
    q = _quadro_visivel(pg)
    assert 12 <= q <= 20, f"meia tela de arrasto devia dar ~meia volta, deu quadro {q}"
    pg.close()


def test_soltar_e_pegar_de_novo_continua_de_onde_parou(navegador, site):
    """Índice por posição ABSOLUTA, não por delta acumulado. Se o segundo arrasto
    reiniciasse do zero, o produto daria um salto — o defeito que faz o giro
    parecer quebrado mesmo com tudo 'funcionando'."""
    pg = navegador.new_page(viewport={"width": 900, "height": 900})
    pg.goto(site, wait_until="load")
    _pronto(pg)
    c = pg.locator(".v360").bounding_box()
    y = c["y"] + c["height"] / 2
    for inicio, fim in ((0.20, 0.45), (0.20, 0.45)):
        pg.mouse.move(c["x"] + c["width"] * inicio, y)
        pg.mouse.down()
        pg.mouse.move(c["x"] + c["width"] * fim, y, steps=8)
        pg.mouse.up()
        pg.wait_for_timeout(120)
    q = _quadro_visivel(pg)
    # dois arrastos de 1/4 de tela ≈ meia volta acumulada; reiniciar daria ~8
    assert 12 <= q <= 20, f"o segundo arrasto não continuou de onde parou (quadro {q})"
    pg.close()


def test_teclado_gira_um_quadro(navegador, site):
    """Sem isto o viewer é inacessível a quem não usa mouse nem toque — e ele
    carrega informação de produto, não decoração."""
    pg = navegador.new_page(viewport={"width": 900, "height": 900})
    pg.goto(site, wait_until="load")
    _pronto(pg)
    pg.locator(".v360").focus()
    pg.keyboard.press("ArrowRight")
    pg.wait_for_timeout(80)
    assert _quadro_visivel(pg) == 1
    pg.keyboard.press("ArrowLeft")
    pg.wait_for_timeout(80)
    assert _quadro_visivel(pg) == 0
    pg.close()


def test_sem_javascript_ainda_mostra_o_produto(navegador, site):
    """Progressive enhancement: o <img> do primeiro quadro é HTML, não JS. Rede
    ruim ou script bloqueado tem que degradar pra foto, nunca pra buraco."""
    ctx = navegador.new_context(java_script_enabled=False,
                                viewport={"width": 900, "height": 900})
    pg = ctx.new_page()
    pg.goto(site, wait_until="load")
    assert pg.locator(".v360 img.on").count() == 1
    assert pg.locator(".v360 img.on").is_visible()
    ctx.close()


def test_nao_sequestra_a_rolagem_no_celular(navegador, site):
    """`touch-action: pan-y` é o que deixa o giro horizontal pro viewer e a rolagem
    vertical pro navegador. Sem isso o visitante fica preso no hero — o erro
    clássico de carrossel em celular."""
    ctx = navegador.new_context(viewport={"width": 390, "height": 844},
                                has_touch=True, is_mobile=True)
    pg = ctx.new_page()
    pg.goto(site, wait_until="load")
    assert "pan-y" in pg.evaluate(
        "getComputedStyle(document.querySelector('.v360')).touchAction")
    ctx.close()
