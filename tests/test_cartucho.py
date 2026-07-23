"""Cartucho de cliente → briefing → site montado (fecha o gargalo cross-repo)."""
import json
from pathlib import Path

from app import cartucho, pipeline


def _cartucho(tmp: Path) -> str:
    (tmp / "cli.json").write_text(json.dumps({
        "nome_empresa": "Ateliê Pedra", "vertical": "marmoraria",
        "escopo": "granito, quartzo, mármore", "regioes_atendidas": ["Jundiaí"],
        "whatsapp_dono": "5511988887777"}), encoding="utf-8")
    return str(tmp)


def test_cartucho_vira_site(tmp_path):
    b = cartucho.briefing_de_cartucho("cli", base=_cartucho(tmp_path))
    assert b["cidade"] == "Jundiaí" and b["servico_principal"] == "granito"
    res = pipeline.montar_site(b)  # stub+... default; não deve levantar
    assert res.brief.nome_empresa == "Ateliê Pedra"
    assert res.brief.cidade == "Jundiaí"  # cidade chega no BriefingSite (SEO local)


def test_cartucho_inexistente_vazio(tmp_path):
    assert cartucho.briefing_de_cartucho("nao-existe", base=str(tmp_path)) == {}
