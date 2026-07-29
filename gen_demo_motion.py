#!/usr/bin/env python3
"""Gerador de DEMO com motion 'grid de serviços → detalhe' (e-commerce style).

Bloco REUSÁVEL (TASK 1): template único, parametrizado por dataset. Pra um novo
segmento, adiciona um dict em DEMOS e roda — sai um index.html estático, sem build,
sem custo de IA. Publica em /var/www/sites/<slug>/ (servido em p.jpos.com.br/<slug>/).

Imagem: loremflickr (temática por keyword) com fallback picsum via onerror — nunca
mostra imagem quebrada numa call. WhatsApp: número do JP (demonstra o fluxo real na
call); troca por dataset quando virar cliente.

ponytail: standalone (não fiado no engine Python do motor). Fiar no template engine
é follow-up — sob pressão de call, HTML estático auto-contido é o caminho seguro.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

SAIDA = Path("/var/www/sites")
WA_DEMO = "5514998745847"  # número do JP — na call demonstra o WhatsApp real funcionando


def _card_img(keyword: str, lock: int, w: int = 600, h: int = 420) -> str:
    """URL de imagem temática (loremflickr) com fallback picsum embutido no onerror."""
    kw = keyword.replace(" ", ",")
    prim = f"https://loremflickr.com/{w}/{h}/{kw}?lock={lock}"
    fb = f"https://picsum.photos/seed/{kw}{lock}/{w}/{h}"
    return prim, fb


def _wa_link(negocio: str, servico: str) -> str:
    msg = f"Olá! Vim pelo site e queria agendar: {servico}. Pode me passar horários?"
    from urllib.parse import quote
    return f"https://wa.me/{WA_DEMO}?text={quote(msg)}"


def render(demo: dict) -> str:
    nome = demo["negocio"]
    servicos = demo["servicos"]
    cor = demo.get("cor", "#0ea5a4")
    cor2 = demo.get("cor2", "#155e63")
    tagline = demo.get("tagline", "Atendimento rápido, agendamento pelo WhatsApp")

    cards = []
    for i, s in enumerate(servicos):
        prim, fb = _card_img(s["img"], i + 1)
        cards.append(f"""
      <button class="card" data-i="{i}" aria-label="Ver {html.escape(s['nome'])}">
        <div class="thumb"><img loading="lazy" src="{prim}"
             onerror="this.onerror=null;this.src='{fb}'" alt="{html.escape(s['nome'])}"></div>
        <div class="cbody"><h3>{html.escape(s['nome'])}</h3>
          <span class="preco">{html.escape(s['preco'])}</span></div>
      </button>""")

    # dados dos serviços pro JS (detalhe)
    import json
    dados = []
    for i, s in enumerate(servicos):
        prim, fb = _card_img(s["img"], i + 1, 900, 620)
        dados.append({"nome": s["nome"], "desc": s["desc"], "preco": s["preco"],
                      "img": prim, "fb": fb, "wa": _wa_link(nome, s["nome"])})
    dados_js = json.dumps(dados, ensure_ascii=False)

    return f"""<!doctype html><html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(nome)}</title>
<style>
:root{{--c:{cor};--c2:{cor2};--ink:#12141a;--mut:#6b7280;--bg:#f7f8fa;--card:#fff;--line:#eceef2}}
*{{box-sizing:border-box;margin:0}}
body{{font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}}
header{{position:sticky;top:0;z-index:5;background:linear-gradient(120deg,var(--c),var(--c2));color:#fff;
  padding:16px 18px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 14px rgba(0,0,0,.12)}}
header h1{{font-size:1.15rem;font-weight:800;letter-spacing:.2px}}
header .tl{{font-size:.74rem;opacity:.9;font-weight:500}}
.wabtn{{background:#fff;color:var(--c2);border:0;border-radius:999px;padding:9px 15px;font-weight:700;
  font-size:.85rem;text-decoration:none;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.15)}}
.wrap{{max-width:940px;margin:0 auto;padding:20px 16px 60px}}
.lead{{color:var(--mut);font-size:.92rem;margin:6px 2px 20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(158px,1fr));gap:14px}}
.card{{border:1px solid var(--line);background:var(--card);border-radius:16px;overflow:hidden;cursor:pointer;
  text-align:left;padding:0;font:inherit;color:inherit;transition:transform .18s,box-shadow .18s}}
