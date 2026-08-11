"""Stack pesada — GSAP/ScrollTrigger e Three.js, atrás de um portão.

DECISÃO (JP, 2026-08-11): "GSAP e Three.js entram agora." Este módulo é o como.

O QUE CUSTA, MEDIDO (gzip, que é o que o Caddy manda no fio):
    camada CSS (motion.py)   1,7 KB   0 JS    ← continua sendo o PISO, sempre presente
    cena-v1.js  (GSAP+ST)     44,1 KB          ← só se a página tiver [data-cena]
    campo-v1.js (Three)      119,0 KB          ← só se a página tiver [data-campo]

VIABILIZAÇÃO — as três regras que fazem 163 KB não virar um site lento:

1. O CUSTO SEGUE O USO, NÃO O TIER. Não há gate por tier: um T1 com cena pinada
   baixa a cena; um T4 sem campo não baixa Three. Amarrar peso a tier cobraria de
   quem não usa e bloquearia quem usa.

2. CARREGA DEPOIS DO LCP. `load` + idle callback. O HTML e o CSS crítico já
   pintaram; a stack chega no tempo ocioso. É isto que mantém o LCP igual ao de
   antes — medido, não suposto.

3. O CSS É O PISO, O JS É O TETO. A página está completa e bonita sem nenhum
   byte de JS. GSAP e Three só REFINAM. Rede caiu, WebGL ausente, aparelho fraco,
   `prefers-reduced-motion` — em todos, o visitante vê a versão CSS, nunca um
   buraco. Um efeito que só existe com 119 KB baixados não é uma feature, é uma
   aposta na conexão do visitante.

QUEM NÃO PAGA NADA: reduced-motion, `saveData` ligado, 2G, e — só pro campo —
menos de 4 GB de RAM ou 4 núcleos. Esses recebem exatamente o site de hoje.
"""
from __future__ import annotations

# Versionado no NOME do arquivo: o Caddy serve /_lib com cache imutável de 1 ano.
# Trocar o conteúdo sem trocar a versão entregaria bundle velho por um ano — a
# versão sobe no build, junto com o arquivo.
VERSAO = "v1"
BASE = "/_lib"

# RAM (GB) e núcleos abaixo dos quais o campo WebGL não é oferecido. Não é
# capricho: num aparelho assim o shader não roda a 60fps e o resultado é uma
# animação travada, que lê como site quebrado — pior que fundo liso.
MIN_RAM_GB = 4
MIN_NUCLEOS = 4


def portao(*, cena: bool = False, campo: bool = False) -> str:
    """O `<script>` inline que decide, no aparelho do visitante, o que baixar.

    INLINE de propósito: são ~700 bytes. Um arquivo externo custaria um round-trip
    só pra descobrir que não vai baixar nada — o portão ficaria mais caro que a
    decisão que ele toma.

    Devolve "" se a página não usa nenhuma das duas. Página sem cena e sem campo
    não carrega nem o portão.
    """
    if not (cena or campo):
        return ""

    pedidos = []
    if cena:
        pedidos.append(
            f"if(q('[data-cena]'))imp('{BASE}/cena-{VERSAO}.js');")
    if campo:
        # `gl()` testa WebGL com o MESMO `failIfMajorPerformanceCaveat` que o campo.js
        # usa. Sem esta checagem aqui, aparelho sem GPU baixava os 119 KB e o
        # renderizador recusava logo depois — 119 KB de download 100% desperdiçado,
        # e justamente em quem menos pode pagar. Testar custa ~90 bytes.
        pedidos.append(
            f"if(q('[data-campo]')&&(n.deviceMemory||8)>={MIN_RAM_GB}"
            f"&&(n.hardwareConcurrency||8)>={MIN_NUCLEOS}&&gl())imp('{BASE}/campo-{VERSAO}.js');")

    return (
        "<script>(function(){var n=navigator,c=n.connection||{};"
        # quem pediu menos movimento não recebe MAIS movimento
        "if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;"
        # dado caro ou rede ruim: a stack inteira é supérflua diante de carregar a página
        "if(c.saveData||/(^|-)2g$/.test(c.effectiveType||''))return;"
        "var q=function(s){return document.querySelector(s)},"
        "gl=function(){try{var e=document.createElement('canvas'),"
        "o={failIfMajorPerformanceCaveat:true};"
        "return!!(e.getContext('webgl2',o)||e.getContext('webgl',o))}catch(x){return false}},"
        # falha no import é silenciosa: o CSS já entregou a página, o refino não veio
        "imp=function(u){import(u).then(function(m){m.ligar&&m.ligar()}).catch(function(){})};"
        "addEventListener('load',function(){"
        # idle: espera o navegador terminar o que importa antes de gastar CPU/rede
        "(window.requestIdleCallback||function(f){setTimeout(f,200)})(function(){"
        + "".join(pedidos) +
        "})})})();</script>"
    )


