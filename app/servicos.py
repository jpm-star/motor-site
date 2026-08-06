"""O que ESTE segmento realmente vende — e que foto combina com isso.

RAIZ DO ERRO CRÍTICO #4 (auditoria Rações & Cia, 2026-08-05): `_SERVICOS_MOTION` era um
dicionário fechado de 5 segmentos (odonto/estética/fisio/salão/psico). Pet shop não
estava lá, caía em `_generico` e o site saía com "Atendimento / Orçamento /
Acompanhamento" ilustrados por `service,professional` — foto de reunião de escritório
num pet shop. Não era falta de conteúdo: era um dicionário fingindo ser um catálogo.

Inversão: a curadoria humana continua sendo o caminho rápido (5 segmentos revisados à
mão vencem qualquer LLM), mas deixou de ser a ÚNICA fonte. Segmento desconhecido vai
pro LLM, que devolve serviço + descrição + palavra-chave de foto, e o resultado fica em
cache no disco — pet shop custa uma chamada na vida, não uma por site.

Ordem: curadoria → cache → LLM → genérico (só se tudo falhar; nunca quebra a geração).
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

log = logging.getLogger(__name__)

# Curadoria humana. Revisados um a um; vencem o LLM sempre que o segmento bate.
CURADOS: dict[str, list[tuple[str, str, str]]] = {
    "odonto": [
        ("Avaliação", "Consulta pra diagnóstico e plano de tratamento, sem compromisso.", "dentist,consultation"),
        ("Limpeza e Profilaxia", "Remoção de placa e tártaro, polimento e orientação de higiene.", "dental,cleaning"),
        ("Clareamento", "Clareamento profissional com acompanhamento — sorriso mais branco.", "teeth,whitening,smile"),
        ("Implante", "Reposição de dente com implante fixo, aparência e mastigação naturais.", "dental,implant"),
        ("Ortodontia", "Aparelho fixo ou alinhador transparente pra alinhar o sorriso.", "braces,orthodontics"),
    ],
    "estetica": [
        ("Avaliação Estética", "Análise personalizada e plano de cuidados sob medida.", "beauty,consultation"),
        ("Limpeza de Pele", "Limpeza profunda com extração e hidratação.", "facial,skincare"),
        ("Botox / Toxina", "Suaviza linhas de expressão com naturalidade.", "beauty,face,treatment"),
        ("Preenchimento", "Restaura volume e contorno do rosto com ácido hialurônico.", "aesthetics,skincare"),
        ("Depilação a Laser", "Redução duradoura dos pelos com conforto.", "laser,beauty"),
    ],
    "fisio": [
        ("Avaliação Fisioterapêutica", "Diagnóstico funcional e plano de tratamento individual.", "physiotherapy"),
        ("Fisioterapia Ortopédica", "Recuperação de lesões, pós-cirúrgico e dores articulares.", "physiotherapy,rehab"),
        ("RPG / Postural", "Reeducação postural que alivia dores nas costas.", "posture,stretching"),
        ("Pilates Clínico", "Fortalecimento e mobilidade com acompanhamento profissional.", "pilates"),
    ],
    "salao": [
        ("Corte", "Corte personalizado ao seu rosto e estilo, com finalização.", "haircut,salon"),
        ("Coloração / Mechas", "Cor, luzes e mechas com brilho que dura.", "hair,color,salon"),
        ("Tratamento / Hidratação", "Reconstrução e nutrição dos fios danificados.", "hair,treatment,spa"),
        ("Manicure & Pedicure", "Unhas bem-feitas e duradouras, com capricho.", "manicure,nails"),
    ],
    "psico": [
        ("Terapia Individual", "Espaço seguro pra cuidar da ansiedade, estresse e questões pessoais.", "therapy,counseling"),
        ("Terapia de Casal", "Mediação pra melhorar a comunicação e a relação.", "couple,counseling"),
        ("Atendimento Online", "Sessões por vídeo, com o mesmo acolhimento, de onde você estiver.", "online,therapy"),
    ],
    # Os quatro abaixo entraram pela auditoria: são os segmentos com mais leads na base
    # (pet shop 99, advocacia 90, imobiliária 83, academia 83, oficina 81) e não podiam
    # seguir dependendo de uma chamada de LLM pra sair certo.
    "petshop": [
        ("Banho e Tosa", "Banho, tosa higiênica ou na tesoura, com secagem e hidratação.", "dog,grooming,bath"),
        ("Ração e Alimentação", "Ração seca, úmida e petisco — marcas que a gente usa e indica.", "pet,food,store"),
        ("Consulta Veterinária", "Atendimento clínico, vacina e vermífugo em dia.", "veterinary,clinic,dog"),
        ("Acessórios e Higiene", "Coleira, cama, brinquedo, antipulgas e o que mais o bicho precisa.", "pet,shop,accessories"),
    ],
    "academia": [
        ("Musculação", "Treino montado pro seu objetivo, com acompanhamento na sala.", "gym,weights,training"),
        ("Avaliação Física", "Medidas, composição corporal e meta clara antes de começar.", "fitness,assessment"),
        ("Aulas Coletivas", "Funcional, spinning, dança — energia de treinar junto.", "group,fitness,class"),
        ("Personal Trainer", "Acompanhamento individual, do aquecimento à última série.", "personal,trainer,gym"),
    ],
    "advocacia": [
        ("Consulta Jurídica", "Análise do seu caso e as opções reais, sem juridiquês.", "lawyer,office,consultation"),
        ("Direito Trabalhista", "Rescisão, verbas, processo — do cálculo à audiência.", "law,justice,scales"),
        ("Direito de Família", "Divórcio, guarda, pensão e inventário com discrição.", "family,law,documents"),
        ("Acompanhamento Processual", "Você sabe em que pé está o processo, sem ter que cobrar.", "legal,documents,office"),
    ],
    "imobiliaria": [
        ("Compra e Venda", "Da visita à escritura, com a documentação conferida.", "real,estate,house,keys"),
        ("Locação", "Imóvel alugado com contrato, vistoria e garantia resolvidos.", "apartment,rental,interior"),
        ("Avaliação de Imóvel", "Quanto vale o seu, com base no que de fato vendeu na região.", "house,evaluation,documents"),
        ("Administração de Aluguel", "A gente cuida do repasse, do reajuste e da cobrança.", "property,management,building"),
    ],
    "oficina": [
        ("Revisão Completa", "Checagem ponto a ponto — você sai sabendo o estado do carro.", "car,mechanic,inspection"),
        ("Troca de Óleo e Filtros", "Óleo, filtros e fluidos no prazo certo, sem enrolação.", "car,oil,change"),
        ("Freios e Suspensão", "Pastilha, disco, amortecedor — o que segura o carro na estrada.", "car,brakes,repair"),
        ("Diagnóstico Eletrônico", "Scanner na injeção pra achar a causa, não chutar a peça.", "car,diagnostic,scanner"),
    ],
    "contabilidade": [
        ("Abertura de Empresa", "CNPJ, alvará e enquadramento — pronto pra faturar.", "accounting,office,documents"),
        ("Contabilidade Mensal", "Guias, folha e obrigações entregues no prazo, todo mês.", "accounting,calculator,desk"),
        ("Imposto de Renda", "Declaração conferida, com o que dá pra deduzir de verdade.", "tax,documents,finance"),
        ("Consultoria Tributária", "Regime certo pro seu porte — quase sempre dá pra pagar menos.", "business,consulting,meeting"),
    ],
}

GENERICO: list[tuple[str, str, str]] = [
    ("Atendimento", "Atendimento próximo e sem enrolação, do jeito que você precisa.", "service,professional"),
    ("Orçamento", "Chame no WhatsApp e receba os valores antes de fechar qualquer coisa.", "consultation,meeting"),
    ("Acompanhamento", "A gente acompanha do início à entrega, no prazo combinado.", "support,office"),
]

# Cada entrada: (chave do CURADOS, termos que a identificam). Ordem IMPORTA — "salão de
# beleza" tem que bater em salão antes de estética, senão "beleza" o rouba.
_SINONIMOS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("odonto", ("odonto", "dent", "implant", "ortodont", "sorri")),
    ("fisio", ("fisio", "physio", "pilates", "rpg")),
    ("salao", ("salão", "salao", "cabel", "hair", "manicure", "barbe", "barber")),
    ("estetica", ("estét", "estet", "harmoniz", "facial", "beleza", "botox", "derm", "aesthetic")),
    ("psico", ("psico", "terap", "psychol")),
    # "ração" precisa das 4 formas: o nome que chega é "Rações e Cia" (plural), e o
    # radical curto "raç" pegaria "coração" — cardiologia virando pet shop.
    ("petshop", ("pet", "ração", "racao", "rações", "racoes", "veterin", "tosa",
                 "agropec", "animal")),
    ("academia", ("academia", "gym", "crossfit", "fitness", "musculação", "musculacao")),
    ("advocacia", ("advocac", "advogad", "jurídic", "juridic", "law")),
    ("imobiliaria", ("imobiliár", "imobiliar", "corretor", "imóve", "imove", "real estate")),
    ("oficina", ("oficina", "mecânic", "mecanic", "auto center", "autocenter", "funilar")),
    ("contabilidade", ("contábil", "contabil", "contador", "escritório de contab")),
)


def chave_curada(nicho: str) -> str:
    """A chave de `CURADOS` que este nicho casa, ou "" se nenhuma.

    Devolver "" em vez de "_generico" é a mudança de comportamento: antes, TODO nicho
    desconhecido recebia um match falso com o genérico e nunca chegava ao LLM.

    O casamento é por INÍCIO DE PALAVRA, não por substring solta. Com `in` puro,
    "clínica do coração" virava pet shop — co-"ração" — e uma cardiologia receberia um
    site de banho e tosa. Os termos são radicais de propósito ("veterin" pega
    veterinária/veterinário), e o \\b garante que o radical comece a palavra."""
    n = (nicho or "").lower()
    return next((k for k, termos in _SINONIMOS
                 if any(re.search(r"\b" + re.escape(t), n) for t in termos)), "")


# ── cache ────────────────────────────────────────────────────────────────────────
def _caminho_cache() -> Path:
    return Path(os.environ.get(
        "SERVICOS_CACHE", str(Path(__file__).resolve().parent.parent / "data" / "servicos_segmento.json")))


def _slug(nicho: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (nicho or "").lower()).strip("-") or "generico"


def _ler_cache() -> dict:
    p = _caminho_cache()
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    except (OSError, ValueError):
        return {}


def _gravar_cache(chave: str, itens: list[tuple[str, str, str]]) -> None:
    p = _caminho_cache()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        d = _ler_cache()
        d[chave] = [list(i) for i in itens]
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        log.warning("não consegui gravar o cache de serviços em %s", p)


# ── LLM ──────────────────────────────────────────────────────────────────────────
_SYS = (
    "Você conhece o comércio e os serviços de bairro no Brasil. Recebe o SEGMENTO de um "
    "negócio e devolve o que esse negócio REALMENTE vende — os itens que o dono colocaria "
    "na vitrine, não categorias abstratas. PROIBIDO: 'Atendimento', 'Orçamento', "
    "'Acompanhamento', 'Qualidade', 'Consultoria' e qualquer nome que sirva pra qualquer "
    "ramo. PROIBIDO inventar preço, prazo ou número. A descrição fala com o CLIENTE do "
    "negócio (não com o dono) em 1 frase concreta, sem clichê de marketing.\n"
    "Responda SOMENTE JSON: {\"itens\":[{\"nome\":\"...\",\"desc\":\"...\",\"foto\":\"...\"}]} "
    "com 4 a 5 itens. O campo \"foto\" são 2-3 palavras EM INGLÊS separadas por vírgula "
    "que achem uma foto real desse serviço num banco de imagens (ex.: 'dog,grooming,bath'). "
    "Nunca use 'service', 'professional', 'business' ou 'office' sozinhos."
)


def _do_llm(nicho: str) -> list[tuple[str, str, str]]:
    """Pergunta ao LLM. Levanta em qualquer falha — quem chama decide o fallback."""
    from .providers.llm_orquestrador import _chave, _groq_json  # cascata do gateway
    d = _groq_json(_SYS, f"SEGMENTO: {nicho}", _chave(), temperatura=0.4)
    itens = []
    for it in (d.get("itens") or [])[:5]:
        nome, desc = str(it.get("nome", "")).strip(), str(it.get("desc", "")).strip()
        foto = re.sub(r"[^a-z, ]", "", str(it.get("foto", "")).lower()).replace(" ", "")
        if nome and desc and foto:
            itens.append((nome, desc, foto))
    if len(itens) < 3:
        raise ValueError(f"LLM devolveu {len(itens)} itens úteis para {nicho!r}")
    return itens


def servicos_do_segmento(nicho: str) -> list[tuple[str, str, str]]:
    """(nome, descrição, palavra-chave de foto) do que este segmento vende.

    Nunca levanta: o pior caso é o genérico de antes, e site com seção genérica é melhor
    que geração quebrada. Mas o genérico agora é o ÚLTIMO recurso, não o segundo."""
    if k := chave_curada(nicho):
        return CURADOS[k]
    chave = _slug(nicho)
    if em_cache := _ler_cache().get(chave):
        return [tuple(i) for i in em_cache if len(i) == 3]
    try:
        itens = _do_llm(nicho)
    except Exception as e:  # noqa: BLE001 — sem chave, gateway fora, JSON ruim
        log.warning("serviços de %r pelo LLM falharam (%s); caindo no genérico", nicho, e)
        return GENERICO
    _gravar_cache(chave, itens)
    return itens


if __name__ == "__main__":  # self-check sem rede
    os.environ["SERVICOS_CACHE"] = "/tmp/_sv_selfcheck.json"
    Path("/tmp/_sv_selfcheck.json").unlink(missing_ok=True)
    assert chave_curada("pet shop") == "petshop", "pet shop caía no genérico — o bug"
    assert chave_curada("Salão de Beleza") == "salao", "beleza não pode roubar salão"
    assert chave_curada("clínica de estética") == "estetica"
    assert chave_curada("Rações e Cia") == "petshop"
    assert chave_curada("escritório de advocacia") == "advocacia"
    assert chave_curada("padaria artesanal") == "", "desconhecido tem que ir pro LLM"
    # segmento desconhecido + LLM indisponível => genérico, sem levantar. Precisa matar
    # os DOIS caminhos: o gateway responde mesmo sem GROQ_API_KEY (é ele quem tem as
    # chaves), então zerar só a chave deixava o self-check batendo em rede de verdade.
    os.environ["GROQ_API_KEY"] = ""
    os.environ["LITELLM_BASE"] = "http://127.0.0.1:9"  # porta descartável: recusa na hora
    import app.providers.llm_orquestrador as _llm
    _llm._GATEWAY_URL = "http://127.0.0.1:9/v1/chat/completions"
    assert servicos_do_segmento("padaria artesanal") == GENERICO
    # e o cache: grava e lê de volta sem tocar no LLM
    _gravar_cache("padaria-artesanal", [("Pão na hora", "Sai do forno de duas em duas horas.", "bakery,bread")])
    assert servicos_do_segmento("padaria artesanal")[0][0] == "Pão na hora"
    assert all(len(i) == 3 for v in CURADOS.values() for i in v)
    proibido = {"atendimento", "orçamento", "acompanhamento"}
    assert not [n for k, v in CURADOS.items() for n, _, _ in v if n.lower() in proibido]
    Path("/tmp/_sv_selfcheck.json").unlink(missing_ok=True)
    print(f"servicos OK — {len(CURADOS)} segmentos curados, "
          f"{sum(len(v) for v in CURADOS.values())} itens, LLM+cache pro resto")
