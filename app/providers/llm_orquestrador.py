"""Seam pro orquestrador real (C1): múltiplos modelos analisam o nicho por ângulos
diferentes (LLM fleet do JP, mesmo pool round-robin do resto do ecossistema — ver
memória `noemi-llm-key-fleet`), depois um modelo "editor" sintetiza os ângulos num
BriefingSite. Contrato de prompt ainda não existe neste ambiente — implementar
`analisar`/`sintetizar` quando as chaves LLM entrarem aqui. Até lá, falha explícita
(nunca finge um site pronto sem análise real). Uso: SITE_ORQUESTRADOR=llm."""
from __future__ import annotations

import os
from typing import Any

from .base import AnguloAnalise, BriefingSite, OrquestradorProvider


class LLMOrquestrador(OrquestradorProvider):
    name = "llm"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("SITE_LLM_API_KEY")

    def analisar(self, briefing: dict[str, Any]) -> list[AnguloAnalise]:
        if not self.api_key:
            raise RuntimeError("SITE_LLM_API_KEY ausente — provider não configurado")
        raise NotImplementedError(
            "LLMOrquestrador.analisar: implementar as chamadas reais (N prompts, um por "
            "ângulo) quando o contrato de prompt entrar (ver README §Providers reais). "
            "Até lá, use SITE_ORQUESTRADOR=stub."
        )

    def sintetizar(self, briefing: dict[str, Any], angulos: list[AnguloAnalise]) -> BriefingSite:
        if not self.api_key:
            raise RuntimeError("SITE_LLM_API_KEY ausente — provider não configurado")
        raise NotImplementedError(
            "LLMOrquestrador.sintetizar: implementar a chamada real (prompt 'editor' que "
            "funde os ângulos) quando entrar. Até lá, use SITE_ORQUESTRADOR=stub."
        )
