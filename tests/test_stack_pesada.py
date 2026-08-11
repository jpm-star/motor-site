"""A stack pesada precisa CHEGAR no HTML — e só na página que a usa.

O risco que estes testes cobrem não é a lib estar errada: é ela ficar INERTE. A
assinatura `processo` viveu meses declarada em 5 temas sem o template renderizar
nada, e a camada de motion já saiu uma vez sem casar segmento nenhum. Peso
declarado e nunca exercido é o modo de falha da casa.
"""
from __future__ import annotations

from app import design, stack_pesada
from app.providers.base import BriefingSite
from app.providers.template_real import GeradorTemplate


def _brief(nicho: str) -> BriefingSite:
    return BriefingSite(
        nome_empresa=f"Teste {nicho}", nicho=nicho,
        headline="Seu carro pronto no prazo combinado",
        subheadline="Diagnóstico honesto, orçamento antes do serviço.",
        secoes=[{"titulo": f"Passo {i}", "corpo": "Texto real do passo, sem placeholder."}
                for i in range(1, 5)],
        cta_texto="Falar no WhatsApp", cta_contato="5514998745847", cidade="Bauru",
        servico_principal="revisão completa")


def _html(nicho: str) -> str:
    return GeradorTemplate().gerar(_brief(nicho), "slug-teste").arquivos["index.html"]


def _nicho_com(assinatura: str, escuro: bool | None = None) -> str:
    """Um nicho real cujo tema bate os critérios — em vez de fixar o nome de um
    tema, que muda quando a paleta é reorganizada."""
    for n in ("oficina mecânica", "clínica odontológica", "padaria artesanal",
              "imobiliária", "advocacia", "academia", "pet shop", "restaurante",
              "barbearia", "arquitetura", "contabilidade", "farmácia"):
        t = design.escolher_tema(n, f"Empresa {n}")
        if t.assinatura == assinatura and (escuro is None or t.hero_escuro == escuro):
            return n
    raise AssertionError(f"nenhum nicho com assinatura={assinatura} escuro={escuro}")


def test_tema_processo_emite_cena_de_verdade():
    """Sem isto a assinatura `processo` volta a ser um token decorativo."""
    h = _html(_nicho_com("processo"))
    assert h.count("data-passo") == 4, "os 4 passos precisam estar marcados"
    assert "data-cena" in h and "cena-v1.js" in h
    assert "cena-ativa" in h, "o CSS do layout sobreposto tem que ir junto"


def test_hero_claro_nao_paga_os_119kb_do_three():
    h = _html(_nicho_com("processo", escuro=False))
    assert "campo-v1.js" not in h and "data-campo" not in h


def test_hero_escuro_liga_o_campo():
    h = _html(_nicho_com("processo", escuro=True))
    assert "data-campo" in h and "campo-v1.js" in h


def test_tema_sem_processo_nao_baixa_gsap():
    h = _html(_nicho_com("index"))
    assert "cena-v1.js" not in h and "data-passo" not in h


def test_passos_degradam_legiveis_sem_js():
    """O layout sobreposto depende de `.cena-ativa`, que só o JS adiciona. Se o CSS
    posicionasse os passos direto, sem JS eles empilhariam texto sobre texto."""
    css = stack_pesada.css_cena()
    assert "position:absolute" in css
    for regra in css.split("}"):
        if "position:absolute" in regra:
            assert ".cena-ativa" in regra, "posicionamento solto deixaria os passos ilegíveis sem JS"


def test_nada_da_stack_bloqueia_o_primeiro_paint():
    h = _html(_nicho_com("processo", escuro=True))
    assert "addEventListener('load'" in h
    # nenhum <script src> da stack no HTML: tudo entra por import() depois do load
    assert 'src="/_lib/' not in h, "script externo da stack viraria render-blocking"
