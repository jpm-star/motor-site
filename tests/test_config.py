import pytest

from app.config import deploy_ativo, gerador_ativo, orquestrador_ativo
from app.providers.llm_orquestrador import LLMOrquestrador
from app.providers.local_deploy import LocalDeploy
from app.providers.stub import StubDeploy, StubGeradorSite, StubOrquestrador


def test_sem_chave_de_llm_cai_no_stub(monkeypatch):
    """Sem credencial nenhuma, stub — é o que mantém a suíte rodando sem chave."""
    for v in ("SITE_ORQUESTRADOR", "SITE_GERADOR", "SITE_DEPLOY",
              "GROQ_API_KEY", "SITE_LLM_API_KEY", "ANTHROPIC_API_KEY",
              "LITELLM_MASTER_KEY"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr("app.config._tem_chave_llm", lambda: False)
    assert isinstance(orquestrador_ativo(), StubOrquestrador)
    assert isinstance(deploy_ativo(), StubDeploy)


def test_com_chave_de_llm_o_default_deixa_de_ser_stub(monkeypatch):
    """A REGRESSÃO QUE ISTO IMPEDE: o default era stub pra todo mundo, e stub
    escreve placeholder ("referência em ótica", "resultado que fala por si").
    Quem gerasse um site sem lembrar de exportar SITE_ORQUESTRADOR=llm entregava
    esse texto ao cliente — silenciosamente, com o site parecendo pronto."""
    monkeypatch.delenv("SITE_ORQUESTRADOR", raising=False)
    monkeypatch.setattr("app.config._tem_chave_llm", lambda: True)
    assert isinstance(orquestrador_ativo(), LLMOrquestrador)


def test_gerador_default_e_o_template_real(monkeypatch):
    """Gerador stub produz site VAZIO — ninguém publica sem notar, mas também não
    há motivo pra ele ser o default de quem só quer gerar um site."""
    monkeypatch.delenv("SITE_GERADOR", raising=False)
    from app.providers.template_real import GeradorTemplate
    assert isinstance(gerador_ativo(), GeradorTemplate)


def test_troca_de_provider_e_1_linha_de_config(monkeypatch):
    monkeypatch.setenv("SITE_ORQUESTRADOR", "llm")
    monkeypatch.setenv("SITE_DEPLOY", "local")
    assert isinstance(orquestrador_ativo(), LLMOrquestrador)
    assert isinstance(deploy_ativo(), LocalDeploy)


def test_provider_desconhecido_falha_explicito(monkeypatch):
    monkeypatch.setenv("SITE_DEPLOY", "netlify-ainda-nao-existe")
    with pytest.raises(ValueError, match="SITE_DEPLOY"):
        deploy_ativo()
