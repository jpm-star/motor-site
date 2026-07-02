"""F/C3: GeradorTemplate (one-page real) + URL pública do LocalDeploy + fluxo do
montar_site com os providers de produção (template+local)."""
import pytest

from app.pipeline import montar_site
from app.providers.base import BriefingSite
from app.providers.local_deploy import LocalDeploy
from app.providers.stub import StubGeradorSite
from app.providers.template_real import GeradorTemplate

BRIEF = BriefingSite(
    nome_empresa="Escritório Silva",
    nicho="contabilidade",
    headline="Contabilidade sem dor de cabeça",
    subheadline="Seu imposto em dia, seu tempo de volta.",
    secoes=[{"titulo": "20 anos de mercado", "corpo": "Experiência comprovada."}],
    cta_texto="Fale com a gente",
    cta_contato="55 (66) 99999-8888",
)


def test_template_gera_onepage_completa():
    site = GeradorTemplate().gerar(BRIEF, "escritorio-silva")
    html = site.arquivos["index.html"]
    assert "Contabilidade sem dor de cabeça" in html
    assert "20 anos de mercado" in html
    assert 'https://wa.me/5566999998888"' in html  # contato vira link limpo (só dígitos)
    assert 'name="viewport"' in html and 'property="og:title"' in html
    assert "--cor: #0f766e" in html  # cor default quando briefing não traz


def test_template_escapa_conteudo_do_briefing():
    b = BriefingSite(**{**BRIEF.__dict__, "headline": '<script>alert("x")</script>'})
    html = GeradorTemplate().gerar(b, "s").arquivos["index.html"]
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_template_usa_cor_do_brief():
    b = BriefingSite(**{**BRIEF.__dict__, "cor_primaria": "#1d4ed8"})
    html = GeradorTemplate().gerar(b, "s").arquivos["index.html"]
    assert "--cor: #1d4ed8" in html


def test_local_deploy_devolve_url_publica_com_base_url(tmp_path):
    site = GeradorTemplate().gerar(BRIEF, "escritorio-silva")
    r = LocalDeploy(out_dir=str(tmp_path), base_url="https://sites.noemi.digital").publicar(site)
    assert r.url == "https://sites.noemi.digital/escritorio-silva/"
    assert (tmp_path / "escritorio-silva" / "index.html").exists()


def test_local_deploy_sem_base_url_segue_file_url(tmp_path):
    site = StubGeradorSite().gerar(BRIEF, "x")
    r = LocalDeploy(out_dir=str(tmp_path)).publicar(site)
    assert r.url.startswith("file://")


def test_montar_site_producao_ponta_a_ponta(tmp_path, monkeypatch):
    monkeypatch.setenv("SITE_GERADOR", "template")
    monkeypatch.setenv("SITE_DEPLOY", "local")
    monkeypatch.setenv("SITE_OUT_DIR", str(tmp_path))
    monkeypatch.setenv("SITE_BASE_URL", "https://sites.noemi.digital")
    r = montar_site({
        "nome_empresa": "Clínica Vida",
        "nicho": "estética",
        "whatsapp": "5566988887777",
        "diferenciais": ["Avaliação gratuita", "Equipe certificada"],
        "cor_primaria": "#be185d",
    })
    assert r.deploy.url == "https://sites.noemi.digital/clinica-vida/"
    html = (tmp_path / "clinica-vida" / "index.html").read_text()
    assert "Avaliação gratuita" in html and "--cor: #be185d" in html
    assert "wa.me/5566988887777" in html


def test_diferenciais_do_briefing_viram_cards_primeiro():
    from app.providers.stub import StubOrquestrador
    o = StubOrquestrador()
    brief = o.sintetizar({"nome_empresa": "X", "nicho": "y", "diferenciais": ["Entrega em 24h"]},
                         o.analisar({"nicho": "y"}))
    assert brief.secoes[0]["titulo"] == "Entrega em 24h"
