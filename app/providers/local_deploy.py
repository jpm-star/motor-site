"""Deploy real MAIS SIMPLES possível: escreve o site em disco sob `OUT_DIR/<slug>/`.
Funciona hoje, sem nenhuma chave — serve de host provisório (ex.: atrás de um Caddy
`file_server` na VPS) até escolher um host definitivo (Vercel/Netlify/S3+CDN etc.),
que entra depois como 1 provider novo (mesmo seam de config, sem mexer na Pipeline)."""
from __future__ import annotations

import os
from pathlib import Path

from .base import DeployProvider, DeployResultado, SiteGerado


class LocalDeploy(DeployProvider):
    name = "local"

    def __init__(self, out_dir: str | None = None):
        self.out_dir = Path(out_dir or os.environ.get("SITE_OUT_DIR", "./out"))

    def publicar(self, site: SiteGerado) -> DeployResultado:
        destino = self.out_dir / site.slug
        destino.mkdir(parents=True, exist_ok=True)
        for caminho, conteudo in site.arquivos.items():
            alvo = destino / caminho
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_text(conteudo, encoding="utf-8")
        return DeployResultado(
            url=f"file://{destino.resolve()}/index.html",
            provider=self.name,
            deploy_id=site.slug,
            meta={"out_dir": str(destino)},
        )
