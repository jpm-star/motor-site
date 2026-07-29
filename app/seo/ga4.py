"""Tier 2 SEO — snippet GA4 (gtag.js). Função pura, stdlib só.

GA4 é a 2ª fonte de verificação (ao lado do beacon próprio), não substituto.
O measurement_id (G-XXXX) o JP cria na property do GA4 — sem ele, inerte.
"""


def gtag_snippet(measurement_id: str) -> str:
    """Snippet gtag.js padrão do GA4 (2 scripts) parametrizado pelo id.
    measurement_id vazio → "" (inerte, não quebra o head)."""
    mid = (measurement_id or "").strip()
    if not mid:
        return ""
    return (
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={mid}"></script>\n'
        "<script>\n"
        "  window.dataLayer = window.dataLayer || [];\n"
        "  function gtag(){dataLayer.push(arguments);}\n"
        "  gtag('js', new Date());\n"
        f"  gtag('config', '{mid}');\n"
        "</script>"
    )


if __name__ == "__main__":  # self-check
    s = gtag_snippet("G-ABC123")
    assert "G-ABC123" in s and "gtag(" in s and "googletagmanager" in s, s
    assert gtag_snippet("") == "" and gtag_snippet("  ") == ""  # inerte sem id
    print("ga4.py OK")
