"""Auditor: sinais → score → tier + diagnóstico. Offline (HTML fixo, sem rede)."""
from app import auditor

_HTML_BOM = """<!doctype html><html><head>
<title>Marmoraria X</title><meta name="viewport" content="w">
<meta name="description" content="d"><script type="application/ld+json">{}</script>
</head><body><h1>oi</h1><form></form><a href="https://wa.me/551199">zap</a>
<details>FAQ</details></body></html>"""


def test_sinais_e_score_site_bom():
    info = {"url_final": "https://x.com/", "ms": 100, "kb": 5}
    s = auditor._sinais(_HTML_BOM, info, "https://x.com")
    assert s["whatsapp"] and s["formulario"] and s["viewport"] and s["jsonld"] and s["aeo"]
    score, cat = auditor._score(s)
    assert cat["Conversão"] == 30 and cat["Mobile"] == 20  # ambos os sinais presentes
    assert score >= 70


def test_tier_por_score():
    assert auditor._tier(False, 0) == 1     # sem site
    assert auditor._tier(True, 20) == 2     # site fraco
    assert auditor._tier(True, 55) == 3
    assert auditor._tier(True, 90) == 4


def test_auditar_sem_url_vira_tier1():
    r = auditor.auditar("", "Fulano")
    assert r["tem_site"] is False and r["tier"] == 1
    assert "não tem site" in r["diagnostico"]


def test_diagnostico_lista_gaps():
    info = {"url_final": "https://x.com/", "ms": 3000}
    s = auditor._sinais("<html><head><title>t</title></head><body></body></html>", info, "https://x.com")
    r = auditor._resultado("Loja Y", "https://x.com", True, s, info, *(_sc(s)))
    assert "não tem botão de WhatsApp" in r["diagnostico"] and "Plano" in r["diagnostico"]


def _sc(s):
    score, cat = auditor._score(s)
    return score, cat


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-q"])
