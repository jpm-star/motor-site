"""Tier 2 — site MULTI-PÁGINA a partir da home já montada.

POR QUE ISTO EXISTE: a apostila vende T2 como "site multi-página + SEO técnico +
AEO + GEO" por R$1.000 + R$397/mês, e o gerador entregava UMA página com ~420
palavras. Era a mesma classe de risco do Google Calendar antes de ser construído:
promessa ativa em toda call, sem produto atrás.

O MOLDE É A PRÓPRIA HOME. Nada de segundo template: a home já vem com head, CSS,
nav, footer, WhatsApp fixo e a camada de motion. Aqui só se troca o que muda de
página pra página — title, description, canonical, JSON-LD e o miolo, delimitado
no template por <!--#miolo-inicio--> / <!--#miolo-fim-->. Um segundo template
divergiria do primeiro na terceira mudança de design, e aí metade do site fica
com a cara velha.

CONTEÚDO FINO É PIOR QUE UMA PÁGINA SÓ. Seis páginas rasas repetindo as mesmas
420 palavras não é T2 — é a mesma página fatiada, e o Google trata como conteúdo
duplicado/thin. Por isso `paginas_de` RECUSA página sem corpo suficiente
(MIN_PALAVRAS): melhor entregar 3 páginas densas que 7 vazias.

QUEM ESCREVE O TEXTO: o orquestrador (LLM), não este módulo. Aqui é HTML puro,
função pura, stdlib só — igual ao resto de app/seo/.
"""
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field

# Abaixo disto a página não se sustenta sozinha: não responde a uma busca nem dá
# a uma IA o que citar. O número não é arbitrário — é a faixa em que uma página
# deixa de parecer índice e passa a parecer resposta.
MIN_PALAVRAS = 120

_INICIO = "<!--#miolo-inicio-->"
_FIM = "<!--#miolo-fim-->"


def _e(s: object) -> str:
    return html.escape(str(s), quote=True)


def _slug(texto: str) -> str:
    t = re.sub(r"[^a-z0-9]+", "-", str(texto).lower().strip())
    for de, para in (("ç", "c"), ("ã", "a"), ("á", "a"), ("é", "e"), ("í", "i"),
                     ("ó", "o"), ("ú", "u"), ("â", "a"), ("ê", "e"), ("ô", "o")):
        t = t.replace(de, para)
    return re.sub(r"^-|-$", "", re.sub(r"-{2,}", "-", t))[:60]


@dataclass
class Pagina:
    """Uma página irmã da home. `blocos` são pares (subtítulo, parágrafo)."""
    slug: str
    titulo: str          # <title> — o que aparece no resultado de busca
    descricao: str       # meta description
    h1: str
    intro: str           # PRIMEIRO parágrafo: a resposta direta (princípio AEO)
    blocos: list[tuple[str, str]] = field(default_factory=list)
    lista: list[str] = field(default_factory=list)
    tipo: str = "WebPage"   # ou "Service" — muda o JSON-LD

    @property
    def url(self) -> str:
        return f"/{self.slug}/"

    def palavras(self) -> int:
        txt = " ".join([self.intro, *(t for par in self.blocos for t in par),
                        *self.lista])
        return len(txt.split())


def _miolo(p: Pagina, link_zap: str, cta: str, nome: str) -> str:
    """O corpo da página. Estrutura AEO: h1, resposta direta, depois detalhes.

    Uma IA que leia só o primeiro parágrafo precisa já ter a resposta — é isso
    que faz o trecho ser citável em vez de precisar da página inteira.
    """
    partes = [
        '<header class="hero hero-interna" id="topo">',
        f'  <h1 class="load load-2">{_e(p.h1)}</h1>',
        f'  <p class="load load-3">{_e(p.intro)}</p>',
        f'  <a class="btn btn-glow load load-4" href="{link_zap}">{_e(cta)}</a>',
        "</header>",
        "<main>",
    ]
    for sub, texto in p.blocos:
        partes.append(f'<section class="reveal"><h2>{_e(sub)}</h2><p>{_e(texto)}</p></section>')
    if p.lista:
        itens = "".join(f"<li>{_e(i)}</li>" for i in p.lista)
        partes.append(f'<section class="reveal"><ul class="lista-t2">{itens}</ul></section>')
    partes += [
        "</main>",
        '<section class="cta-final reveal" id="contato">',
        f"  <h2>Falar com a {_e(nome)}</h2>",
        f'  <a class="btn btn-glow" href="{link_zap}">{_e(cta)}</a>',
        "</section>",
    ]
    return "\n".join(partes)


