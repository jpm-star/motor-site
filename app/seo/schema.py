"""Tier 2 AEO/SEO — Schema.org JSON-LD (stdlib only, funções puras).

json_ld(negocio) -> str: <script type="application/ld+json"> com um @graph de
LocalBusiness + Organization + FAQPage. Answer Engine Optimization: dá pros
crawlers/LLMs a ficha estruturada do negócio e o FAQ como Question/Answer.
"""
import json


def json_ld(negocio: dict) -> str:
    """Recebe dict do negócio, devolve o <script> JSON-LD pronto pra <head>."""
    nome = negocio.get("nome", "")
    url = negocio.get("url", "")
    graph = [
        {
            "@type": "LocalBusiness",
            "name": nome,
            "telephone": negocio.get("whatsapp", ""),
            "url": url,
            "areaServed": negocio.get("cidade", ""),
            "address": {
                "@type": "PostalAddress",
                "streetAddress": negocio.get("endereco", ""),
                "addressLocality": negocio.get("cidade", ""),
                "addressRegion": negocio.get("uf", ""),
                "addressCountry": "BR",
            },
        },
        {
            "@type": "Organization",
            "name": nome,
            "url": url,
        },
        {
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item.get("q", ""),
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item.get("a", ""),
                    },
                }
                for item in negocio.get("faq", [])
            ],
        },
    ]
    payload = {"@context": "https://schema.org", "@graph": graph}
    # ensure_ascii=False mantém acento; </ escapado pra não fechar o <script> cedo.
    miolo = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return '<script type="application/ld+json">' + miolo + "</script>"


if __name__ == "__main__":
    negocio = {
        "nome": "Mármores & Cia",
        "nicho": "marmoraria",
        "cidade": "São Paulo",
        "uf": "SP",
        "whatsapp": "+5511999998888",
        "endereco": "Rua das Pedras, 100",
        "url": "https://marmores.example",
        "servicos": ["Bancadas", "Pias"],
        "faq": [
            {"q": "Fazem entrega?", "a": "Sim, em toda a Grande SP."},
            {"q": "Aceitam cartão?", "a": "Sim, até 12x."},
        ],
    }
    out = json_ld(negocio)
    assert out.startswith('<script type="application/ld+json">')
    assert out.endswith("</script>")
    miolo = out[len('<script type="application/ld+json">'):-len("</script>")]
    data = json.loads(miolo)
    assert "@graph" in data
    tipos = {node["@type"] for node in data["@graph"]}
    assert {"LocalBusiness", "Organization", "FAQPage"} <= tipos, tipos
    faq = next(n for n in data["@graph"] if n["@type"] == "FAQPage")
    assert faq["mainEntity"][0]["@type"] == "Question"
    assert faq["mainEntity"][0]["acceptedAnswer"]["@type"] == "Answer"
    assert faq["mainEntity"][0]["name"] == "Fazem entrega?"
    # </ não deve aparecer cru no miolo (proteção anti quebra de <script>)
    assert "</" not in miolo
    print("schema.py OK")
