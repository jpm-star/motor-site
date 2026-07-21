"""Sistema de design por segmento — direções, ancoragem por assunto, guarda anti-clichê."""
from app import design
from app.providers.template_real import GeradorTemplate
from app.providers.stub import StubOrquestrador


def test_invariante_nenhum_tema_e_cliche():
    design.validar_temas()  # levanta AssertionError se algo nascer clichê / par repetido


def test_direcoes_pre_pensadas():
    imob = design.escolher_tema("imobiliária", "Alfa Imóveis")
    clin = design.escolher_tema("clínica odontológica", "Sorriso")
    assert imob.id == "imobiliaria" and clin.id == "clinica"
    # imobiliária: sans grotesca no título (NUNCA serifa) + índigo, não terracota
    assert imob.fonte_titulo == "Manrope" and imob.fonte_titulo.lower() not in design._SERIFAS
    assert clin.acento == "#0d7d6e"  # deep teal fechado


def test_ancoragem_no_assunto_nao_no_tipo():
    assert design.escolher_tema("adega de vinhos finos", "Baco").id == "vinho"
    assert design.escolher_tema("energia solar", "SolarMax").id == "navy"
    assert design.escolher_tema("advocacia", "Lima & Assoc.").id == "grafite"


def test_acento_nudged_por_nome_paletas_quase_unicas():
    # 12 negócios desconhecidos distintos → acentos majoritariamente únicos
    # (nudge de matiz por nome; par tipográfico do pool finito pode recorrer).
    nomes = [f"Negócio {i}" for i in range(12)]
    acentos = {design.escolher_tema("floricultura", nm).acento for nm in nomes}
    assert len(acentos) >= 9, acentos
    # estável: mesmo nome → mesmo acento
    assert design.escolher_tema("x", "Alfa").acento == design.escolher_tema("x", "Alfa").acento


def test_direcao_pre_pensada_nao_varia():
    # imobiliária/clínica têm cor intencional exata, sem nudge
    assert design.escolher_tema("imobiliária", "A").acento == design.escolher_tema("imobiliária", "B").acento


def test_guarda_pega_o_cliche_claude_design():
    ruim = design.Tema("x", "#2a1a12", "#faf7f0", "#fff", "#eee", "#c2410c", "#fde",
                        "Instrument Serif", "Lora", "", "10px", "700", "0", "index", False)
    assert design._cliche(ruim)  # terracota + serifa


def test_render_por_segmento_difere_e_sem_placeholder():
    o = StubOrquestrador()
    def html(nicho, nome):
        b = o.sintetizar({"nome_empresa": nome, "nicho": nicho, "whatsapp": "5511999998888",
                          "diferenciais": ["Prazo garantido"]}, o.analisar({"nicho": nicho}))
        return GeradorTemplate().gerar(b, "s").arquivos["index.html"]
    imob = html("imobiliária", "Alfa Imóveis")
    clin = html("clínica", "Sorriso")
    assert "Manrope" in imob and "Instrument+Sans" in clin  # tipografias distintas
    assert "#4338ca" in imob and "#0d7d6e" in clin          # paletas distintas
    for h in (imob, clin):
        assert "determinística" not in h and "IntersectionObserver" in h  # sem placeholder + com motion
