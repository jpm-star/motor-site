# Pipeline de design do motor-site

## 1. Tooling (auditado 2026-07-27)
- **Fontes:** Google Fonts por-Tema (preconnect, display=swap, pares curados). ✅
- **Animação:** scroll-reveal (IntersectionObserver + spring + stagger + prefers-reduced-motion); aurora no hero; spotlight nos cards. ✅
- **Imagem:** Tier 1 é imageless (CSS/tipo/cor) → sem Sharp/Pillow. ✅ (revisitar só se um design pedir foto)
- **Ícones:** `app/icones.py` — 17 Lucide inline (currentColor, zero-dep). Wire quando o brief pedir.

## 2. Regra PERMANENTE: motion-gap → asset Higgsfield (`app/motion_gap.py`)
Diferencial da casa (a maioria dos sites-isca é estática). Quando a extração de
design (radar-visão) acha um efeito de movimento que o CSS comum **não** replica:
- **replicável** → o template faz nativo (lista `NATIVO`).
- **não replicável** → `prompt_higgsfield(efeito)` emite a **ordem de trabalho do asset**
  (prompt pronto + como incorporar via `<video autoplay muted loop>` com mix-blend).
  O asset vira **transição/feature real do produto**, não decoração.

Não força efeito feio nem pula silencioso — gera o prompt e segue.

## 3. Tema da casa: JPOS (dogfooding)
`_JPOS` em `app/design.py` — único tema de **fundo escuro + neon** (o "clichê #3" aqui
é IDENTIDADE intencional). Roteado no topo do `escolher_tema` (nichos jpos/ia/automação)
→ bypassa o guard anti-clichê. `acento_ink` (novo campo do Tema) dá texto escuro sobre
o neon (contraste do botão) — default branco pros temas de acento escuro.

## 4. Modo Camaleão self-serve (form → site automático)
O `montar_site(briefing)` já É o pipeline self-serve — o `briefing` é o formulário.

**Formulário que o dono preenche → vira `briefing`:**
| Campo do form | chave do briefing | obrigatório |
|---|---|---|
| Nome do negócio | `nome_empresa` | sim |
| Nicho/segmento | `nicho` | sim (escolhe o Tema) |
| WhatsApp | `whatsapp` | sim (CTA) |
| 3-4 diferenciais | `diferenciais` (lista) | sim |
| Público-alvo | `publico` | não (ajuda a copy) |
| Cor de marca (opcional) | `cor_primaria` | não |
| Cidade | `cidade` | não (SEO local) |

**Fluxo:** form → `briefing` (dict) → `montar_site()` → orquestrador (Groq) escreve a
copy → Tema define visual → deploy estático → URL. Zero código por cliente.

**Pra plugar o form self-serve (Tier 4 rodrigomirandola):** um endpoint que recebe
o POST do form, monta o `briefing` e chama `montar_site` — é a casca que falta
(o motor já faz o resto). Ver `apps/motor-isca-sites/builder_web.py` (casca web
existente que já dirige esse pipeline).

## Deploy
Default: estático em `SITE_OUT_DIR` (Caddy serve). **JPOS Tier 1 → jpos.com.br**
(hoje em 2.57.91.91, servidor separado): gerar aqui e publicar lá, ou repontar o
DNS. **p.jpos.com.br é reservado** pro futuro /obs-Jarvis — NÃO usar pro Tier 1.
