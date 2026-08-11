"""Escreve as páginas irmãs do T2 com LLM, sob trava.

SEPARAÇÃO QUE A ARQUITETURA JÁ PEDIA: quem fala com LLM é o orquestrador; o
gerador só monta HTML. Este módulo fica do lado do orquestrador — devolve o
`brief.paginas` que `multipagina.py` consome.

O RISCO AQUI NÃO É O HTML, É O TEXTO. Página multi-seção dá ao modelo espaço pra
encher linguiça: prazo que ninguém combinou, "mais de 200 clientes", "líder na
região". Num site de cliente isso vira processo, e no gabarito vira uma promessa
que a JPOS não cumpre na call seguinte. Por isso toda saída passa por `validar()`
antes de virar página — e página reprovada não vai pro ar, some.

Sem ANTHROPIC_API_KEY: devolve [] e o site sai de uma página só. Degradar pra T1
é aceitável; publicar T2 com texto inventado, não.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

_URL = "https://api.anthropic.com/v1/messages"
_MODELO = os.environ.get("T2_MODELO", "claude-sonnet-4-5-20250929")

# Números e prazos são a mentira mais fácil de escrever e a mais cara de sustentar:
# o prospect cobra na call, e quem responde é o JP, não o modelo.
_INVENCAO = re.compile(
    r"\b(\d+\s*(%|por cento|clientes?|empresas?|anos?|meses|dias|horas|mil))"
    r"|\b(l[íi]der|n[ºo°]\s*1|melhor da regi[ãa]o|premiad|certificad|garantia de)\w*",
    re.I)
_VAZIO = re.compile(
    r"\b(solu[çc][ãa]o completa|inovador|revolucion|potencializ|alavanc|"
    r"excel[êe]ncia|sinergia|disrupti|de ponta|state of the art)\w*", re.I)

_PROMPT = """Escreva as páginas internas do site de {nome} ({nicho}).

O site é TIER 2: multi-página com SEO técnico. Cada página precisa se sustentar
SOZINHA — alguém que caia nela pelo Google tem que entender o negócio sem passar
pela home, e uma IA que leia só o primeiro parágrafo já tem a resposta.

QUEM LÊ: {publico}

FONTE ÚNICA DE VERDADE (não afirme NADA que não esteja aqui):
{fatos}

PROIBIDO — inventar isto é o que transforma site em processo:
- número, porcentagem, quantidade de clientes, tempo de mercado
- prazo de entrega, SLA, garantia
- "líder", "melhor da região", prêmio, certificação
- palavra vazia: "solução completa", "inovador", "excelência", "de ponta"

TOM: direto, concreto, frase curta. Fala do problema de quem lê, não de si.
Não comece parágrafo com "Nossa", "Nosso" ou "Nós".

PÁGINAS A ESCREVER ({quantas}):
{lista}

Para cada uma:
- "intro": 40-60 palavras. É a RESPOSTA DIRETA — o que é e pra quem, sem rodeio.
- "blocos": 3 blocos {{titulo, texto}}. Texto de 45-70 palavras cada, concreto.
- "lista": 3 a 5 itens curtos, do que está incluído ou de como funciona.

Cada página precisa passar de 120 palavras no total. Responda JSON puro:
{{"paginas": [{{"slug","titulo","descricao","h1","intro","blocos":[{{"titulo","texto"}}],"lista":[],"tipo"}}]}}

