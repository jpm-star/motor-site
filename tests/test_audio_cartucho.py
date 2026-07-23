"""audio→cartucho: partes puras (faltando + multipart). Sem rede."""
from app import audio_cartucho as ac


def test_faltando_lista_nulos():
    cart = {"nome_empresa": "X", "vertical": "marmoraria", "escopo": None,
            "regioes_atendidas": [], "whatsapp_dono": "", "politica_preco": "sob medida",
            "politica_visita": None, "horario": None}
    f = ac.faltando(cart)
    # null/""/[] entram; preenchidos não
    assert "escopo" in f and "regioes_atendidas" in f and "whatsapp_dono" in f
    assert "nome_empresa" not in f and "politica_preco" not in f


def test_multipart_bem_formado():
    corpo, ctype = ac._multipart({"model": "m", "language": "pt"}, ("a.ogg", b"\x00\x01"))
    assert ctype.startswith("multipart/form-data; boundary=")
    assert b'name="model"' in corpo and b'filename="a.ogg"' in corpo
    assert corpo.endswith(b"--\r\n") and b"\x00\x01" in corpo
