"""Providers reais (C1): seams honestos. O LLMOrquestrador AGORA é real (Groq escreve
a copy por-cliente) — sem chave, falha explícita; com chave, escreve copy específica e
filtra corpo repetido (o defeito do stub). O LocalDeploy é real e funciona sem API."""
import pytest

from app.providers import llm_orquestrador as lo
from app.providers.llm_orquestrador import LLMOrquestrador
from app.providers.local_deploy import LocalDeploy


def test_llm_orquestrador_sem_chave_falha_explicito(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("SITE_LLM_API_KEY", raising=False)
    monkeypatch.setattr(lo, "_chave", lambda: "")   # ignora sdr-motor/.env da máquina
    o = LLMOrquestrador(api_key=None)
    with pytest.raises(RuntimeError, match="ausente"):
        o.sintetizar({"nicho": "clínica"}, o.analisar({"nicho": "clínica"}))


def test_llm_orquestrador_com_chave_escreve_copy_real(monkeypatch):
    # sem rede: injeta a resposta do Groq. Corpo duplicado deve ser filtrado.
    monkeypatch.setattr(lo, "_groq_json", lambda *a, **k: {
        "headline": "Granito instalado em 48h, sem quebra",
        "subheadline": "Medição, corte e instalação por uma equipe só.",
        "secoes": [{"titulo": "Prazo", "corpo": "Instala em até 48h após a medição."},
                   {"titulo": "Prazo", "corpo": "Instala em até 48h após a medição."},
                   {"titulo": "Garantia", "corpo": "12 meses contra trinca de fábrica."}],
        "cta_texto": "Pedir orçamento"})
    o = LLMOrquestrador(api_key="fake-key")
    b = o.sintetizar({"nome_empresa": "Marmoraria X", "nicho": "marmoraria",
                      "diferenciais": ["Prazo", "Garantia"], "whatsapp": "5514999"},
                     o.analisar({"nicho": "marmoraria"}))
    corpos = [s["corpo"] for s in b.secoes]
    assert len(corpos) == len(set(corpos)) == 2      # duplicata filtrada
    assert "referência em" not in b.headline.lower()  # sem clichê templado do stub
    assert b.subheadline and b.cta_contato == "5514999"


def test_local_deploy_escreve_arquivos_em_disco(tmp_path):
    from app.providers.base import SiteGerado

    site = SiteGerado(arquivos={"index.html": "<html>oi</html>"}, slug="teste-local")
    res = LocalDeploy(out_dir=str(tmp_path)).publicar(site)
    escrito = tmp_path / "teste-local" / "index.html"
    assert escrito.read_text() == "<html>oi</html>"
    assert res.url.endswith("teste-local/index.html")