def _json_ld(p: Pagina, base: str, nome: str) -> str:
    """Schema por PÁGINA. A home já emite LocalBusiness/Organization; repetir o
    mesmo bloco em toda página dilui o sinal em vez de reforçar — cada página
    descreve a si mesma e aponta pra home como publisher."""
    if not base:
        return ""
    d = {
        "@context": "https://schema.org",
        "@type": p.tipo,
        "name": p.titulo,
        "description": p.descricao,
        "url": f"{base}{p.url}",
        "isPartOf": {"@type": "WebSite", "name": nome, "url": f"{base}/"},
    }
    if p.tipo == "Service":
        d["provider"] = {"@type": "LocalBusiness", "name": nome, "url": f"{base}/"}
    return f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>'


def _troca_head(doc: str, p: Pagina, base: str, nome: str) -> str:
    """title, description, canonical e og — o que um crawler lê antes do corpo.

    Página interna herdando o <title> da home é o erro clássico de multi-página:
    seis resultados idênticos na busca, e o Google escolhe um só."""
    doc = re.sub(r"<title>.*?</title>", f"<title>{_e(p.titulo)}</title>", doc, count=1, flags=re.S)
    doc = re.sub(r'<meta name="description" content="[^"]*">',
                 f'<meta name="description" content="{_e(p.descricao)}">', doc, count=1)
    if base:
        alvo = f'<link rel="canonical" href="{base}{p.url}">'
        doc = (re.sub(r'<link rel="canonical"[^>]*>', alvo, doc, count=1)
               if 'rel="canonical"' in doc else doc.replace("</head>", f"{alvo}\n</head>", 1))
    doc = re.sub(r'<meta property="og:title" content="[^"]*">',
                 f'<meta property="og:title" content="{_e(p.titulo)}">', doc, count=1)
    doc = re.sub(r'<meta property="og:description" content="[^"]*">',
                 f'<meta property="og:description" content="{_e(p.descricao)}">', doc, count=1)
    return doc.replace("</head>", f"{_json_ld(p, base, nome)}\n</head>", 1)


def _nav_com_links(doc: str, paginas: list[Pagina], home: bool) -> str:
    """Links de navegação reais. Sem eles as páginas existem no sitemap e não são
    alcançáveis por clique — órfãs pro crawler e invisíveis pro visitante, que é
    o pior dos dois mundos: custo de gerar sem nenhum dos benefícios."""
    if not paginas:
        return doc
    pre = "" if home else "../"
    # rótulo CURTO: o h1 inteiro ("Site que vende com IA por dentro") faz os 5 links
    # somarem 841px e espremerem marca e CTA na mesma barra. Corta na primeira
    # pontuação e limita — a página tem o título completo, a barra só precisa levar até ela.
    def rotulo(p: Pagina) -> str:
        r = re.split(r"[:—,(]", p.h1)[0].strip()
        return r if len(r) <= 18 else r[:17].rstrip() + "…"

    itens = "".join(f'<a href="{pre}{p.slug}/">{_e(rotulo(p))}</a>' for p in paginas)
    if not home:
        itens = f'<a href="{pre}">Início</a>{itens}'
    return doc.replace('<nav class="nav">',
                       f'<nav class="nav tem-links">\n  <span class="nav-links">{itens}</span>', 1)


