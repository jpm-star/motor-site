from app.pipeline import montar_site, _slug


def test_slug_normaliza_acentos_e_espacos():
    assert _slug("Clínica Sorriso") == "clinica-sorriso"
    assert _slug("  A&B  Café!! ") == "a-b-cafe"


def test_montar_site_ponta_a_ponta_com_stub(monkeypatch):
    monkeypatch.delenv("SITE_ORQUESTRADOR", raising=False)
    monkeypatch.delenv("SITE_GERADOR", raising=False)
    monkeypatch.delenv("SITE_DEPLOY", raising=False)
    briefing = {"nome_empresa": "Clínica Sorriso", "nicho": "clínica odontológica",
                "whatsapp": "5511999998888"}
    resultado = montar_site(briefing)
    assert resultado.brief.nome_empresa == "Clínica Sorriso"
    assert resultado.deploy.provider == "stub"
    assert "clinica-sorriso" in resultado.deploy.url


def test_montar_site_e_idempotente_no_slug():
    briefing = {"nome_empresa": "Padaria Pão Quente", "nicho": "padaria"}
    r1 = montar_site(briefing)
    r2 = montar_site(briefing)
    assert r1.deploy.deploy_id == r2.deploy.deploy_id == "padaria-pao-quente"
