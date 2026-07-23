"""CLI de geração de demos em lote (motor-site): CSV/JSON de prospects → N sites
`demo-*` em disco, SEM publicar no definitivo. Chamado na mão pelo JP; fila serial,
log por item, falha de um prospect NÃO derruba o lote. Retorna código != 0 se houve
qualquer falha. Uso: python -m app.batch_demos prospects.csv [--out out/demos]

Prospect (colunas CSV / chaves JSON): nome_empresa (obrigatório), nicho, cidade,
whatsapp, servico_principal, diferenciais (";"-separado no CSV), publico, cor_primaria.
Cada linha é o mini-briefing do prospect — prospect ainda NÃO é cliente, então não há
cartucho: o site é a isca ANTES da conversão.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from .pipeline import _slug
from .providers.local_deploy import LocalDeploy
from .providers.stub import StubOrquestrador
from .providers.template_real import GeradorTemplate

_OUT_PADRAO = "out/demos"  # isolado do out/ definitivo — demo nunca vai pro ar oficial


def _linhas(caminho: Path) -> list[dict]:
    """Prospects do arquivo. .json = lista de objetos; qualquer outro = CSV."""
    if caminho.suffix.lower() == ".json":
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        if not isinstance(dados, list):
            raise ValueError("JSON de prospects deve ser uma LISTA de objetos")
        return dados
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _briefing(row: dict) -> dict:
    """Linha de prospect → briefing dict do pipeline. `diferenciais` aceita lista
    (JSON) ou string ';'-separada (CSV)."""
    dif = row.get("diferenciais") or []
    if isinstance(dif, str):
        dif = [d.strip() for d in dif.split(";") if d.strip()]
    return {
        "nome_empresa": (row.get("nome_empresa") or "").strip(),
        "nicho": (row.get("nicho") or "").strip(),
        "cidade": (row.get("cidade") or "").strip(),
        "whatsapp": (row.get("whatsapp") or "").strip(),
        "servico_principal": (row.get("servico_principal") or "").strip(),
        "publico": (row.get("publico") or "").strip(),
        "cor_primaria": (row.get("cor_primaria") or "").strip() or None,
        "diferenciais": dif,
    }


def _gerar_um(briefing: dict, out_dir: Path) -> str:
    """Gera 1 demo (stub+template+local, determinístico, ZERO custo de LLM) sob
    out_dir/demo-<slug>/. Devolve o caminho do index.html. Levanta em erro."""
    brief = StubOrquestrador().sintetizar(briefing, [])
    slug = f"demo-{_slug(brief.nome_empresa)}"
    site = GeradorTemplate().gerar(brief, slug)
    resultado = LocalDeploy(out_dir=str(out_dir)).publicar(site)
    return resultado.meta["out_dir"]


def rodar(caminho: Path, out_dir: Path) -> tuple[int, list[tuple[str, str]]]:
    """Lote serial. Devolve (ok, falhas[(nome, motivo)])."""
    prospects = _linhas(caminho)
    ok, falhas = 0, []
    for i, row in enumerate(prospects, 1):
        briefing = _briefing(row)
        nome = briefing["nome_empresa"] or f"linha {i}"
        if not briefing["nome_empresa"]:
            falhas.append((nome, "sem nome_empresa"))
            print(f"[{i}/{len(prospects)}] FALHA {nome}: sem nome_empresa")
            continue
        try:
            destino = _gerar_um(briefing, out_dir)
            ok += 1
            print(f"[{i}/{len(prospects)}] OK    {nome} → {destino}")
        except Exception as exc:  # um prospect quebrado não derruba o lote
            falhas.append((nome, str(exc)[:120]))
            print(f"[{i}/{len(prospects)}] FALHA {nome}: {str(exc)[:120]}")
    return ok, falhas


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print("uso: python -m app.batch_demos prospects.csv|.json [--out DIR]")
        return 2
    caminho = Path(argv[0])
    if not caminho.is_file():
        print(f"arquivo não encontrado: {caminho}")
        return 2
    out_dir = Path(_OUT_PADRAO)
    if "--out" in argv:
        out_dir = Path(argv[argv.index("--out") + 1])

    ok, falhas = rodar(caminho, out_dir)
    print(f"\n=== lote: {ok} OK, {len(falhas)} falha(s) | demos em {out_dir}/ ===")
    for nome, motivo in falhas:
        print(f"  - {nome}: {motivo}")
    return 0 if not falhas else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
