"""Tier 2 AEO/SEO — QA PageSpeed pontual (estático, sem rede).

Funções puras, stdlib só. `auditar(html)` roda um checklist de boas práticas
que impactam LCP/CLS e indexação, sem chamar a API do PageSpeed.
"""
from html.parser import HTMLParser


class _Colheita(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tem_title = False
        self._em_title = False
        self.title_texto = ""
        self.tem_meta_desc = False
        self.tem_viewport = False
        self.imgs = []      # list[dict de atributos]
        self.scripts = []   # list[dict de atributos] (só os com src)

    def handle_starttag(self, tag, attrs):
        d = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self.tem_title = True
            self._em_title = True
        elif tag == "meta":
            name = d.get("name", "").lower()
            if name == "description" and d.get("content", "").strip():
                self.tem_meta_desc = True
            if name == "viewport" and d.get("content", "").strip():
                self.tem_viewport = True
        elif tag == "img":
            self.imgs.append(d)
        elif tag == "script" and d.get("src"):
            self.scripts.append(d)

    def handle_endtag(self, tag):
        if tag == "title":
            self._em_title = False

    def handle_data(self, data):
        if self._em_title:
            self.title_texto += data


def auditar(html: str) -> dict:
    """Checklist estático de QA PageSpeed. Devolve passou/falhas/avisos.

    Falhas = quebram SEO/indexação ou causam CLS (bloqueiam aprovação).
    Avisos = performance recomendada (não bloqueiam).
    """
    c = _Colheita()
    c.feed(html or "")

    falhas = []
    avisos = []

    if not (c.tem_title and c.title_texto.strip()):
        falhas.append("falta <title> não vazio")
    if not c.tem_meta_desc:
        falhas.append("falta <meta name=description>")
    if not c.tem_viewport:
        falhas.append("falta <meta name=viewport>")

    for i, img in enumerate(c.imgs):
        src = img.get("src", "") or f"#{i}"
        if not img.get("alt", "").strip():
            falhas.append(f"<img> sem alt: {src}")
        if not (img.get("width") and img.get("height")):
            falhas.append(f"<img> sem width/height (CLS): {src}")
        if img.get("loading", "").lower() != "lazy":
            avisos.append(f"<img> sem loading=lazy: {src}")

    for s in c.scripts:
        if "defer" not in s and "async" not in s:
            avisos.append(f"<script> externo sem defer/async: {s.get('src')}")

    return {"passou": not falhas, "falhas": falhas, "avisos": avisos}


if __name__ == "__main__":
    bom = """<!doctype html><html><head>
      <title>Marmoraria X — Cotação de granito em Campinas</title>
      <meta name="description" content="Bancadas de granito e mármore sob medida em Campinas.">
      <meta name="viewport" content="width=device-width, initial-scale=1">
    </head><body>
      <img src="bancada.jpg" alt="Bancada de granito" width="800" height="600" loading="lazy">
      <script src="app.js" defer></script>
    </body></html>"""
    r = auditar(bom)
    assert r["passou"] is True, r
    assert r["falhas"] == [], r
    assert r["avisos"] == [], r

    ruim = """<html><head></head><body>
      <img src="hero.png">
      <script src="lib.js"></script>
    </body></html>"""
    r = auditar(ruim)
    assert r["passou"] is False
    assert any("title" in f for f in r["falhas"])
    assert any("description" in f for f in r["falhas"])
    assert any("viewport" in f for f in r["falhas"])
    assert any("sem alt" in f for f in r["falhas"])
    assert any("width/height" in f for f in r["falhas"])
    assert any("defer/async" in a for a in r["avisos"])

    print("pagespeed_qa.py OK")
