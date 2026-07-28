"""Interfaces únicas do motor (C1): 3 estágios, cada um com adapter de provider
substituível — mesmo padrão do motor-video (B1). `Pipeline` (pipeline.py) só conhece
estas interfaces; troca de provider real é seam de config (config.py)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnguloAnalise:
    """Um dos "múltiplos modelos analisam o nicho por ângulos diferentes" do briefing
    original — cada ângulo é uma lente distinta sobre o mesmo nicho (não um provider
    diferente; ver OrquestradorProvider.analisar)."""
    angulo: str
    insight: str


@dataclass
class BriefingSite:
    """Síntese pós-análise: o que efetivamente vira conteúdo do site. Estrutura mínima
    e genérica pra caber qualquer nicho (nada específico de clínica/contabilidade/etc.
    aqui — quem sabe disso é o Provider real, via LLM, quando plugado)."""
    nome_empresa: str
    nicho: str
    headline: str
    subheadline: str
    secoes: list[dict[str, str]]  # [{"titulo": ..., "corpo": ...}, ...]
    cta_texto: str
    cta_contato: str
    angulos_usados: list[AnguloAnalise] = field(default_factory=list)
    cor_primaria: str | None = None  # cor de marca (hex) — o gerador usa se vier
    cidade: str = ""            # 1ª região do cartucho — SEO local (title + JSON-LD)
    servico_principal: str = ""  # serviço-âncora do cartucho — CTA pré-preenchido
    ancora_preco: dict = field(default_factory=dict)   # tiers de preço do cartucho — template renderiza SÓ se vier
    antes_depois: list = field(default_factory=list)   # prova social antes/depois — idem (vazio = sem seção)


def prova_social_texto(v) -> str:
    """prova_social pode vir STRING ou LISTA de {quem,texto}. Devolve texto pro contexto
    do LLM/stub sem quebrar (list.strip() explodia). '' se vazio."""
    if isinstance(v, list):
        return " · ".join(str(x.get("texto", "") if isinstance(x, dict) else x).strip()
                          for x in v if x)
    return str(v or "").strip()


@dataclass
class SiteGerado:
    """Saída do gerador: mapa caminho-relativo → conteúdo. Um `DeployProvider` só
    escreve isso onde quer que o site more (disco local, host estático, etc.)."""
    arquivos: dict[str, str]
    slug: str


@dataclass
class DeployResultado:
    url: str
    provider: str
    deploy_id: str
    meta: dict[str, Any] = field(default_factory=dict)


class OrquestradorProvider(ABC):
    """Estágio 1+2 do C1: analisa o nicho por ângulos diferentes e sintetiza num
    BriefingSite. Uma implementação pode usar 1 ou N modelos de LLM por baixo — quem
    chama só vê a lista de ângulos e a síntese final."""
    name: str

    @abstractmethod
    def analisar(self, briefing: dict[str, Any]) -> list[AnguloAnalise]:
        """`briefing` = o form que o JP preenche (nome, nicho, diferenciais, público,
        etc. — schema livre, o provider decide o que usa). Levanta exceção em falha;
        a Pipeline decide retry/kill switch, o provider não trata isso."""
        ...

    @abstractmethod
    def sintetizar(self, briefing: dict[str, Any], angulos: list[AnguloAnalise]) -> BriefingSite:
        ...


class GeradorSiteProvider(ABC):
    """Estágio 3: BriefingSite → site publicável (arquivos estáticos)."""
    name: str

    @abstractmethod
    def gerar(self, brief: BriefingSite, slug: str) -> SiteGerado:
        ...


class DeployProvider(ABC):
    """Estágio 4: publica o `SiteGerado` em algum host e devolve a URL final."""
    name: str

    @abstractmethod
    def publicar(self, site: SiteGerado) -> DeployResultado:
        ...
