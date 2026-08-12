"""Seam de credencial única por estágio (mesmo padrão do motor-video): trocar de stub
pra provider real é 1 linha de config por estágio. Default: tudo stub (pipeline
testável hoje, zero chave)."""
from __future__ import annotations

import logging
import os

from .providers.base import DeployProvider, GeradorSiteProvider, OrquestradorProvider
from .providers.llm_orquestrador import LLMOrquestrador
from .providers.local_deploy import LocalDeploy
from .providers.stub import StubDeploy, StubGeradorSite, StubOrquestrador
from .providers.template_real import GeradorTemplate

_log = logging.getLogger("motor.config")

_ORQUESTRADORES = {"stub": StubOrquestrador, "llm": LLMOrquestrador}
_GERADORES = {"stub": StubGeradorSite, "template": GeradorTemplate}
_DEPLOYS = {"stub": StubDeploy, "local": LocalDeploy}


def _resolver(registro: dict, env_var: str, default: str = "stub"):
    nome = os.environ.get(env_var, default)
    cls = registro.get(nome)
    if cls is None:
        raise ValueError(f"{env_var} desconhecido: {nome!r} (opções: {list(registro)})")
    return cls()


def _tem_chave_llm() -> bool:
    """Alguma credencial que o LLMOrquestrador saiba usar."""
    if any(os.environ.get(v, "").strip()
           for v in ("GROQ_API_KEY", "SITE_LLM_API_KEY", "ANTHROPIC_API_KEY",
                     "LITELLM_MASTER_KEY")):
        return True
    # o provider também lê a chave de um .env fora do repo — mesma fonte dele
    try:
        from .providers.llm_orquestrador import _chave
        return bool(_chave())
    except Exception:  # noqa: BLE001 — descobrir credencial nunca pode derrubar a geração
        return False


def orquestrador_ativo() -> OrquestradorProvider:
    """COM chave de LLM, o default é `llm`. Sem chave, stub — mas gritando.

    O default era `stub` para todo mundo, e stub escreve copy de placeholder
    ("Ótica Visão Lins — referência em ótica", "resultado que fala por si"). Quem
    gerasse um site sem lembrar de exportar SITE_ORQUESTRADOR=llm entregava esse
    texto ao cliente sem nenhum aviso. É a raiz registrada do "Tier 1 inferior",
    e o modo de falha é o pior possível: silencioso e plausível — o site fica
    bonito, só a copy é genérica, e ninguém percebe até o cliente ler.

    Continua sobrescritível por env (os testes dependem do stub), mas agora stub
    em produção é escolha explícita, não esquecimento.
    """
    escolhido = os.environ.get("SITE_ORQUESTRADOR", "").strip()
    if not escolhido:
        escolhido = "llm" if _tem_chave_llm() else "stub"
        if escolhido == "stub":
            _log.warning(
                "SITE_ORQUESTRADOR não definido e NENHUMA chave de LLM encontrada: "
                "a copy vai sair de PLACEHOLDER, não de IA. Se este site vai pra "
                "cliente, defina a chave antes de publicar.")
    cls = _ORQUESTRADORES.get(escolhido)
    if cls is None:
        raise ValueError(f"SITE_ORQUESTRADOR desconhecido: {escolhido!r} "
                         f"(opções: {list(_ORQUESTRADORES)})")
    return cls()


def gerador_ativo() -> GeradorSiteProvider:
    # o gerador default segue `template`: o stub existe pro teste de seam, e um
    # site de stub não é "menos bonito", é vazio — ninguém publica sem notar
    return _resolver(_GERADORES, "SITE_GERADOR", default="template")


def deploy_ativo() -> DeployProvider:
    return _resolver(_DEPLOYS, "SITE_DEPLOY")
