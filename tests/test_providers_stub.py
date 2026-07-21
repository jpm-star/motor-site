from app.providers.stub import StubDeploy, StubGeradorSite, StubOrquestrador

_BRIEFING = {"nome_empresa": "Clínica Sorriso", "nicho": "clínica odontológica", "whatsapp": "5511999998888"}


def test_analisar_produz_multiplos_angulos_deterministicos():
    o = StubOrquestrador()
    a1 = o.analisar(_BRIEFING)
    a2 = o.analisar(_BRIEFING)
    assert len(a1) >= 2
    assert [x.angulo for x in a1] == [x.angulo for x in a2]  # determinístico


def test_sintetizar_secoes_de_conteudo_real_nao_de_angulos():
    o = StubOrquestrador()
    angulos = o.analisar(_BRIEFING)
    brief = o.sintetizar(_BRIEFING, angulos)
    assert "Clínica Sorriso" in brief.headline
    # ângulos são meta-análise, NÃO viram seção (antes vazavam placeholder pro site)
    insights = {a.insight for a in angulos}
    assert all(s["corpo"] not in insights for s in brief.secoes)
    assert not any("determinística" in s["corpo"] for s in brief.secoes)
    # diferencial real vira seção (primeiro card)
    b2 = o.sintetizar({**_BRIEFING, "diferenciais": ["Atende no mesmo dia"]}, angulos)
    assert b2.secoes[0]["titulo"] == "Atende no mesmo dia"


def test_gerador_produz_html_valido():
    o = StubOrquestrador()
    brief = o.sintetizar(_BRIEFING, o.analisar(_BRIEFING))
    site = StubGeradorSite().gerar(brief, "clinica-sorriso")
    assert "index.html" in site.arquivos
    assert "<html" in site.arquivos["index.html"]
    assert brief.nome_empresa in site.arquivos["index.html"]


def test_deploy_devolve_url():
    o = StubOrquestrador()
    brief = o.sintetizar(_BRIEFING, o.analisar(_BRIEFING))
    site = StubGeradorSite().gerar(brief, "clinica-sorriso")
    res = StubDeploy().publicar(site)
    assert res.provider == "stub"
    assert "clinica-sorriso" in res.url
