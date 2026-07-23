# TESTE.md — roteiro de teste (copiar, colar, olhar)

Rode na ordem. Cada bloco é copiar → colar no terminal → olhar o resultado.
Não precisa entender o código. **Comece pelo Passo 0.**

> Legenda: 🟢 roda sem nada extra · 🔑 precisa da chave Higgsfield viva (vai falhar de propósito hoje — está em MOCK).
> A chave do Groq (áudio/IA) já está configurada; esses testes rodam normal.

---

## Passo 0 — pôr os dois repos na branch certa (rode 1 vez)

```bash
cd /root/motor-site && git checkout feat/conversao && cd /root/noemi-infra && git checkout feat/conversao-cartucho
```

**Você deve ver:** `Switched to branch 'feat/conversao'` e depois `... 'feat/conversao-cartucho'` (ou "Already on").
**Se der errado** (erro de branch): me manda a saída — a branch pode não ter sido criada.

---

## 1 🟢 Nada quebrou — Motor Site (rápido, ~2s)

```bash
cd /root/motor-site && python3 -m pytest -q
```

**Você deve ver:** uma linha verde tipo `37 passed`.
**Se der errado** (`failed`/vermelho): algo do site quebrou — vá pra seção "Se quebrar" no fim.

## 2 🟢 Nada quebrou — Motor B / vídeo (~45s)

```bash
cd /root/noemi-infra && .venv/bin/python -m pytest apps/motor-b-video/tests/ -q
```

**Você deve ver:** `66 passed, 1 skipped`.
**Se der errado:** o motor de vídeo quebrou — seção "Se quebrar".

## 3 🟢 Health de todos os motores

```bash
echo "Motor B:"; curl -s http://localhost:8010/health; echo; echo "Painéis:"; systemctl is-active noemi-motor-b noemi-painel noemi-operador noemi-papai
```

**Você deve ver:** `{"ok":true,"mock":true}` no Motor B e vários `active` nos painéis.
**Se der errado** (`inactive`/`failed`/sem resposta): esse motor está fora do ar — seção "Se quebrar".

---

## 4 🟢 Cartucho de cliente → site pronto

```bash
cd /root/motor-site && NOEMI_CARTUCHOS_DIR=/root/sdr-motor/backend/cartuchos python3 -c "from app import cartucho, pipeline; b=cartucho.briefing_de_cartucho('marmoraria'); print('CLIENTE:', b['nome_empresa'], '| CIDADE:', b['cidade'], '| SERVIÇO:', b['servico_principal']); print('SLUG DO SITE:', pipeline.montar_site(b).deploy.deploy_id)"
```

**Você deve ver:** `CLIENTE: Marmoraria Exemplo | CIDADE: São Paulo - Zona Norte | SERVIÇO: granito` e um `SLUG DO SITE:`.
**Se der errado:** o cartucho não virou site — me manda a saída.

## 5 🟢 Título + JSON-LD com a cidade (SEO local)

```bash
cd /root/motor-site && python3 -c "
from app.providers.base import BriefingSite
from app.providers.template_real import GeradorTemplate
b=BriefingSite(nome_empresa='Marmoraria Silva',nicho='Marmoraria',headline='h',subheadline='Bancadas sob medida',secoes=[{'titulo':'A','corpo':'b'}],cta_texto='Orçamento',cta_contato='5519998887777',cidade='Campinas',servico_principal='granito')
html=GeradorTemplate().gerar(b,'demo').arquivos['index.html']
import re
print('TÍTULO:', re.search(r'<title>(.*?)</title>',html).group(1))
print('TEM JSON-LD LocalBusiness:', 'LocalBusiness' in html)
"
```

**Você deve ver:** `TÍTULO: Marmoraria em Campinas | Marmoraria Silva` e `TEM JSON-LD LocalBusiness: True`.
**Se der errado** (título sem "em Campinas" ou JSON-LD False): o SEO não aplicou.

## 6 🟢 CTA do WhatsApp pré-preenchido com o serviço

```bash
cd /root/motor-site && python3 -c "
from app.providers.base import BriefingSite
from app.providers.template_real import GeradorTemplate
b=BriefingSite(nome_empresa='Marmoraria Silva',nicho='Marmoraria',headline='h',subheadline='s',secoes=[{'titulo':'A','corpo':'b'}],cta_texto='Orçamento',cta_contato='5519998887777',cidade='Campinas',servico_principal='granito')
html=GeradorTemplate().gerar(b,'demo').arquivos['index.html']
print('LINK DO ZAP TEM \"Quero orçamento de granito\":', 'Quero%20or' in html and 'granito' in html)
print('TEM BOTÃO FLUTUANTE:', 'zap-fixo' in html)
"
```

**Você deve ver:** as duas linhas com `True`.
**Se der errado:** o CTA não pegou o serviço do cartucho.

## 7 🟢 Lote de demos (vários prospects de uma vez)

```bash
cd /root/motor-site && printf 'nome_empresa,nicho,cidade,whatsapp,servico_principal\nMarmoraria Silva,Marmoraria,Campinas,5519998887777,granito\nClinica Bem Estar,Clinica de estetica,Valinhos,5519991112222,harmonizacao\n' > /tmp/prospects.csv && python3 -m app.batch_demos /tmp/prospects.csv --out /tmp/demos && echo "--- abra este arquivo no navegador: ---" && echo /tmp/demos/demo-marmoraria-silva/index.html
```

