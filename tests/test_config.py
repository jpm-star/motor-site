import pytest

from app.config import deploy_ativo, gerador_ativo, orquestrador_ativo
from app.providers.llm_orquestrador import LLMOrquestrador
from app.providers.local_deploy import LocalDeploy
from app.providers.stub import StubDeploy, StubGeradorSite, StubOrquestrador


def test_default_e_stub_em_todos_os_estagios(monkeypatch):
    monkeypatch.delenv("SITE_ORQUESTRADOR", raising=False)
    monkeypatch.delenv("SITE_GERADOR", raising=False)
    monkeypatch.delenv("SITE_DEPLOY", raising=False)
    assert isinstance(orquestrador_ativo(), StubOrquestrador)
    assert isinstance(gerador_ativo(), StubGeradorSite)
    assert isinstance(deploy_ativo(), StubDeploy)


def test_troca_de_provider_e_1_linha_de_config(monkeypatch):
    monkeypatch.setenv("SITE_ORQUESTRADOR", "llm")
    monkeypatch.setenv("SITE_DEPLOY", "local")
    assert isinstance(orquestrador_ativo(), LLMOrquestrador)
    assert isinstance(deploy_ativo(), LocalDeploy)


def test_provider_desconhecido_falha_explicito(monkeypatch):
    monkeypatch.setenv("SITE_DEPLOY", "netlify-ainda-nao-existe")
    with pytest.raises(ValueError, match="SITE_DEPLOY"):
        deploy_ativo()
