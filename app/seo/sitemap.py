"""Tier 2 AEO/SEO — sitemap.xml + robots.txt. Funções puras, stdlib só."""
from xml.sax.saxutils import escape


def sitemap_xml(urls: list[str], lastmod: str = "") -> str:
    """Gera um <urlset> válido, um <url><loc> por url (com <lastmod> se dado)."""
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        loc = f"    <loc>{escape(u)}</loc>"
        if lastmod:
            linhas.append(f"  <url>\n{loc}\n    <lastmod>{escape(lastmod)}</lastmod>\n  </url>")
        else:
            linhas.append(f"  <url>\n{loc}\n  </url>")
    linhas.append("</urlset>")
    return "\n".join(linhas)


def robots_txt(sitemap_url: str) -> str:
    """robots.txt permissivo com linha Sitemap:."""
    return f"User-agent: *\nAllow: /\nSitemap: {sitemap_url}\n"


if __name__ == "__main__":
    from xml.dom.minidom import parseString

    urls = ["https://ex.com/", "https://ex.com/servicos", "https://ex.com/?a=1&b=2"]
    xml = sitemap_xml(urls, lastmod="2026-07-28")
    parseString(xml)  # bem formado ou levanta
    for u in urls:
        assert escape(u) in xml, u
    assert "<lastmod>2026-07-28</lastmod>" in xml
    # sem lastmod também é bem formado
    parseString(sitemap_xml(urls))

    rob = robots_txt("https://ex.com/sitemap.xml")
    assert "Sitemap: https://ex.com/sitemap.xml" in rob
    assert "User-agent: *" in rob and "Allow: /" in rob

    print("sitemap.py OK")
