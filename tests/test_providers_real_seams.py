"""Providers reais (C1): seams honestos — sem chave, falha explícita; com chave mas
sem implementação, NotImplementedError explícito (nunca finge sucesso). Mesmo padrão
do motor-video pro LLMOrquestrador. O LocalDeploy é real e funciona hoje (sem API)."""
import pytest

from app.providers.llm_orquestrador import LLMOrquestrador
from app.providers.local_deploy import LocalDeploy


def test_llm_orquestrador_sem_chave_falha_explicito():
    o = LLMOrquestrador(api_key=None)
    with pytest.raises(RuntimeError, match="SITE_LLM_API_KEY"):
        o.analisar({"nicho": "clínica"})


def test_llm_orquestrador_com_chave_falha_notimplemented():
    o = LLMOrquestrador(api_key="fake-key")
    with pytest.raises(NotImplementedError):
        o.analisar({"nicho": "clínica"})


def test_local_deploy_escreve_arquivos_em_disco(tmp_path):
    from app.providers.base import SiteGerado

    site = SiteGerado(arquivos={"index.html": "<html>oi</html>"}, slug="teste-local")
    res = LocalDeploy(out_dir=str(tmp_path)).publicar(site)
    escrito = tmp_path / "teste-local" / "index.html"
    assert escrito.read_text() == "<html>oi</html>"
    assert res.url.endswith("teste-local/index.html")
