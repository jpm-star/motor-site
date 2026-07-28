# DEPENDENCIAS.md — acoplamento físico + lições de arquitetura (motor-site)

Registro de acoplamento REAL e armadilhas descobertas (separado do log de decisões).
Mesma categoria do `NOEMI_DATA_DIR` do noemi-infra: coisa que se repete se não ficar escrita.

## Lição via dogfood (2026-07-28): campos descartados silenciosamente no pipeline
- **`briefing_de_cartucho` (app/cartucho.py) só mapeava um subconjunto do cartucho** —
  descartava `ancora_preco` e `prova_social` SEM avisar. Um cartucho podia ter preço e
  prova social e o site gerado saía sem nada disso. Descoberto gerando o site do PRÓPRIO
  JPOS (dogfood): o motor não aplicava padrões validados que estavam no cartucho.
- **Fix**: `briefing_de_cartucho` agora carrega `ancora_preco`/`prova_social`; `BriefingSite`
  (base.py) ganhou os campos; `template_real` renderiza seção de preço (`_bloco_preco`) e
  antes/depois (`_bloco_antes_depois`) — **só se o campo vier** (fallback gracioso).
- **Regra**: campo novo no cartucho que deve virar conteúdo precisa de 3 pontos alinhados —
  `briefing_de_cartucho` (carrega) → `BriefingSite` (transporta) → `template` (renderiza).
  Se qualquer um dos 3 não souber do campo, ele some sem erro. Sempre checar os 3.
- **Armadilha de tipo**: `prova_social` podia vir string OU lista; `.strip()` direto em lista
  explodia. `base.prova_social_texto()` normaliza (usado por llm_orquestrador e stub).

## Regressão (condição dura)
- Cartucho de cliente SEM `ancora_preco`/`prova_social` TEM que gerar igual a antes (sem
  seção de preço/antes-depois, sem erro). Teste: `tests/` da motor-site (37 passed) +
  regressão explícita (stub gera marmoraria sem os campos → sem `id="planos"`/`id="antes-depois"`).

## Providers (config.py, seam)
- `SITE_ORQUESTRADOR` = stub | llm (Groq direto, precisa GROQ_API_KEY/SITE_LLM_API_KEY).
- `SITE_GERADOR` = stub | template. `SITE_DEPLOY` = stub | local (escreve em `out/<slug>/`).
- `NOEMI_CARTUCHOS_DIR` = dir base dos cartuchos JSON (mesmo do shared-core do vídeo).