**Você deve ver:** `[1/2] OK ...`, `[2/2] OK ...`, `=== lote: 2 OK, 0 falha(s) ===`, e um caminho de arquivo no fim.
**Se der errado** (algum `FALHA`): me manda a saída — mas repare que UMA falha não derruba o lote (é de propósito).

## 8 🟢 Auditor de prospect (score → tier → diagnóstico)

```bash
cd /root/motor-site && printf 'nome,url\nMarmoraria Sem Site,\nConcorrente,https://example.com\n' > /tmp/audit.csv && python3 -m app.auditor /tmp/audit.csv --out /tmp/auditoria.md && echo "--- relatório: ---" && cat /tmp/auditoria.md
```

**Você deve ver:** `Marmoraria Sem Site: score 0 → Tier 1`, `Concorrente: score 34 → Tier 2`, e uma tabela com diagnóstico escrito.
**Se der errado** (erro de rede em TODOS): o VPS pode estar sem saída pra internet — me manda a saída.

## 9 🟢 Áudio → cartucho (transcreve a fala do dono e monta o cartucho)

Isto testa a extração (a parte de IA) com uma fala de exemplo:

```bash
cd /root/motor-site && python3 -c "
from app import audio_cartucho as ac
import json
cart = ac.extrair('Aqui é da Marmoraria Silva, trabalho com granito e quartzo, atendo Campinas, zap 19 99888-7777, visita técnica grátis, abro de segunda a sábado das 8 às 18.', ac._chave())
print(json.dumps(cart, ensure_ascii=False, indent=2))
print('FALTANDO:', ac.faltando(cart))
"
```

**Você deve ver:** um JSON com `nome_empresa: Marmoraria Silva`, `escopo: granito, quartzo`, etc., e `FALTANDO: ['politica_preco']` (ele NÃO inventou o que você não falou).
**Se der errado** (erro 403/timeout): a chave do Groq caiu — me manda a saída.
Para testar com um áudio REAL do WhatsApp: `cd /root/motor-site && python3 -m app.audio_cartucho /caminho/do/audio.ogg`

## 10 🟢 Vídeo com ficha do imóvel + PACOTE de entrega

> Roda o Motor B com o código NOVO em memória (não mexe no :8010 em produção — esse só terá
> as novidades quando você redeployar). É MOCK: o vídeo é um padrão de teste, mas prova o
> overlay do imóvel, o CTA com código e o pacote de entrega — sem gastar Higgsfield.
> Copie o bloco INTEIRO (é uma coisa só). O aviso "StarletteDeprecationWarning" é inofensivo, ignore.

```bash
cd /root/noemi-infra/apps/motor-b-video && NOEMI_DATA_DIR=$(mktemp -d) MOCK_DELAY_S=0 WORKER_POLL_S=0.05 PYTHONPATH=/root/noemi-infra/packages:. /root/noemi-infra/.venv/bin/python -c "
import base64, time, json
from fastapi.testclient import TestClient
from main import app
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
with TestClient(app) as c:
    aid=c.post('/api/upload',files={'file':('i.png',PNG,'image/png')},data={'owner':'teste'}).json()['asset_id']
    jid=c.post('/api/jobs',json={'asset_id':aid,'config':{'codigo':'AP-12','preco':'R\$ 850 mil','bairro':'Cambui','descricao':'3 quartos vista mar'}}).json()['job_id']
    j={}
    for _ in range(60):
        j=c.get(f'/api/jobs/{jid}').json()
        if j['estado'] in ('completed','failed'): break
        time.sleep(0.2)
    print('JOB:', j['estado'])
    print('===== PACOTE DE ENTREGA =====')
    print(json.dumps(c.get(f\"/api/assets/{j['asset_video']}/pacote\").json(), ensure_ascii=False, indent=2))
"
```

**Você deve ver:** `JOB: completed` e um JSON `PACOTE DE ENTREGA` com `titulo`, `hashtags` (lista),
`cta` citando **AP-12**, `copy` (legenda pronta pro post) e `ficha` com preço/bairro/código.
**Se der errado** (`JOB: failed` ou erro Python): o motor de vídeo quebrou — seção "Se quebrar".

## 11 🔑 Vídeo REAL (Higgsfield) — vai falhar de propósito hoje

Hoje o Motor B está em MOCK (vídeo é padrão de teste). Para vídeo real você precisa da **chave Higgsfield viva** e subir com `MOCK_MODE=false`. **Sem a chave, este teste falha de propósito** — não é bug. Deixe pra quando for ligar o Higgsfield.

---

## Se quebrar, me manda isso

Rode os 3 e cola a saída aqui:

```bash
# 1) Motor B está de pé e responde?
curl -s http://localhost:8010/health; echo; systemctl status noemi-motor-b --no-pager -n 15
```

```bash
# 2) Primeiro teste que falhou no motor de vídeo (para no 1º erro)
cd /root/noemi-infra && .venv/bin/python -m pytest apps/motor-b-video/tests/ -x -q 2>&1 | tail -30
```

```bash
# 3) Log recente do Motor B + em que commit cada repo está
journalctl -u noemi-motor-b --no-pager -n 40; echo "--- motor-site:"; git -C /root/motor-site log --oneline -3; echo "--- noemi-infra:"; git -C /root/noemi-infra log --oneline -3
```