def _links_no_rodape(doc: str, paginas: list[Pagina], home: bool) -> str:
    """Mapa do site no rodapé — em TODA largura de tela.

    A barra superior esconde os links abaixo de 820px (não cabem junto de marca e
    CTA num celular), e celular é de onde vem a maior parte do tráfego. Sem isto,
    o visitante mobile não tem como chegar em nenhuma página interna, e o crawler
    depende só da home. Rodapé resolve os dois sem uma linha de JS — nada de menu
    hamburger, que exigiria script e mais um estado pra dar errado.
    """
    if not paginas or "<footer>" not in doc:
        return doc
    pre = "" if home else "../"
    itens = "".join(f'<a href="{pre}{p.slug}/">{_e(p.h1)}</a>' for p in paginas)
    if not home:
        itens = f'<a href="{pre}">Início</a>{itens}'
    bloco = f'<nav class="rodape-mapa" aria-label="Páginas do site">{itens}</nav>'
    return doc.replace("<footer>", f"{bloco}\n<footer>", 1)


def _corrige_raizes(doc: str) -> str:
    """Página interna vive em /<slug>/, então caminho relativo do molde quebra.
    Só os assets do próprio site — /_lib é absoluto de propósito (compartilhado
    entre domínios) e link externo não se toca."""
    return doc.replace('href="#topo"', 'href="../#topo"')


CSS = """
/* A nav do template nasce com transform:translateY(-105%) e só desce quando o JS
   põe .on ao rolar — desenho pensado pra one-page, onde o hero já tem o CTA. Com
   páginas irmãs isso esconde a ÚNICA navegação do site: quem chega por uma
   interna vinda do Google não vê como sair dela. Tendo links, a barra fica. */
.nav.tem-links{transform:none;border-color:var(--linha)}
.hero-interna{min-height:auto;padding-block:clamp(3rem,8vw,5rem)}
.hero-interna h1{max-width:34ch}
.lista-t2{max-width:44rem;margin-inline:auto;line-height:1.9;padding-left:1.1rem}
.nav-links{display:none;gap:1.1rem;font-size:.86rem;font-weight:600}
.nav-links a{opacity:.75;text-decoration:none}
.nav-links a:hover{opacity:1}
@media(min-width:820px){.nav-links{display:flex}}
main section.reveal{max-width:44rem;margin-inline:auto;margin-bottom:2.2rem}
main section.reveal h2{font-size:clamp(1.2rem,2.6vw,1.55rem);margin-bottom:.6rem}
.rodape-mapa{display:flex;flex-wrap:wrap;justify-content:center;gap:.5rem 1.4rem;
  padding:2.4rem clamp(1rem,4vw,2.5rem) .6rem;font-size:.9rem}
.rodape-mapa a{opacity:.72;text-decoration:none;padding:.3rem 0}
.rodape-mapa a:hover{opacity:1;text-decoration:underline}
"""


def paginas_de(brief) -> list[Pagina]:
    """Lê `brief.paginas` (escrito pelo orquestrador) e devolve só as que se
    sustentam. Briefing sem o campo → lista vazia → o gerador se comporta
    exatamente como antes. É o que mantém T1 intocado."""
    cruas = list(getattr(brief, "paginas", None) or [])
    saida = []
    for d in cruas:
        if not isinstance(d, dict):
            continue
        h1 = str(d.get("h1") or d.get("titulo") or "").strip()
        if not h1:
            continue
        p = Pagina(
            slug=_slug(d.get("slug") or h1),
            titulo=str(d.get("titulo") or h1).strip()[:70],
            descricao=str(d.get("descricao") or "").strip()[:160],
            h1=h1,
            intro=str(d.get("intro") or "").strip(),
            blocos=[(str(b.get("titulo", "")), str(b.get("texto", "")))
                    for b in (d.get("blocos") or []) if isinstance(b, dict)],
            lista=[str(x) for x in (d.get("lista") or [])],
            tipo=str(d.get("tipo") or "WebPage"),
        )
        if p.slug and p.palavras() >= MIN_PALAVRAS:
            saida.append(p)
    return saida