.card:hover{{transform:translateY(-4px);box-shadow:0 10px 26px rgba(0,0,0,.10)}}
.thumb{{aspect-ratio:4/3;overflow:hidden;background:#e5e7eb}}
.thumb img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform .3s}}
.card:hover .thumb img{{transform:scale(1.06)}}
.cbody{{padding:11px 13px 14px}}.cbody h3{{font-size:.98rem;font-weight:700}}
.preco{{display:inline-block;margin-top:5px;color:var(--c2);font-weight:800;font-size:.9rem}}
/* detalhe */
.detalhe{{position:fixed;inset:0;z-index:20;background:var(--bg);overflow-y:auto;
  opacity:0;visibility:hidden;transform:translateY(14px);transition:opacity .28s,transform .28s,visibility .28s}}
.detalhe.on{{opacity:1;visibility:visible;transform:none}}
.dhero{{position:relative;aspect-ratio:16/10;max-height:52vh;overflow:hidden;background:#e5e7eb}}
.dhero img{{width:100%;height:100%;object-fit:cover}}
.voltar{{position:absolute;top:14px;left:14px;background:rgba(0,0,0,.5);color:#fff;border:0;border-radius:999px;
  width:42px;height:42px;font-size:1.3rem;cursor:pointer;backdrop-filter:blur(4px)}}
.dbody{{max-width:680px;margin:0 auto;padding:22px 18px 40px}}
.dbody h2{{font-size:1.5rem;font-weight:800}}
.dprice{{color:var(--c2);font-weight:800;font-size:1.25rem;margin:8px 0 14px}}
.dbody p{{color:#374151;font-size:1.02rem}}
.ctas{{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px;position:sticky;bottom:0;
  background:linear-gradient(transparent,var(--bg) 22%);padding-top:18px}}
.cta{{flex:1;min-width:150px;text-align:center;padding:15px;border-radius:14px;font-weight:800;
  text-decoration:none;font-size:1rem}}
.cta.wa{{background:#25d366;color:#063}}.cta.ag{{background:var(--c);color:#fff}}
.badge{{display:inline-block;background:#eef2f7;color:var(--mut);font-size:.7rem;font-weight:700;
  padding:4px 9px;border-radius:999px;margin-bottom:10px;letter-spacing:.04em}}
footer{{text-align:center;color:var(--mut);font-size:.75rem;padding:24px}}
</style></head><body>
<header>
  <div><h1>{html.escape(nome)}</h1><div class="tl">{html.escape(tagline)}</div></div>
  <a class="wabtn" href="https://wa.me/{WA_DEMO}?text={html.escape('Olá! Vim pelo site e quero agendar.')}">💬 WhatsApp</a>
</header>
<div class="wrap">
  <p class="lead">Escolha o serviço para ver detalhes, valor e agendar na hora pelo WhatsApp.</p>
  <div class="grid">{''.join(cards)}</div>
</div>
<div class="detalhe" id="det" role="dialog" aria-modal="true">
  <div class="dhero"><button class="voltar" id="volta" aria-label="Voltar">←</button>
    <img id="dimg" src="" alt=""></div>
  <div class="dbody">
    <span class="badge">DEMONSTRAÇÃO</span>
    <h2 id="dnome"></h2><div class="dprice" id="dpreco"></div><p id="ddesc"></p>
    <div class="ctas">
      <a class="cta wa" id="dwa" href="#">💬 Agendar pelo WhatsApp</a>
      <a class="cta ag" id="dag" href="#">📅 Agendar horário</a>
    </div>
  </div>
</div>
<footer>Feito com Motor Site — JPOS · demonstração</footer>
<script>
const D={dados_js};
const det=document.getElementById('det'),volta=document.getElementById('volta');
function abrir(i){{const s=D[i];
  document.getElementById('dimg').src=s.img;
  document.getElementById('dimg').onerror=function(){{this.onerror=null;this.src=s.fb}};
  document.getElementById('dnome').textContent=s.nome;
  document.getElementById('dpreco').textContent=s.preco;
  document.getElementById('ddesc').textContent=s.desc;
  document.getElementById('dwa').href=s.wa;
  document.getElementById('dag').href=s.wa;
  det.classList.add('on');det.scrollTop=0;document.body.style.overflow='hidden';}}
function fechar(){{det.classList.remove('on');document.body.style.overflow='';}}
document.querySelectorAll('.card').forEach(c=>c.onclick=()=>abrir(+c.dataset.i));
volta.onclick=fechar;
document.addEventListener('keydown',e=>{{if(e.key==='Escape')fechar()}});
</script>
</body></html>"""


# ── Datasets (troca itens/fotos por segmento; preço/desc placeholder editável) ──
DEMOS = {
    "demo-odonto-motion": {
        "negocio": "[Nome do Consultório]", "cor": "#0ea5a4", "cor2": "#155e63",
        "tagline": "Odontologia · agende sua avaliação pelo WhatsApp",
        "servicos": [
            {"nome": "Limpeza e Profilaxia", "preco": "a partir de R$ 120", "img": "dental,cleaning",
             "desc": "Remoção de placa e tártaro, polimento e orientação de higiene. Sensação de boca nova e prevenção de cáries e gengivite."},
            {"nome": "Clareamento Dental", "preco": "a partir de R$ 690", "img": "teeth,whitening,smile",
             "desc": "Clareamento profissional com acompanhamento. Resultado visível em poucas sessões, sem agredir o esmalte."},
            {"nome": "Implante Dentário", "preco": "avaliação gratuita", "img": "dental,implant",
             "desc": "Reposição de dente perdido com implante fixo, aparência e mastigação naturais. Planejamento individualizado."},
            {"nome": "Aparelho / Ortodontia", "preco": "consulte condições", "img": "braces,orthodontics",
             "desc": "Correção do alinhamento com aparelho fixo ou alinhador transparente. Sorriso mais bonito e mordida saudável."},
            {"nome": "Tratamento de Canal", "preco": "a partir de R$ 450", "img": "dentist,treatment",
             "desc": "Alívio da dor e recuperação do dente comprometido com técnica atual e menos desconforto."},
            {"nome": "Avaliação Inicial", "preco": "gratuita", "img": "dentist,consultation",
             "desc": "Diagnóstico completo e plano de tratamento sem compromisso. Agende agora e tire suas dúvidas."},
        ]},
    "demo-estetica-motion": {
        "negocio": "[Nome da Clínica]", "cor": "#c026d3", "cor2": "#701a75",
        "tagline": "Estética & Dermato · realce sua beleza natural",
        "servicos": [
            {"nome": "Limpeza de Pele", "preco": "a partir de R$ 150", "img": "facial,skincare",
             "desc": "Limpeza profunda com extração e hidratação. Pele mais limpa, macia e livre de cravos."},
            {"nome": "Botox / Toxina", "preco": "a partir de R$ 590", "img": "beauty,face,treatment",
             "desc": "Suaviza linhas de expressão com naturalidade. Aplicação por profissional, resultado que respeita seus traços."},
            {"nome": "Preenchimento", "preco": "consulte", "img": "aesthetics,skincare",
             "desc": "Restaura volume e contorno do rosto com ácido hialurônico. Efeito natural e imediato."},
            {"nome": "Peeling / Rejuvenescimento", "preco": "a partir de R$ 220", "img": "spa,facial",
             "desc": "Renova a pele, atenua manchas e marcas. Viço e uniformidade em sessões progressivas."},
            {"nome": "Depilação a Laser", "preco": "pacotes a partir de R$ 99", "img": "laser,beauty",
             "desc": "Redução duradoura dos pelos com conforto. Pele lisa sem o incômodo da depilação recorrente."},
            {"nome": "Avaliação Estética", "preco": "gratuita", "img": "beauty,consultation",
             "desc": "Análise personalizada e plano de cuidados sob medida. Agende sua avaliação sem compromisso."},
        ]},
    "demo-fisio-motion": {
        "negocio": "[Nome da Clínica]", "cor": "#2563eb", "cor2": "#1e3a8a",
        "tagline": "Fisioterapia · movimento sem dor, agende avaliação",
        "servicos": [
            {"nome": "Avaliação Fisioterapêutica", "preco": "a partir de R$ 130", "img": "physiotherapy",
             "desc": "Diagnóstico funcional completo do seu quadro e definição do plano de tratamento individual."},
            {"nome": "Fisioterapia Ortopédica", "preco": "sessão a partir de R$ 110", "img": "physiotherapy,rehab",
             "desc": "Recuperação de lesões, pós-cirúrgico e dores articulares com técnicas manuais e exercícios."},
            {"nome": "RPG / Postural", "preco": "consulte pacotes", "img": "posture,stretching",
             "desc": "Reeducação postural que alivia dores nas costas e melhora o alinhamento do corpo."},
            {"nome": "Pilates Clínico", "preco": "planos mensais", "img": "pilates",
             "desc": "Fortalecimento e mobilidade com acompanhamento profissional. Menos dor, mais disposição."},
            {"nome": "Fisioterapia Esportiva", "preco": "consulte", "img": "sports,rehab",
             "desc": "Prevenção e recuperação de lesões para quem treina. Volte ao esporte com segurança."},
            {"nome": "Agende sua Avaliação", "preco": "gratuita", "img": "physiotherapy,clinic",
             "desc": "Primeira conversa sem compromisso para entender sua dor e como podemos ajudar."},
        ]},
    "demo-salao-motion": {
        "negocio": "[Nome do Salão]", "cor": "#b45309", "cor2": "#7c2d12",
        "tagline": "Salão & Beleza · agende seu horário pelo WhatsApp",
        "servicos": [
            {"nome": "Corte Feminino", "preco": "a partir de R$ 70", "img": "haircut,salon",
             "desc": "Corte personalizado ao seu rosto e estilo, com finalização. Saia daqui se sentindo renovada."},
            {"nome": "Coloração / Mechas", "preco": "a partir de R$ 190", "img": "hair,color,salon",
             "desc": "Cor, luzes e mechas com produtos de qualidade. Tom uniforme e brilho que dura."},
            {"nome": "Escova & Progressiva", "preco": "consulte", "img": "hairstyle,blowout",
             "desc": "Fios alinhados, macios e sem frizz. Praticidade no dia a dia com acabamento profissional."},
            {"nome": "Tratamento / Hidratação", "preco": "a partir de R$ 90", "img": "hair,treatment,spa",
             "desc": "Reconstrução e nutrição dos fios danificados. Cabelo mais forte, saudável e brilhante."},
            {"nome": "Manicure & Pedicure", "preco": "a partir de R$ 55", "img": "manicure,nails",
             "desc": "Unhas bem-feitas e duradouras, com higiene e capricho. Mãos e pés impecáveis."},
            {"nome": "Dia da Noiva / Pacotes", "preco": "sob consulta", "img": "bride,makeup,salon",
             "desc": "Penteado, maquiagem e cuidados completos para o seu dia especial. Reserve com antecedência."},
        ]},
    "demo-psico-motion": {
        "negocio": "[Nome do Consultório]", "cor": "#0d9488", "cor2": "#134e4a",
        "tagline": "Psicologia · acolhimento e cuidado, agende sua sessão",
        "servicos": [
            {"nome": "Terapia Individual", "preco": "sessão a partir de R$ 150", "img": "therapy,counseling",
             "desc": "Espaço seguro para cuidar da ansiedade, estresse e questões pessoais, no seu ritmo."},
            {"nome": "Terapia de Casal", "preco": "a partir de R$ 220", "img": "couple,counseling",
             "desc": "Mediação para melhorar a comunicação e reconstruir a relação com apoio profissional."},
            {"nome": "Atendimento Online", "preco": "a partir de R$ 130", "img": "online,therapy",
             "desc": "Sessões por vídeo, com o mesmo acolhimento, de onde você estiver."},
            {"nome": "Psicologia Infantil", "preco": "consulte", "img": "child,psychology",
             "desc": "Acompanhamento lúdico e cuidadoso para o desenvolvimento emocional das crianças."},
            {"nome": "Orientação / 1ª Conversa", "preco": "acolhimento gratuito", "img": "counseling,talk",
             "desc": "Primeiro contato sem compromisso para entender sua necessidade e como posso ajudar."},
        ]},
}


def main(slugs: list[str] | None = None) -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    alvos = slugs or list(DEMOS)
    for slug in alvos:
        demo = DEMOS[slug]
        d = SAIDA / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render(demo), encoding="utf-8")
        print(f"https://p.jpos.com.br/{slug}/")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
