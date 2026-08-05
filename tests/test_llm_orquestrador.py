

def test_copy_passa_pelo_gateway_antes_do_provider_cru(monkeypatch):
    """REGRESSÃO (2026-08-05): este caminho chamava api.groq.com direto e um 429 no
    pico matava a geração inteira — o JP não conseguia gerar demo nenhuma. A cascata
    do LiteLLM existia e nunca era usada aqui.

    O teste prova a ORDEM: gateway primeiro; provider cru só se o gateway estiver fora."""
    from app.providers import llm_orquestrador as lo
    chamadas = []

    def _fake(url, autorizacao, modelo, ps, pu, temp):
        chamadas.append(url)
        if url == lo._GATEWAY_URL:
            return {"ok": True}
        raise AssertionError("não devia ter chamado o provider cru com o gateway vivo")

    monkeypatch.setattr(lo, "_chamar", _fake)
    assert lo._groq_json("s", "u", "chave-qualquer") == {"ok": True}
    assert chamadas == [lo._GATEWAY_URL], chamadas


def test_gateway_fora_cai_no_provider_cru(monkeypatch):
    """Gateway fora do ar (container caído) não pode matar a geração: o provider cru
    é a última rede. Só aí — 429 do Groq NÃO é 'gateway fora'."""
    import urllib.error
    from app.providers import llm_orquestrador as lo
    chamadas = []

    def _fake(url, autorizacao, modelo, ps, pu, temp):
        chamadas.append(url)
        if url == lo._GATEWAY_URL:
            raise urllib.error.URLError("connection refused")
        return {"ok": "provider-cru"}

    monkeypatch.setattr(lo, "_chamar", _fake)
    assert lo._groq_json("s", "u", "chave")["ok"] == "provider-cru"
    assert chamadas == [lo._GATEWAY_URL, lo._CHAT_URL], chamadas
