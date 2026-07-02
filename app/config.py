"""Seam de credencial única por estágio (mesmo padrão do motor-video): trocar de stub
pra provider real é 1 linha de config por estágio. Default: tudo stub (pipeline
testável hoje, zero chave)."""
from __future__ import annotations

import os

from .providers.base import DeployProvider, GeradorSiteProvider, OrquestradorProvider
from .providers.llm_orquestrador import LLMOrquestrador
from .providers.local_deploy import LocalDeploy
from .providers.stub import StubDeploy, StubGeradorSite, StubOrquestrador

_ORQUESTRADORES = {"stub": StubOrquestrador, "llm": LLMOrquestrador}
_GERADORES = {"stub": StubGeradorSite}
_DEPLOYS = {"stub": StubDeploy, "local": LocalDeploy}


def _resolver(registro: dict, env_var: str, default: str = "stub"):
    nome = os.environ.get(env_var, default)
    cls = registro.get(nome)
    if cls is None:
        raise ValueError(f"{env_var} desconhecido: {nome!r} (opções: {list(registro)})")
    return cls()


def orquestrador_ativo() -> OrquestradorProvider:
    return _resolver(_ORQUESTRADORES, "SITE_ORQUESTRADOR")


def gerador_ativo() -> GeradorSiteProvider:
    return _resolver(_GERADORES, "SITE_GERADOR")


def deploy_ativo() -> DeployProvider:
    return _resolver(_DEPLOYS, "SITE_DEPLOY")
