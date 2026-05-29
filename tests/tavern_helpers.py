"""
tests/tavern_helpers.py – Funções auxiliares para testes Tavern.
"""


def verificar_lista_nao_vazia(response):
    """Valida que a resposta é uma lista com pelo menos 1 item."""
    data = response.json()
    assert isinstance(data, list), "Resposta deveria ser uma lista"
    assert len(data) > 0, "Lista de produtos não deveria estar vazia"

    for produto in data:
        assert "id" in produto
        assert "nome" in produto
        assert "preco" in produto
        assert "estoque" in produto
