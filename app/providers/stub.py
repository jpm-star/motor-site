"""Mock determinístico dos 4 estágios — permite testar a pipeline inteira sem
nenhuma chave real. A suíte roda 100% sobre isto (mesma filosofia do motor-video)."""
from __future__ import annotations

from typing import Any

from .base import (
    AnguloAnalise,
    BriefingSite,
    DeployProvider,
    DeployResultado,
    GeradorSiteProvider,
    OrquestradorProvider,
    SiteGerado,
)

_ANGULOS_PADRAO = ["diferenciacao", "publico_alvo", "prova_social"]


class StubOrquestrador(OrquestradorProvider):
    name = "stub"

    def analisar(self, briefing: dict[str, Any]) -> list[AnguloAnalise]:
        nicho = briefing.get("nicho", "negócio")
        return [
            AnguloAnalise(angulo=a, insight=f"[{a}] observação determinística pro nicho '{nicho}'")
            for a in _ANGULOS_PADRAO
        ]

    def sintetizar(self, briefing: dict[str, Any], angulos: list[AnguloAnalise]) -> BriefingSite:
        nome = briefing.get("nome_empresa", "Sua Empresa")
        nicho = briefing.get("nicho", "negócio")
        # Seções vêm SÓ de conteúdo REAL do briefing — nunca do insight dos ângulos
        # (que é meta-análise, não copy). Os ângulos guiam a estrutura, não viram
        # texto na tela. (Antes: os ângulos-placeholder vazavam pro site em produção.)
        secoes = [
            {"titulo": d.strip(), "corpo": f"{nome} entrega isso no dia a dia."}
            for d in briefing.get("diferenciais", []) if d.strip()
        ]
        if briefing.get("publico", "").strip():
            secoes.append({"titulo": "Para quem atendemos", "corpo": briefing["publico"].strip()})
        if briefing.get("prova_social", "").strip():
            secoes.append({"titulo": "Prova social", "corpo": briefing["prova_social"].strip()})
        if not secoes:  # nada real veio → uma seção honesta, não placeholder
            secoes = [{"titulo": f"Sobre a {nome}",
                       "corpo": f"{nome} atua em {nicho} com atendimento próximo e entrega no prazo."}]
        return BriefingSite(
            nome_empresa=nome,
            nicho=nicho,
            headline=f"{nome} — referência em {nicho}",
            subheadline="Atendimento rápido, resultado que fala por si.",
            secoes=secoes,
            cta_texto="Fale com a gente",
            cta_contato=briefing.get("whatsapp", "(a combinar)"),
            angulos_usados=angulos,
            cor_primaria=briefing.get("cor_primaria"),
            cidade=briefing.get("cidade", "").strip(),
            servico_principal=briefing.get("servico_principal", "").strip(),
        )


class StubGeradorSite(GeradorSiteProvider):
    name = "stub"

    def gerar(self, brief: BriefingSite, slug: str) -> SiteGerado:
        secoes_html = "\n".join(
            f'<section><h2>{s["titulo"]}</h2><p>{s["corpo"]}</p></section>' for s in brief.secoes
        )
        html = (
            f"<!doctype html><html lang=\"pt-br\"><head><meta charset=\"utf-8\">"
            f"<title>{brief.nome_empresa}</title></head><body>"
            f"<header><h1>{brief.headline}</h1><p>{brief.subheadline}</p></header>"
            f"{secoes_html}"
            f'<footer><a href="https://wa.me/{brief.cta_contato}">{brief.cta_texto}</a></footer>'
            f"</body></html>"
        )
        return SiteGerado(arquivos={"index.html": html}, slug=slug)


class StubDeploy(DeployProvider):
    name = "stub"

    def publicar(self, site: SiteGerado) -> DeployResultado:
        return DeployResultado(
            url=f"stub://sites/{site.slug}/index.html",
            provider=self.name,
            deploy_id=site.slug,
            meta={"arquivos": list(site.arquivos)},
        )
