# STATUS — Gate técnico Tier 2 (AEO/SEO) — 2026-07-29

_Estado honesto. NÃO reivindica "Tier 2 provado" — só o que de fato foi feito e o que trava._

## ✅ Feito (por mim, hoje)
- **37 testes verdes** na `feat/tier2-seo-wiring` (antes de mergear, como pedido).
- **Merge fast-forward** de `feat/tier2-seo-wiring` → `feat/jpos-tier1` (1 commit: `d5f4498`,
  fiação dos 6 módulos AEO/SEO no gerador). **37 testes verdes de novo** pós-merge.
- Merge **não empurrado** (`git push` pendente — decisão sua) e **não muda nada no ar**:
  jpos.com.br é estático em `/var/www/jpos`, não é servido por branch.

## ⛔ NÃO fiz de propósito: regenerar/publicar jpos.com.br
Dois motivos duros:

1. **Regenerar apagaria a copy aprovada.** Invariante do próprio Tier 1
   (RELATORIO_BUILD_JPOS): _"copy Groq é não-determinística: pra preservar a aprovada, **patcha
   o HTML**, não regera."_ Rodar o gerador de novo pra "ligar o T2" reescreveria a copy que já
   está no ar e foi validada. Deploy de T2 em prod tem que ser **patch dos elementos de head**
   (schema.org / sitemap / robots / GA4) no HTML existente — não regeneração cega.

2. **Falta o GA4 (gate humano).** Sem `GA4_MEASUREMENT_ID`, a tag GA4 sai fora (degrada
   honesto), e 1 dos 3 critérios de aceite do T2 já nasce incompleto.

## 🔴 Precisa de VOCÊ (gates humanos — agente não resolve)
1. **GSC**: verificar o domínio `jpos.com.br` no Google Search Console.
2. **GA4**: criar a property + pegar o `measurement id` (`G-XXXXXXX`).
3. Decidir: `git push` da `feat/jpos-tier1` agora, ou segurar.

## Deploy correto de T2 (quando os gates entrarem) — receita segura
1. `export SITE_URL=https://jpos.com.br` + `export GA4_MEASUREMENT_ID=G-XXXX`.
2. **Patchar** no `/var/www/jpos/index.html` os blocos de head do T2 (1 JSON-LD @graph,
   sitemap/robots gerados, GA4) — sem regenerar a copy. `robots.txt` + `sitemap.xml` são
   arquivos novos, publica direto em `/var/www/jpos/`.
3. Submeter sitemap no GSC, rodar o Rich Results Test no JSON-LD, confirmar evento real no GA4.
4. **Só então** marcar "Tier 2 PROVADO" — os 3 checks reais, não os testes de unidade.

## Regra
Testes de unidade verdes ≠ validado pelo Google. Enquanto os 3 checks reais não baterem, o
discurso de venda é "**ativando essa semana**", nunca "já funciona no Google".
(ver `noemi-infra/docs/APOSTILA_VENDAS_T2.md`)

---

## Motion premium unificado no gerador (2026-07-29)
O gerador real (`app/providers/template_real.py`, `GeradorTemplate`) agora emite a seção
**"Nossos serviços" com grid→detalhe premium** (transição list→detalhe, shared-element no hero,
CTA bar fixa mobile) — dinâmica por segmento (`_bloco_catalogo_motion` + `_seg_motion` +
`_SERVICOS_MOTION`), estilizada pelas vars de tema. **Não é mais mockup à parte:** o studio
(`/studio`) gera o motion junto do one-page institucional + T2 (@graph/FAQPage/sitemap/robots),
verificado gerando site de teste. Demos-prova gerados pelo motor: `p.jpos.com.br/demo-{odonto,
estetica,fisio,salao,psico}-motor/`. Preço nunca inventado — CTA de serviço abre o WhatsApp.
**Pendente:** restart do serviço `noemi-site-builder` (:8020) pra o studio no ar servir o código
novo (o já-gerado em `/var/www/sites` já reflete). Os `demo-*-motion` estáticos antigos seguem
no ar pra comparação até o JP decidir aposentá-los.

### Motion é DEFAULT DE FÁBRICA (não flag)
`_bloco_catalogo_motion` + `_MOTION_CSS` são chamados INCONDICIONALMENTE no `GeradorTemplate.gerar`
— não há flag/env pra escolher entre "motion premium" e "versão simples"; a versão simples não
existe. O único env é `SITE_GERADOR` (stub vs template), que o `/studio` (`builder_web.py`) já
fixa em `template` via `setdefault`. (O default cru do pipeline em `config.py` segue `stub`
DE PROPÓSITO — é o que os 37 testes usam; não mexer, não afeta o caminho do studio.)
Nicho fora dos 5 mapeados → fallback `_generico`, MESMO padrão visual, nunca regride/quebra
(verificado: petshop/advocacia/mecânica/vazio → 3 cards + overlay).

### ⚠️ As 5 demos-motor SÃO a referência de VENDA — NÃO sobrescrever sem confirmação do JP
`/var/www/sites/demo-{odonto,estetica,fisio,salao,psico}-motor/` são o padrão de referência
visual/estrutural do motor E a base que o JP edita à mão (nome/whatsapp/diferenciais por lead)
pra apresentar em call. **NÃO regenerar/apagar esses 5 slugs sem o JP confirmar.**
Seguro por padrão: o studio gera cada lead novo num slug NOVO (derivado de `nome_empresa` via
`_slug`), então não toca esses 5 — as edições manuais do JP só correm risco se alguém regenerar
exatamente esses slugs.
