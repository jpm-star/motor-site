"""Prova que o T2 está PLUGADO — não que os módulos funcionam isolados.

POR QUE EXISTE: `conteudo_t2` e `multipagina` passavam nos próprios testes e o
produto entregava página única, porque `brief.paginas` nunca era escrito. Duas
metades corretas que ninguém conectou. Teste de unidade não cobre fronteira; este
cobre exatamente a fronteira e mais nada.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import pipeline  # noqa: E402


def test_t1_nao_chama_o_escritor_de_paginas(monkeypatch):
    chamou = []
    from app import conteudo_t2
    monkeypatch.setattr(conteudo_t2, "escrever", lambda *a, **k: chamou.append(1) or ([], []))
    pgs, erros = pipeline.paginas_t2({"nome_empresa": "X", "nicho": "y"})
    assert pgs == [] and erros == [] and not chamou, "T1 não pode gastar LLM com páginas irmãs"


def test_t2_chama_e_devolve_as_paginas(monkeypatch):
    from app import conteudo_t2
    fake = [{"slug": "servico-a", "h1": "Serviço A", "titulo": "t", "descricao": "d",
             "intro": "i", "blocos": [], "lista": [], "tipo": "Service"}]
    visto = {}

    def _fake(cart, **k):
        visto.update(cart)
        return fake, []
    monkeypatch.setattr(conteudo_t2, "escrever", _fake)
    pgs, erros = pipeline.paginas_t2({
        "nome_empresa": "Ferreira e Rachid", "nicho": "advocacia", "tier": "T2",
        "cidade": "Lins", "publico": "quem tem causa trabalhista",
        "diferenciais": ["atendimento presencial", "primeira consulta sem compromisso"]})
    assert pgs == fake and not erros
    assert visto["vertical"] == "advocacia"
    assert visto["regioes_atendidas"] == ["Lins"]
    # sem escopo/catálogo, os diferenciais são a fonte real — nunca deixar o modelo
    # inventar quais serviços a empresa presta
    assert visto["escopo"] == ["atendimento presencial", "primeira consulta sem compromisso"]


def test_t3_e_t4_tambem_sao_multipagina(monkeypatch):
    from app import conteudo_t2
    monkeypatch.setattr(conteudo_t2, "escrever", lambda cart, **k: ([{"h1": "x"}], []))
    for tier in ("T3", "T4", "t2"):
        pgs, _ = pipeline.paginas_t2({"nome_empresa": "X", "nicho": "y", "tier": tier})
        assert pgs, f"{tier} é cumulativo — tem que incluir o multi-página do T2"


def test_degradacao_nao_e_silenciosa(monkeypatch, caplog):
    """T2 que vira página única precisa APARECER — foi o modo de falha original."""
    import logging

    from app import conteudo_t2
    monkeypatch.setattr(conteudo_t2, "escrever",
                        lambda cart, **k: ([], ["sem ANTHROPIC_API_KEY"]))
    monkeypatch.setattr(pipeline, "orquestrador_ativo", lambda: _OrqFake())
    monkeypatch.setattr(pipeline, "gerador_ativo", lambda: _GerFake())
    monkeypatch.setattr(pipeline, "deploy_ativo", lambda: _DepFake())
    with caplog.at_level(logging.WARNING, logger="motor.pipeline"):
        pipeline.montar_site({"nome_empresa": "X", "nicho": "y", "tier": "T2"})
    assert any("degradou" in r.message for r in caplog.records), \
        "T2 caindo pra página única sem aviso é como o bug original passou despercebido"


class _Brief:
    nome_empresa = "X"
    headline = subheadline = cta_titulo = ""
    secoes: list = []
    paginas: list = []


class _OrqFake:
    def analisar(self, b): return []
    def sintetizar(self, b, a): return _Brief()


class _GerFake:
    def gerar(self, brief, slug): return object()


class _DepFake:
    def publicar(self, site): return object()
