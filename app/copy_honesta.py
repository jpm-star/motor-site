"""Trava anti-invenção da copy da HOME — a mesma que as páginas T2 já tinham.

POR QUE EXISTE: `conteudo_t2.validar` barrava dado inventado nas páginas internas,
mas a HOME não passava por nada. Num teste real com uma ótica de Lins, o briefing
dizia "conserto na hora" e o h1 saiu **"Óculos prontos em 1 hora"** — uma promessa
de prazo que o dono nunca fez.

Isso é pior que erro de layout. Numa venda porta-a-porta, o dono lê o h1 na frente
do vendedor: ou ele corrige na hora (e a demo perde credibilidade), ou ele aceita e
o negócio passa a dever um prazo que não pratica. Nas duas pontas, quem paga é a
relação.

A REGRA: número, prazo, garantia e superlativo só entram se estiverem no briefing.
Não se inventa "1 hora" a partir de "na hora", nem "40 anos" a partir de nada.
"""
from __future__ import annotations

import logging
import re

log = logging.getLogger("motor.copy_honesta")

# Números com unidade de compromisso: prazo, tempo de casa, volume, desconto.
# "R$ 50" fica de fora de propósito — preço vem do cartucho, não do modelo.
_INVENCAO = re.compile(
    r"\b\d+\s*(?:hora|horas|h\b|min\b|minuto|minutos|dia|dias|semana|semanas|"
    r"m[êe]s|meses|ano|anos|%|por cento|clientes?|empresas?|mil|x\b)"
    # superlativo sem lastro: "melhor"/"maior" isolados já são afirmação de
    # ranking que ninguém mediu. `melhor d[aeo]` deixava passar "a melhor ótica
    # da região", que é exatamente a frase que o dono teria que defender.
    r"|\b(?:l[íi]der\w*|n[ºo°]\s*1|melhor|maior|premiad\w*|"
    r"certificad\w*|garantido|garantia de|desde \d{4})",
    re.I)


def achados(texto: str, briefing: dict | None = None) -> list[str]:
    """Trechos que afirmam algo que o briefing não sustenta.

    Um achado é perdoado se aparecer LITERAL no briefing — se o dono escreveu
    "entrega em 3 dias", o site pode dizer "entrega em 3 dias".
    """
    fonte = ""
    if briefing:
        fonte = " ".join(str(v) for v in briefing.values() if isinstance(v, (str, int))) + " " + \
                " ".join(str(x) for v in briefing.values() if isinstance(v, list) for x in v)
    fonte = fonte.lower()
    saida = []
    for m in _INVENCAO.finditer(texto or ""):
        trecho = m.group(0)
        if trecho.lower() in fonte:
            continue          # o dono afirmou isso; repetir é honesto
        saida.append(trecho)
    return saida


def revisar(brief, briefing: dict) -> list[str]:
    """Varre os campos que o visitante lê primeiro. Devolve o que não se sustenta."""
    problemas = []
    for campo in ("headline", "subheadline", "cta_titulo"):
        texto = str(getattr(brief, campo, "") or "")
        for achado in achados(texto, briefing):
            problemas.append(f"{campo}: {achado!r}")
    for i, s in enumerate(getattr(brief, "secoes", None) or []):
        if not isinstance(s, dict):
            continue
        for achado in achados(f"{s.get('titulo','')} {s.get('corpo','')}", briefing):
            problemas.append(f"secao[{i}]: {achado!r}")
    return problemas


def sanear(brief, briefing: dict):
    """Última linha de defesa: troca a headline inventada por uma ANCORADA no briefing.

    Não tenta reescrever com IA (seria outra rodada de invenção, e no meio de uma
    demo porta-a-porta não há tempo). Monta a partir do que o dono declarou —
    menos vendedora, e verdadeira.
    """
    problemas = revisar(brief, briefing)
    if not problemas:
        return brief, []

    nome = str(briefing.get("nome_empresa") or "").strip()
    serv = str(briefing.get("servico_principal") or briefing.get("nicho") or "").strip()
    cidade = str(briefing.get("cidade") or "").strip()

    if any(p.startswith("headline") for p in problemas):
        brief.headline = (f"{serv.capitalize()} em {cidade}" if serv and cidade
                          else f"{serv.capitalize()}" if serv else nome)[:70]
    if any(p.startswith("subheadline") for p in problemas):
        difs = [str(d) for d in (briefing.get("diferenciais") or [])][:2]
        brief.subheadline = ("; ".join(difs) or f"Fale com a {nome} pelo WhatsApp.")[:130]
    # seções: some com a frase inventada em vez de reescrever o bloco inteiro
    for s in (getattr(brief, "secoes", None) or []):
        if isinstance(s, dict):
            for achado in achados(str(s.get("corpo", "")), briefing):
                s["corpo"] = re.sub(rf"[^.!?]*{re.escape(achado)}[^.!?]*[.!?]\s*", "",
                                    s["corpo"], flags=re.I).strip() or s["corpo"]
    log.warning("copy da home tinha %d afirmação(ões) sem lastro no briefing: %s",
                len(problemas), "; ".join(problemas[:4]))
    return brief, problemas


if __name__ == "__main__":
    b = {"nome_empresa": "Ótica Visão Lins", "nicho": "ótica", "cidade": "Lins",
         "servico_principal": "óculos de grau",
         "diferenciais": ["exame de vista no local", "conserto na hora"]}

    # o caso real que motivou o módulo
    assert achados("Óculos prontos em 1 hora", b) == ["1 hora"], achados("Óculos prontos em 1 hora", b)
    # "na hora" não vira "1 hora"
    assert achados("Conserto na hora", b) == []
    # o que o dono declarou pode ser repetido
    assert achados("entrega em 3 dias", {"escopo": ["entrega em 3 dias"]}) == []
    assert achados("Somos líderes do setor", b) == ["líderes"], achados("Somos líderes do setor", b)
    assert achados("Atendemos desde 1998", b) == ["desde 1998"]
    assert achados("Atendimento no mesmo dia", b) == [], "sem número não é invenção"

    class B:
        headline = "Óculos prontos em 1 hora"
        subheadline = "A melhor ótica da região"
        cta_titulo = ""
        secoes = [{"titulo": "Rapidez", "corpo": "Ficamos prontos em 30 minutos. Atendemos todo dia."}]

    novo, probs = sanear(B(), b)
    assert len(probs) >= 2, probs
    assert novo.headline == "Óculos de grau em Lins", novo.headline
    assert "1 hora" not in novo.headline and "melhor" not in novo.subheadline
    assert "30 minutos" not in novo.secoes[0]["corpo"], novo.secoes[0]["corpo"]

    class Limpo:
        headline = "Óculos de grau em Lins"
        subheadline = "Exame de vista no local"
        cta_titulo = ""
        secoes = []
    _, nada = sanear(Limpo(), b)
    assert nada == [], nada

    print("copy_honesta OK — pega prazo/tempo de casa/superlativo inventado, "
          "perdoa o que o briefing declara, e ancora a headline no dado real")