"titulo" = <title> da busca, até 60 caracteres, termina com " | {nome}".
"descricao" = meta description, 110-155 caracteres, sem repetir o título.
"tipo" = "Service" nas páginas de serviço, "WebPage" nas outras."""


def _paginas_pedidas(cart: dict) -> list[tuple[str, str, str]]:
    """(slug, h1, instrução). Uma por serviço + as três institucionais.

    A escolha não é estética: página de serviço é a que responde busca comercial
    ("quem faz X em Y"), e as institucionais são as que uma IA cita quando
    perguntam "essa empresa é séria?".
    """
    escopo = [str(x).strip() for x in (cart.get("escopo") or []) if str(x).strip()]
    pedidas = []
    for item in escopo[:4]:
        curto = item.split(":")[0].split("(")[0].strip()[:44]
        pedidas.append((None, curto,
                        f'página de SERVIÇO sobre "{item}" — o que resolve, como '
                        f"funciona na prática, e o que a pessoa recebe"))
    pedidas += [
        (None, "Como trabalhamos",
         "página institucional: como é trabalhar com a empresa, do primeiro "
         "contato à entrega. Sem prazo inventado — descreva as ETAPAS."),
        (None, "Perguntas frequentes",
         "página de PERGUNTAS: cada bloco é uma dúvida real de quem vai contratar, "
         "com a resposta direta na primeira frase"),
    ]
    return pedidas


def validar(paginas: list[dict]) -> list[str]:
    """Problemas que impedem a página de ir pro ar. Roda sempre, inclusive no teste."""
    erros = []
    vistos = set()
    for i, p in enumerate(paginas):
        marca = p.get("slug") or p.get("h1") or f"#{i}"
        texto = " ".join([str(p.get("intro", "")),
                          *(str(b.get("texto", "")) for b in p.get("blocos") or []),
                          *(str(x) for x in p.get("lista") or [])])
        if len(texto.split()) < 120:
            erros.append(f"{marca}: {len(texto.split())} palavras (mín 120)")
        if m := _INVENCAO.search(texto):
            erros.append(f"{marca}: dado inventado — '{m.group(0)}'")
        if m := _VAZIO.search(texto):
            erros.append(f"{marca}: palavra vazia — '{m.group(0)}'")
        d = str(p.get("descricao", ""))
        if not (60 <= len(d) <= 165):
            erros.append(f"{marca}: description com {len(d)} caracteres (60-165)")
        t = str(p.get("titulo", ""))
        if len(t) > 70:
            erros.append(f"{marca}: title com {len(t)} caracteres (máx 70)")
        if t in vistos:
            erros.append(f"{marca}: title repetido — páginas competem entre si na busca")
        vistos.add(t)
    return erros


def escrever(cart: dict, *, chave: str | None = None) -> tuple[list[dict], list[str]]:
    """(paginas, erros). Lista vazia = o site sai de uma página só, sem drama."""
    chave = chave or os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not chave:
        return [], ["sem ANTHROPIC_API_KEY — T2 degrada pra página única"]

    pedidas = _paginas_pedidas(cart)
    fatos = json.dumps({k: cart.get(k) for k in
                        ("escopo", "diferenciais", "prova_social", "catalogo",
                         "regioes_atendidas", "criterio_qualificado")},
                       ensure_ascii=False, indent=1)[:3000]
    prompt = _PROMPT.format(
        nome=cart.get("nome_empresa", ""), nicho=cart.get("vertical", ""),
        publico=cart.get("criterio_qualificado", "dono de negócio local"),
        fatos=fatos, quantas=len(pedidas),
        lista="\n".join(f'{i+1}. h1 "{h1}" — {inst}' for i, (_, h1, inst) in enumerate(pedidas)))

    req = urllib.request.Request(
        _URL,
        data=json.dumps({"model": _MODELO, "max_tokens": 8000,
                         "messages": [{"role": "user", "content": prompt}]}).encode(),
        headers={"x-api-key": chave, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            txt = json.loads(r.read().decode())["content"][0]["text"].strip()
    except Exception as e:  # noqa: BLE001 — falha de rede não pode derrubar a geração
        return [], [f"LLM indisponível ({type(e).__name__}) — T2 degrada pra página única"]

    if txt.startswith("```"):
        txt = txt.split("```")[1].removeprefix("json").strip()
    try:
        paginas = json.loads(txt).get("paginas") or []
    except ValueError as e:
        return [], [f"resposta do LLM não é JSON ({e})"]

    erros = validar(paginas)
    if erros:
        # tudo ou nada: meia dúzia de páginas boas com uma inventando número
        # contamina o site inteiro, e a inventada é justamente a que o prospect lê
        return [], erros
    return paginas, []


if __name__ == "__main__":
    # a validação é a peça que precisa de teste — a chamada de rede não.
    ok = [{"slug": "x", "titulo": "Atendimento com IA | X", "descricao": "d" * 100,
           "intro": "palavra " * 60,
           "blocos": [{"titulo": "t", "texto": "palavra " * 60}], "lista": ["a"]}]
    assert validar(ok) == [], validar(ok)

    magra = [dict(ok[0], intro="curto", blocos=[], lista=[])]
    assert any("palavras" in e for e in validar(magra))

    inventado = [dict(ok[0], intro="Atendemos mais de 200 clientes por mês " * 12)]
    assert any("inventado" in e for e in validar(inventado)), validar(inventado)

    prazo = [dict(ok[0], intro="Entrega em 5 dias garantida sempre " * 12)]
    assert any("inventado" in e for e in validar(prazo)), validar(prazo)

    vazio = [dict(ok[0], intro="Uma solução completa e inovadora aqui " * 12)]
    assert any("vazia" in e for e in validar(vazio)), validar(vazio)

    repetido = [ok[0], dict(ok[0], slug="y")]
    assert any("repetido" in e for e in validar(repetido))

    curta_desc = [dict(ok[0], descricao="curta")]
    assert any("description" in e for e in validar(curta_desc))

    # sem chave: degrada, não explode
    ps, errs = escrever({"nome_empresa": "X"}, chave="")
    assert ps == [] and errs and "degrada" in errs[0]

    pedidas = _paginas_pedidas({"escopo": ["Serviço A", "Serviço B"]})
    assert len(pedidas) == 4, pedidas   # 2 serviços + 2 institucionais

    print("conteudo_t2 OK — validação barra página magra, número inventado, prazo, "
          "palavra vazia, title repetido e description fora de faixa")
