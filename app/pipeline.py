"""C1+C2: orquestração ponta a ponta — 'JP briefa, motor entrega'. Uma chamada só
(`montar_site`) percorre os 4 estágios (analisar → sintetizar → gerar → publicar);
nenhum passo manual entre eles (C2 — zero setup na mão)."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from .config import deploy_ativo, gerador_ativo, orquestrador_ativo
from .providers.base import BriefingSite, DeployResultado


@dataclass
class ResultadoMontagem:
    brief: BriefingSite
    deploy: DeployResultado


def _slug(nome: str) -> str:
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "site"


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
    slug = _slug(brief.nome_empresa)
    site = gerador.gerar(brief, slug)
    resultado = deploy.publicar(site)
    return ResultadoMontagem(brief=brief, deploy=resultado)
