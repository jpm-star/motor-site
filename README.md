# Motor Montador de Site

JP briefa (form curto: nome, nicho, diferenciais, público, contato), o motor entrega
um site publicável (~R$800, margem alta — Workstream C do LOOP.md do ecossistema JP).

4 estágios, cada um com adapter de provider substituível (`app/providers/base.py`),
orquestrados por `app/pipeline.py:montar_site()` numa chamada só (sem passo manual
entre eles):

1. **Analisar** — N modelos/prompts olham o nicho por ângulos diferentes
   (diferenciação, público-alvo, prova social, ...).
2. **Sintetizar** — funde os ângulos num `BriefingSite` (headline, seções, CTA).
3. **Gerar** — `BriefingSite` → arquivos estáticos (HTML hoje; template real do
   ecossistema entra depois sem mudar a interface).
4. **Publicar** — escreve/sobe o site em algum host e devolve a URL final.

## Rodar os testes

```
pip install -r requirements.txt
python -m pytest   # `pytest` sozinho não acha o pacote `app` sem instalar; use -m
```

A suíte inteira roda sobre providers **stub** (determinísticos) — zero chave real
necessária. Sem venv neste ambiente: rodar via `docker run --rm -v "$PWD":/app -w /app
python:3.12-slim bash -c "pip install -q -r requirements.txt && python -m pytest -q"`.

## Decisão de arquitetura (C1) — registrada por Code, JP autorizou decidir sozinho

- **Análise de ângulos = seam LLM** (`LLMOrquestrador`, `app/providers/llm_orquestrador.py`):
  mesmo padrão do `HiggsfieldProvider` no motor-video — a interface está pronta, mas
  `analisar()`/`sintetizar()` levantam `NotImplementedError` até o contrato de prompt
  + as chaves do pool LLM do JP (ver memória `noemi-llm-key-fleet`) entrarem aqui.
  Não bloqueia o resto: `SITE_ORQUESTRADOR=stub` (default) já produz um site completo
  e coerente hoje, sem IA nenhuma — só troca depois pra ficar mais esperto por nicho.
- **Geração do site = HTML determinístico, real e funcional HOJE** (não é stub-mock,
  é o entregável de fato — só não é bonito ainda). Reusar a stack de frontend do
  ecossistema (Next.js do `web/`) como *template real* é o próximo passo natural
  (troca só `app/providers/stub.py:StubGeradorSite` por um `TemplateGeradorSite` que
  gera a partir de um template Next exportado estático — mesma interface, 1 arquivo).
- **Deploy = `LocalDeploy` (real, funciona hoje)**: escreve os arquivos em
  `SITE_OUT_DIR/<slug>/`, pra servir atrás de um Caddy `file_server` já rodando na
  VPS do JP (mesmo padrão dos outros deploys do ecossistema) — zero custo de host
  novo, zero chave, publicável hoje. Um host definitivo (Vercel/Netlify/S3+CDN) é 1
  provider novo + 1 linha em `config.py` quando o volume justificar (não gold-plating
  agora: reaproveitar a VPS que já existe é a menor mudança que destrava venda).

Trocar de provider é **uma linha** de `.env` por estágio: `SITE_ORQUESTRADOR=llm`,
`SITE_GERADOR=...`, `SITE_DEPLOY=local`. Default de todos = `stub`.

## Publicar um site (F/C2-C3) — 1 comando

```
python3 montar_site.py --nome "Escritório Contábil Silva" --nicho "contabilidade" \
    --whatsapp 5566999998888 --diferencial "20 anos de mercado" \
    --diferencial "Atendimento em 1h" --cor "#1d4ed8"
# => site publicado: https://sites.noemi.digital/escritorio-contabil-silva/
```

O CLI usa os providers de produção por default: `SITE_GERADOR=template`
(`app/providers/template_real.py` — one-page real: hero, cards de diferenciais,
CTA WhatsApp fixo, SEO/OG, responsivo, cor de marca, conteúdo escapado) +
`SITE_DEPLOY=local` escrevendo em `/var/www/sites/<slug>/`, servido pelo Caddy da
VPS em `https://sites.noemi.digital/<slug>/`.

### Host/domínio (pendências de 1 vez)

1. **Caddy**: `cat deploy/caddy-sites.snippet >> /etc/caddy/Caddyfile && caddy
   validate --config /etc/caddy/Caddyfile && systemctl reload caddy`.
2. **DNS**: A record `sites.noemi.digital -> 2.24.120.204` (cert TLS emite sozinho).
3. **Domínio próprio do cliente**: 1 bloco a mais no Caddyfile com `root *
   /var/www/sites/<slug>` (modelo comentado no snippet) + A record do cliente.

## Status

F (C2/C3) entregue: template real + deploy público + CLI de 1 comando. Falta só o
apply do snippet Caddy + DNS (acima) e, opcional depois, o contrato de prompt do
`LLMOrquestrador` quando as chaves entrarem.
