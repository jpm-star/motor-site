"""C1+C2: orquestração ponta a ponta — 'JP briefa, motor entrega'. Uma chamada só
(`montar_site`) percorre os 4 estágios (analisar → sintetizar → gerar → publicar);
nenhum passo manual entre eles (C2 — zero setup na mão)."""
from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from .config import deploy_ativo, gerador_ativo, orquestrador_ativo
from .providers.base import BriefingSite, DeployResultado

_log = logging.getLogger("motor.pipeline")


@dataclass
class ResultadoMontagem:
    brief: BriefingSite
    deploy: DeployResultado


def _slug(nome: str) -> str:
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "site"


def paginas_t2(briefing: dict[str, Any]) -> tuple[list[dict], list[str]]:
    """Páginas irmãs quando o tier pede. ([], []) em T1 — o caminho de sempre.

    O tier vem do briefing porque é o painel quem sabe o que foi VENDIDO; o motor
    não adivinha por tamanho de escopo. Tier ausente = T1, que é o default seguro:
    entregar menos do que foi pago aparece na hora, entregar mais some no custo.
    """
    tier = str(briefing.get("tier") or "").strip().upper()
    if tier not in ("T2", "T3", "T4"):
        return [], []
    from . import conteudo_t2
    # `escopo` é o que vira página de SERVIÇO. O painel manda os serviços em
    # `escopo`/`catalogo`; sem nenhum dos dois, os diferenciais são a melhor fonte
    # real que existe — melhor que o modelo inventar quais serviços a empresa presta.
    escopo = (briefing.get("escopo") or briefing.get("catalogo")
              or briefing.get("diferenciais") or [])
    cart = {
        "nome_empresa": briefing.get("nome_empresa", ""),
        "vertical": briefing.get("nicho", ""),
        "escopo": [str(x) for x in escopo if str(x).strip()],
        "diferenciais": briefing.get("diferenciais") or [],
        "prova_social": briefing.get("prova_social") or [],
        "catalogo": briefing.get("catalogo") or [],
        "regioes_atendidas": [briefing["cidade"]] if briefing.get("cidade") else [],
        "criterio_qualificado": briefing.get("publico", ""),
    }
    return conteudo_t2.escrever(cart)


def montar_site(briefing: dict[str, Any]) -> ResultadoMontagem:
    """`briefing` = o form que o JP preenche (nome_empresa, nicho, diferenciais,
    público, whatsapp, ...). Levanta exceção em qualquer estágio — sem fallback
    silencioso: falha aqui vira `BLOQUEADA` na fila do JP, não site incompleto no ar."""
    orquestrador = orquestrador_ativo()
    gerador = gerador_ativo()
    deploy = deploy_ativo()

    angulos = orquestrador.analisar(briefing)
    brief = orquestrador.sintetizar(briefing, angulos)
    # ÚLTIMA TRAVA antes de virar HTML: o modelo inventa prazo/superlativo que o
    # dono nunca declarou ("prontos em 1 hora" a partir de "conserto na hora").
    # As páginas T2 já eram validadas; a home — que é o que o dono lê primeiro —
    # não era. Ver app/copy_honesta.py.
    from . import copy_honesta
    brief, _ = copy_honesta.sanear(brief, briefing)

    # === T2: as páginas irmãs. ============================================
    # ISTO ESTAVA DESLIGADO. `conteudo_t2` e `multipagina` existiam, passavam nos
    # próprios testes, e não se conheciam: `brief.paginas` nunca era escrito, então
    # `multipagina.paginas_de()` recebia [] e TODO site saía de página única — T2
    # vendido, T1 entregue, sem nada quebrar na tela. Duas metades corretas que
    # ninguém tinha conectado; teste de unidade não pega fronteira.
    brief.paginas, _erros_t2 = paginas_t2(briefing)
    if _erros_t2:
        # degradar é aceitável (T1 honesto > T2 inventado), ficar CALADO não é: quem
        # gerou precisa saber que vendeu multi-página e publicou uma só.
        _log.warning("T2 degradou pra página única: %s", "; ".join(_erros_t2[:3]))

    slug = _slug(brief.nome_empresa)
    site = gerador.gerar(brief, slug)
    resultado = deploy.publicar(site)
    return ResultadoMontagem(brief=brief, deploy=resultado)
