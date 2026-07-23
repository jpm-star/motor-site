"""Lote de demos: parse CSV, slug demo-*, falha isolada não derruba o lote."""
from pathlib import Path

from app import batch_demos


def test_lote_falha_isolada(tmp_path: Path):
    csv = tmp_path / "p.csv"
    csv.write_text(
        "nome_empresa,nicho,cidade,whatsapp,servico_principal\n"
        "Marmoraria Silva,Marmoraria,Campinas,5519998887777,granito\n"
        ",Contabilidade,SP,5511999,abertura\n",  # sem nome → falha isolada
        encoding="utf-8",
    )
    out = tmp_path / "demos"
    ok, falhas = batch_demos.rodar(csv, out)
    assert ok == 1 and len(falhas) == 1
    idx = out / "demo-marmoraria-silva" / "index.html"
    assert idx.is_file()
    html = idx.read_text(encoding="utf-8")
    assert "Marmoraria em Campinas | Marmoraria Silva" in html  # SEO local
    assert "application/ld+json" in html                        # JSON-LD


def test_json_lista(tmp_path: Path):
    j = tmp_path / "p.json"
    j.write_text('[{"nome_empresa":"Ateliê Pedra","nicho":"Marmoraria","cidade":"Jundiaí"}]',
                 encoding="utf-8")
    ok, falhas = batch_demos.rodar(j, tmp_path / "d")
    assert ok == 1 and not falhas
