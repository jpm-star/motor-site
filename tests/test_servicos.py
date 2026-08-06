"""Regressão do erro crítico #4 (auditoria Rações & Cia, 2026-08-05/06).

O site de um pet shop foi ao ar com os serviços "Atendimento / Orçamento /
Acompanhamento" ilustrados por `service,professional` — foto de escritório. A causa era
um dicionário fechado de 5 segmentos: tudo que não fosse clínica caía no genérico.

Estes testes travam as duas metades do conserto: o segmento tem que ser RECONHECIDO, e
o card sem foto aprovada não pode voltar a puxar imagem aleatória de banco.
"""
from __future__ import annotations

import app.servicos as sv
from app.providers.template_real import _bloco_catalogo_motion


def test_pet_shop_nao_cai_no_generico():
    assert sv.chave_curada("pet shop") == "petshop"
    assert sv.chave_curada("Rações e Cia") == "petshop"      # plural, o nome real do lead
    nomes = [n for n, _, _ in sv.servicos_do_segmento("pet shop")]
    assert "Banho e Tosa" in nomes
    assert "Atendimento" not in nomes, "o genérico voltou a vencer o segmento"


def test_segmentos_curados_nunca_sao_genericos():
    proibidos = {"atendimento", "orçamento", "acompanhamento", "consultoria", "qualidade"}
    for chave, itens in sv.CURADOS.items():
        for nome, desc, foto in itens:
            assert nome.lower() not in proibidos, f"{chave} tem item genérico: {nome}"
            assert desc and foto, f"{chave}/{nome} incompleto"
            # keyword de foto genérica é o que trouxe reunião de escritório pro pet shop
            assert foto not in ("service,professional", "business", "office"), chave


def test_desconhecido_nao_casa_com_curadoria():
    """Nicho fora da curadoria devolve "" (vai pro LLM), NÃO um match falso."""
    assert sv.chave_curada("padaria artesanal") == ""
    assert sv.chave_curada("") == ""


def test_coracao_nao_vira_pet_shop():
    """O radical curto 'raç' pegaria 'coração' — cardiologia virando pet shop."""
    assert sv.chave_curada("clínica do coração") != "petshop"


def test_sem_foto_aprovada_nao_puxa_banco_de_imagem():
    """Posição sem acervo vira PLACA. O fallback pro loremflickr publicou uma estátua
    de urso ilustrando 'Acessórios e Higiene' num pet shop."""
    html = _bloco_catalogo_motion("pet shop", "5514999999999", acervo=["/x/1.jpg"])
    assert "loremflickr" not in html and "picsum" not in html
    assert "/x/1.jpg" in html              # a única foto real entrou
    assert "sv-semfoto" in html            # e as demais viraram placa


def test_acervo_com_buraco_no_meio_nao_desloca_as_fotos():
    """Lista compactada empurraria a foto do serviço 3 pro card do serviço 1."""
    html = _bloco_catalogo_motion("pet shop", "", acervo=["", "/x/2.jpg"])
    i_placa, i_foto = html.index("sv-semfoto"), html.index("/x/2.jpg")
    assert i_placa < i_foto, "a foto subiu pro card errado"
