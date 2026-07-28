"""Cartucho de CLIENTE → briefing do site (motor-site). Fecha o gargalo: hoje o
pipeline recebe um briefing solto; aqui um cartucho real (o mesmo JSON que o SDR
usa) vira briefing pronto pro montar_site — sem info do cliente duplicada. Lê a
MESMA fonte (NOEMI_CARTUCHOS_DIR) que o shared-core do vídeo; nunca lança.

Chamado por: quem monta site de cliente já cadastrado. Retorna: dict de briefing
(nome_empresa, nicho, cidade, servico_principal, whatsapp, diferenciais).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

_NOME_SEGURO = re.compile(r"[^a-z0-9_-]")


def _carregar(nome: str, base: str | None = None) -> dict:
    """Cartucho <base>/<nome>.json como dict. Best-effort: ausente/quebrado → {}.
    Nome saneado contra path traversal."""
    base = base or os.environ.get("NOEMI_CARTUCHOS_DIR")
    nome = _NOME_SEGURO.sub("", (nome or "").lower().removesuffix(".json"))
    if not base or not nome:
        return {}
    caminho = Path(base) / f"{nome}.json"
    if not caminho.is_file():
        return {}
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _escopo_itens(cart: dict) -> list[str]:
    """Escopo (string 'a, b, c' ou lista) → lista de serviços limpa."""
    esc = cart.get("escopo") or ""
    itens = esc if isinstance(esc, list) else str(esc).split(",")
    return [i.strip() for i in itens if str(i).strip()]


def briefing_de_cartucho(nome: str, base: str | None = None) -> dict:
    """Cartucho <nome>.json → briefing pro montar_site. {} se o cartucho não existe
    (o caller decide o que fazer). Mapeamento honesto: só campos que o cartucho tem."""
    cart = _carregar(nome, base)
    if not cart:
        return {}
    itens = _escopo_itens(cart)
    regioes = cart.get("regioes_atendidas") or []
    return {
        "nome_empresa": (cart.get("nome_empresa") or "").strip(),
        "nicho": (cart.get("vertical") or "").strip(),
        "cidade": str(regioes[0]).strip() if regioes else "",
        "servico_principal": itens[0] if itens else (cart.get("vertical") or "").strip(),
        "whatsapp": (cart.get("whatsapp_dono") or "").strip(),
        "diferenciais": itens,  # cada serviço vira uma seção honesta no site
        "publico": (cart.get("criterio_qualificado") or "").strip(),
        # Padrões validados pelo Radar (só entram se o cartucho tiver — cartucho de
        # cliente SEM esses campos gera igual a antes: fallback gracioso, não quebra).
        "ancora_preco": cart.get("ancora_preco") or {},
        "prova_social": cart.get("prova_social") or [],
        "logo_svg": (cart.get("logo_svg") or "").strip(),   # logo de marca — nav + favicon (vazio = texto)
        "catalogo": cart.get("catalogo") or [],              # escopo por tier (seção de catálogo)
    }


if __name__ == "__main__":  # self-check (usa um cartucho real se o dir estiver setado)
    b = briefing_de_cartucho("../etc/passwd")
    assert b == {}, "path traversal deveria dar {}"
    # mapeamento a partir de um dict simulado no formato do cartucho
    import tempfile
    d = tempfile.mkdtemp()
    Path(d, "x.json").write_text(json.dumps({
        "nome_empresa": "Marmoraria X", "vertical": "marmoraria",
        "escopo": "granito, quartzo", "regioes_atendidas": ["Campinas"],
        "whatsapp_dono": "5519999"}), encoding="utf-8")
    b = briefing_de_cartucho("x", base=d)
    assert b["nome_empresa"] == "Marmoraria X" and b["cidade"] == "Campinas"
    assert b["servico_principal"] == "granito" and b["diferenciais"] == ["granito", "quartzo"]
    print("cartucho→briefing OK:", b["nome_empresa"], "|", b["cidade"], "|", b["servico_principal"])
