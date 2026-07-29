"""Tier 2 AEO/SEO — conteúdo para CITAÇÃO por IA, não blog.

Funções puras (dict entra, str/HTML sai). Zero dependência externa (stdlib só).

"negocio" é um dict: nome, nicho, cidade, uf, whatsapp, endereco, url,
servicos (list[str]), faq (list[{'q','a'}]).

Princípio AEO (Answer Engine Optimization): cada bloco é AUTOCONTIDO e LIDERA
com a resposta direta, para que uma IA que leia só aquele trecho já entenda —
sem depender do resto da página.
"""
from __future__ import annotations

import html


def _esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def secao_aeo(pergunta: str, resposta_direta: str, detalhes: list[str]) -> str:
    """<section> autocontida para citação: h2 = pergunta, 1º parágrafo = resposta
    direta, depois <ul> com os detalhes. A resposta vem ANTES dos detalhes."""
    itens = "".join(f"<li>{_esc(d)}</li>" for d in detalhes)
    ul = f"<ul>{itens}</ul>" if itens else ""
    return (
        f"<section class=\"aeo\">"
        f"<h2>{_esc(pergunta)}</h2>"
        f"<p>{_esc(resposta_direta)}</p>"
        f"{ul}"
        f"</section>"
    )


def faq_aeo(negocio: dict) -> str:
    """Renderiza o FAQ do negócio como seções AEO — uma section por pergunta."""
    faq = negocio.get("faq") or []
    return "".join(secao_aeo(item["q"], item["a"], []) for item in faq)


def resumo_negocio(negocio: dict) -> str:
    """Section-âncora: 'Quem é <nome>?' respondida em uma frase citável, com os
    dados de contato/serviços como detalhes."""
    nome = negocio.get("nome", "")
    nicho = negocio.get("nicho", "")
    cidade = negocio.get("cidade", "")
    uf = negocio.get("uf", "")
    local = ", ".join(p for p in (cidade, uf) if p)
    resposta = f"{nome} é {nicho}" + (f" em {local}." if local else ".")
    detalhes: list[str] = []
    if negocio.get("endereco"):
        detalhes.append(f"Endereço: {negocio['endereco']}")
    if negocio.get("whatsapp"):
        detalhes.append(f"WhatsApp: {negocio['whatsapp']}")
    if negocio.get("url"):
        detalhes.append(f"Site: {negocio['url']}")
    for s in negocio.get("servicos") or []:
        detalhes.append(f"Serviço: {s}")
    return secao_aeo(f"Quem é {nome}?", resposta, detalhes)


if __name__ == "__main__":
    # section autocontida: resposta antes dos detalhes, section fechada, pergunta no h2
    s = secao_aeo(
        "Quanto custa trocar a tela?",
        "A troca de tela custa a partir de R$150 e fica pronta no mesmo dia.",
        ["Garantia de 90 dias", "Orçamento sem compromisso"],
    )
    assert s.startswith("<section")
    assert s.endswith("</section>")
    assert "<h2>Quanto custa trocar a tela?</h2>" in s
    i_resp = s.index("A troca de tela custa")
    i_det = s.index("Garantia de 90 dias")
    assert i_resp < i_det, "resposta direta deve vir ANTES dos detalhes"
    assert s.index("<p>") < s.index("<ul>"), "parágrafo antes da lista"

    # escaping de HTML (segurança / não quebrar markup)
    x = secao_aeo("A & B <script>?", "resposta <b>", ["<li>x"])
    assert "<script>" not in x and "&lt;script&gt;" in x
    assert "&amp;" in x

    # sem detalhes → sem <ul>
    vazia = secao_aeo("P?", "R.", [])
    assert "<ul>" not in vazia and vazia.endswith("</section>")

    neg = {
        "nome": "Tech Fix",
        "nicho": "assistência técnica de celulares",
        "cidade": "Sorocaba",
        "uf": "SP",
        "whatsapp": "15999990000",
        "endereco": "Rua A, 100",
        "url": "https://techfix.example",
        "servicos": ["Troca de tela", "Troca de bateria"],
        "faq": [{"q": "Fazem a domicílio?", "a": "Sim, atendemos a domicílio."}],
    }
    r = resumo_negocio(neg)
    assert "<h2>Quem é Tech Fix?</h2>" in r
    assert "Tech Fix é assistência técnica de celulares em Sorocaba, SP." in r
    assert "WhatsApp: 15999990000" in r
    assert "Serviço: Troca de tela" in r

    f = faq_aeo(neg)
    assert "<h2>Fazem a domicílio?</h2>" in f
    assert "Sim, atendemos a domicílio." in f
    assert faq_aeo({}) == ""

    print("aeo_content.py OK")
