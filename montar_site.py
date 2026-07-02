#!/usr/bin/env python3
"""C2/C3: JP briefa → site publicado. Um comando.

  python montar_site.py --nome "Escritório Contábil Silva" --nicho "contabilidade" \
      --whatsapp 5566999998888 --diferencial "20 anos de mercado" \
      --diferencial "Atendimento em 1h" [--cor "#1d4ed8"]

Defaults de produção (sem env): gerador=template (one-page real), deploy=local em
/var/www/sites servido pelo Caddy em https://sites.noemi.digital/<slug>/. Domínio
próprio do cliente depois = 1 bloco a mais no Caddyfile (ver README §Domínio)."""
from __future__ import annotations

import argparse
import os


def main() -> None:
    os.environ.setdefault("SITE_GERADOR", "template")
    os.environ.setdefault("SITE_DEPLOY", "local")
    os.environ.setdefault("SITE_OUT_DIR", "/var/www/sites")
    os.environ.setdefault("SITE_BASE_URL", "https://sites.noemi.digital")
    from app.pipeline import montar_site

    ap = argparse.ArgumentParser()
    ap.add_argument("--nome", required=True)
    ap.add_argument("--nicho", required=True)
    ap.add_argument("--whatsapp", required=True, help="ex.: 5566999998888")
    ap.add_argument("--diferencial", action="append", default=[], help="repetir por diferencial")
    ap.add_argument("--publico", default="", help="público-alvo (ajuda a síntese)")
    ap.add_argument("--cor", default="", help="cor primária hex, ex.: #1d4ed8")
    args = ap.parse_args()

    briefing = {
        "nome_empresa": args.nome,
        "nicho": args.nicho,
        "whatsapp": args.whatsapp,
        "diferenciais": args.diferencial,
        "publico": args.publico,
        "cor_primaria": args.cor or None,
    }
    resultado = montar_site(briefing)
    print(f"site publicado: {resultado.deploy.url}")
    print(f"arquivos em:    {resultado.deploy.meta.get('out_dir')}")


if __name__ == "__main__":
    main()
