"""Ícones — set leve inline (Lucide, MIT), stroke em `currentColor`.

Por que inline e não lib: o gerador é HTML estático. SVG inline = zero runtime,
zero request, zero npm — e `currentColor` faz o ícone herdar a cor do contexto
(basta `color: var(--acento)` no elemento). Traço de 24×24, stroke-width 2,
arredondado (mesma linguagem do Lucide) → visual de site moderno sem peso.

Uso no template:  icone("check", size=20)  → '<svg ...>…</svg>'
Só entra ícone que um site de serviço/isca de fato usa (benefícios, contato,
prova, processo). Sem catálogo especulativo — cada um justifica um uso real.
"""
from __future__ import annotations

# name -> conteúdo interno do <svg> (paths do Lucide, viewBox 0 0 24 24)
_LUCIDE: dict[str, str] = {
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "check-circle": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "message-circle": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "map-pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "shield-check": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "star": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "sparkles": '<path d="M9.94 14.06A2 2 0 0 0 8.5 12.62L2.37 11.04a.5.5 0 0 1 0-.96L8.5 8.5a2 2 0 0 0 1.44-1.44l1.58-6.13a.5.5 0 0 1 .96 0l1.58 6.13A2 2 0 0 0 15.5 8.5l6.13 1.58a.5.5 0 0 1 0 .96L15.5 12.62a2 2 0 0 0-1.44 1.44l-1.58 6.13a.5.5 0 0 1-.96 0z"/>',
    "calendar": '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "trending-up": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "award": '<circle cx="12" cy="8" r="6"/><path d="M15.48 12.89 17 22l-5-3-5 3 1.52-9.11"/>',
    "heart": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
}

# apelidos práticos pro domínio (whatsapp = message-circle; etc.)
_ALIAS = {"whatsapp": "message-circle", "zap": "zap", "relogio": "clock",
          "escudo": "shield-check", "estrela": "star", "local": "map-pin",
          "telefone": "phone", "agenda": "calendar", "check-ok": "check-circle"}


def existe(nome: str) -> bool:
    return _resolver(nome) in _LUCIDE


def _resolver(nome: str) -> str:
    n = (nome or "").strip().lower()
    return _ALIAS.get(n, n)


def icone(nome: str, *, size: int = 22, stroke: float = 2, cls: str = "ic") -> str:
    """SVG inline do ícone (currentColor). '' se o nome não existir (nunca quebra o
    template — o chamador decide o fallback). `cls` pra estilizar via CSS."""
    conteudo = _LUCIDE.get(_resolver(nome))
    if not conteudo:
        return ""
    return (f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="none" stroke="currentColor" stroke-width="{stroke}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{conteudo}</svg>')


def nomes() -> list[str]:
    """Todos os ícones disponíveis (pro brief de design saber o que dá pra usar)."""
    return sorted(_LUCIDE)


if __name__ == "__main__":  # self-check: gera SVG válido, currentColor, alias, vazio seguro
    s = icone("check", size=20)
    assert s.startswith("<svg") and 'stroke="currentColor"' in s and 'width="20"' in s
    assert "viewBox" in s and "M20 6" in s
    assert icone("whatsapp") == icone("message-circle")  # alias
    assert icone("naoexiste") == "" and not existe("naoexiste")
    assert existe("shield-check") and len(nomes()) >= 15
    for n in nomes():  # cada ícone gera SVG bem-formado (abre e fecha)
        assert icone(n).startswith("<svg") and icone(n).endswith("</svg>"), n
    print(f"icones OK — {len(nomes())} ícones inline, currentColor, alias, fallback vazio")