def montar(doc_home: str, paginas: list[Pagina], *, base: str, nome: str,
           link_zap: str, cta: str) -> dict[str, str]:
    """{caminho → html} das páginas irmãs. `doc_home` é o molde já renderizado.

    Devolve {} se não houver marcador no molde — sem isso o resultado seria uma
    página irmã sem hero e sem rodapé, pior que não existir.
    """
    if not paginas or _INICIO not in doc_home or _FIM not in doc_home:
        return {}
    antes, resto = doc_home.split(_INICIO, 1)
    _, depois = resto.split(_FIM, 1)

    saida = {}
    for p in paginas:
        doc = antes + _miolo(p, link_zap, cta, nome) + depois
        doc = _troca_head(doc, p, base, nome)
        doc = _nav_com_links(doc, paginas, home=False)
        doc = _links_no_rodape(doc, paginas, home=False)
        doc = _corrige_raizes(doc)
        doc = doc.replace("</style>", CSS + "</style>", 1)
        saida[f"{p.slug}/index.html"] = doc
    return saida


def home_com_links(doc_home: str, paginas: list[Pagina]) -> str:
    """A home também precisa apontar pras irmãs — senão elas nascem órfãs."""
    doc = _nav_com_links(doc_home, paginas, home=True)
    doc = _links_no_rodape(doc, paginas, home=True)
    return doc.replace("</style>", CSS + "</style>", 1) if paginas else doc


def urls(paginas: list[Pagina], base: str) -> list[str]:
    return [f"{base}{p.url}" for p in paginas]


if __name__ == "__main__":
    MOLDE = ('<!doctype html><html><head><title>Home</title>'
             '<meta name="description" content="d"><meta property="og:title" content="o">'
             '<meta property="og:description" content="od"><style>a{}</style></head>'
             '<body><nav class="nav"><a href="#topo">M</a></nav>'
             '<!--#miolo-inicio--><header>miolo velho</header><!--#miolo-fim-->'
             '<footer>rodapé</footer></body></html>')

    class B:
        paginas = [
            {"h1": "Atendimento com IA", "titulo": "Atendimento com IA | X",
             "descricao": "desc", "intro": "resposta direta " * 30,
             "blocos": [{"titulo": "Como funciona", "texto": "detalhe " * 60},
                        {"titulo": "Pra quem serve", "texto": "publico " * 40}],
             "lista": ["um", "dois"], "tipo": "Service"},
            {"h1": "Página magra", "intro": "curta demais"},   # tem que ser recusada
        ]

    ps = paginas_de(B())
    assert len(ps) == 1, f"a magra devia ser recusada, vieram {len(ps)}"
    assert ps[0].slug == "atendimento-com-ia", ps[0].slug

    arq = montar(MOLDE, ps, base="https://x.com", nome="X",
                 link_zap="https://wa.me/1", cta="Falar")
    assert list(arq) == ["atendimento-com-ia/index.html"], list(arq)
    d = arq["atendimento-com-ia/index.html"]
    assert "miolo velho" not in d, "o miolo da home vazou pra página interna"
    assert "rodapé" in d and "<nav" in d, "página interna perdeu rodapé/nav do molde"
    assert "<title>Atendimento com IA | X</title>" in d, "title não trocou"
    assert 'canonical" href="https://x.com/atendimento-com-ia/"' in d
    assert '"@type": "Service"' in d and '"provider"' in d
    assert 'href="../#topo"' in d, "link raiz do molde ficaria quebrado na interna"

    # sem marcador no molde, não inventa página quebrada
    assert montar("<html>sem marcador</html>", ps, base="", nome="X",
                  link_zap="#", cta="c") == {}
    # briefing sem o campo = comportamento de T1, intocado
    assert paginas_de(object()) == []
    assert urls(ps, "https://x.com") == ["https://x.com/atendimento-com-ia/"]

    h = home_com_links(MOLDE, ps)
    assert 'href="atendimento-com-ia/"' in h, "home não aponta pra irmã (página órfã)"
    assert "rodape-mapa" in h and "rodape-mapa" in d, \
        "sem mapa no rodapé o visitante de celular não alcança página nenhuma"

    print(f"multipagina OK — molde reusado, page magra recusada (< {MIN_PALAVRAS} palavras), "
          f"title/canonical/JSON-LD por página, nav cruzada nos dois sentidos")