def css_cena() -> str:
    """Layout sobreposto dos passos — só sob `.cena-ativa`, classe que o cena.js
    adiciona DEPOIS de ligar.

    A dependência da classe é a coisa toda: numa cena os passos ocupam o mesmo
    lugar e se revezam, mas isso só faz sentido se houver quem os revele. Escrever
    `position:absolute` solto no CSS empilharia os quatro passos por cima uns dos
    outros pra quem está sem JS — texto sobre texto, ilegível. Sem a classe, o
    grid normal continua valendo e o visitante lê tudo em sequência.
    """
    return (
        "<style>"
        ".cena-ativa .grid{position:relative;display:block;min-height:58svh}"
        ".cena-ativa .passo{position:absolute;inset:0;margin:auto;height:max-content;"
        "max-width:42rem;will-change:transform,opacity}"
        "</style>"
    )


def peso(*, cena: bool = False, campo: bool = False) -> dict:
    """Custo declarado desta página, pro auditor e pro painel. Números medidos no
    build (gzip), não estimados."""
    kb = (44.1 if cena else 0) + (119.0 if campo else 0)
    return {
        "portao_bytes": len(portao(cena=cena, campo=campo).encode()),
        "cena_kb_gzip": 44.1 if cena else 0,
        "campo_kb_gzip": 119.0 if campo else 0,
        "total_kb_gzip": round(kb, 1),
        "bloqueia_lcp": False,  # carrega no load+idle; nada disto é render-blocking
    }


if __name__ == "__main__":
    assert portao() == "", "página sem cena e sem campo não pode emitir nem o portão"

    so_cena = portao(cena=True)
    assert "cena-v1.js" in so_cena and "campo-v1.js" not in so_cena, \
        "quem só tem cena não pode baixar os 119 KB do Three"

    so_campo = portao(campo=True)
    assert "campo-v1.js" in so_campo and "cena-v1.js" not in so_campo

    ambos = portao(cena=True, campo=True)
    # as três travas que tornam o peso aceitável — se alguma sumir, o portão furou
    for trava in ("prefers-reduced-motion", "saveData", "deviceMemory",
                  "requestIdleCallback", "failIfMajorPerformanceCaveat"):
        assert trava in ambos, f"portão sem a trava '{trava}'"
    # a checagem de WebGL só faz sentido antes do download; se o `gl()` sumir do
    # ramo do campo, quem não tem GPU volta a baixar 119 KB pra nada
    assert "&&gl())imp" in ambos, "campo sem checagem de WebGL antes de baixar"
    assert "gl()" not in so_cena, "página sem campo não deve nem testar WebGL"
    assert "addEventListener('load'" in ambos, "carregar antes do load mataria o LCP"
    assert len(ambos.encode()) < 1024, f"portão inline grande demais: {len(ambos.encode())}B"

    p = peso(cena=True, campo=True)
    assert p["total_kb_gzip"] == 163.1 and p["bloqueia_lcp"] is False
    assert peso()["total_kb_gzip"] == 0

    print(f"stack_pesada OK — portão inline {len(ambos.encode())}B, "
          f"teto {p['total_kb_gzip']} KB gzip e só pra quem usa; "
          f"piso segue sendo o CSS de 1,7 KB")
