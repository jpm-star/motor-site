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


def test_titulo_nao_e_fatiado_em_spans():
    """REGRESSÃO (2026-08-06): fatiar o h1 em <span class="pal"> APAGOU o título de todos
    os sites. O h1 usa background-clip:text — os spans herdam o text-fill transparente e
    não herdam o gradiente do fundo, então cada palavra vira texto invisível.

    Regra: não se fatia elemento que usa background-clip:text."""
    from app import design
    js = design.js_motion_scroll()
    assert "'pal'" not in js and '"pal"' not in js, "o fatiamento do título voltou"
    css = design.css_motion_scroll()
    assert ".hero h1 {" in css, "o título precisa animar como elemento inteiro"


def test_card_sem_foto_usa_icone_nao_letra_gigante():
    """REGRESSÃO: a placa mostrava a INICIAL do serviço em corpo enorme. Publicado, virou
    um 'A' e um 'L' de 60px ocupando o card — lê como placeholder quebrado."""
    from app.providers.template_real import _bloco_catalogo_motion

    html = _bloco_catalogo_motion("odontologia", "5514999999999")
    placa = html.split('class="sv-placa"')[1][:200]
    assert "<svg" in placa, "a placa tem que trazer ícone"
    assert "font-size:clamp(2.4rem" not in html, "a tipografia gigante voltou"
    # e o texto do serviço continua no card, que é o que de fato informa
    assert "Avaliação" in html


def test_hero_trust_nao_divide_linha_com_o_cta():
    """REGRESSÃO: `.hero-trust` era inline-block, igual ao `.btn` que vem antes — dois
    inline-block adjacentes ficam na MESMA LINHA e o margin-top não separa nada. No site
    publicado, lia como texto sobreposto ao botão."""
    from app.providers.base import BriefingSite
    from app.providers.template_real import GeradorTemplate

    html = GeradorTemplate().gerar(
        BriefingSite(nome_empresa="X", nicho="clínica odontológica", headline="H",
                     subheadline="S", secoes=[], cta_texto="C", cta_contato="5514999999999"), "x").arquivos["index.html"]
    i = html.index(".hero-trust")
    assert "display:block" in html[i:i + 220], "hero-trust voltou a dividir linha com o CTA"


def test_overlay_nao_nasce_com_src_vazio():
    """REGRESSÃO: `<img src="">` não é "sem imagem" — o navegador resolve a string vazia
    para a URL da PÁGINA e dispara um request extra que sempre falha. Estava em 39 dos 54
    sites publicados; o gate visual (qa_visual) o encontrou.

    TIRAR o src NÃO resolve, e foi o que a primeira correção fez: `<img>` sem src reporta
    `complete=true` e `naturalWidth=0` — a MESMA assinatura de imagem quebrada que a sonda
    procura (medido no Chromium). Os 39 sites continuariam reprovando depois de regerados.
    Só um src que CARREGA (GIF 1×1 transparente) tira o elemento do radar."""
    from app.providers.base import BriefingSite
    from app.providers.template_real import GeradorTemplate

    html = GeradorTemplate().gerar(
        BriefingSite(nome_empresa="X", nicho="clínica odontológica", headline="H",
                     subheadline="S", secoes=[], cta_texto="C",
                     cta_contato="5514999999999"), "x").arquivos["index.html"]
    assert 'src=""' not in html, "voltou um src vazio no HTML"
    i = html.index('id="svImg"')
    assert 'src="data:image/gif;base64,' in html[i:i + 140], \
        "o placeholder do overlay voltou a ficar sem src que carregue"
