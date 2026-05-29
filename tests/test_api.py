"""
tests/test_api.py – Testes de API (cliente Flask)

Testa os endpoints HTTP da aplicação via test_client,
com o gateway mockado para não chamar serviços externos.
"""
import json
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_gateway(mocker):
    """Mocka o GatewayPagamento em todas as rotas para evitar chamada real."""
    gateway_mock = MagicMock()
    gateway_mock.cobrar.return_value = {"status": "aprovado"}
    mocker.patch("app.GatewayPagamento", return_value=gateway_mock)
    return gateway_mock


class TestEndpointProdutos:

    def test_get_produtos_status_200(self, client):
        resp = client.get("/produtos")
        assert resp.status_code == 200

    def test_get_produtos_retorna_lista(self, client):
        data = resp = client.get("/produtos")
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_get_produtos_tem_chaves_esperadas(self, client):
        data = json.loads(client.get("/produtos").data)
        produto = data[0]
        assert "id" in produto
        assert "nome" in produto
        assert "preco" in produto
        assert "estoque" in produto

    def test_get_produto_por_id(self, client):
        resp = client.get("/produtos/1")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["id"] == 1

    def test_get_produto_inexistente(self, client):
        resp = client.get("/produtos/9999")
        assert resp.status_code == 404

    def test_get_produto_contem_nome(self, client):
        data = json.loads(client.get("/produtos/1").data)
        assert "Teclado" in data["nome"]


class TestEndpointComprar:

    def test_compra_sucesso_retorna_200(self, client):
        resp = client.post(
            "/comprar",
            data=json.dumps({"produto_id": 1, "quantidade": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_compra_sucesso_mensagem(self, client):
        resp = client.post(
            "/comprar",
            data=json.dumps({"produto_id": 1, "quantidade": 1}),
            content_type="application/json",
        )
        data = json.loads(resp.data)
        assert "sucesso" in data["mensagem"].lower()

    def test_compra_sem_estoque_retorna_400(self, client):
        # Produto 2 tem estoque=0
        resp = client.post(
            "/comprar",
            data=json.dumps({"produto_id": 2, "quantidade": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_compra_produto_inexistente_retorna_404(self, client):
        resp = client.post(
            "/comprar",
            data=json.dumps({"produto_id": 9999, "quantidade": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_compra_sem_produto_id_retorna_400(self, client):
        resp = client.post(
            "/comprar",
            data=json.dumps({"quantidade": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_compra_com_cupom_valido(self, client):
        resp = client.post(
            "/comprar",
            data=json.dumps({"produto_id": 1, "quantidade": 1, "cupom": "DESCONTO10"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["total"] == pytest.approx(299.90 * 0.90)

    def test_compra_com_cupom_invalido(self, client):
        resp = client.post(
            "/comprar",
            data=json.dumps({"produto_id": 1, "quantidade": 1, "cupom": "FALSO"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_compra_retorna_total(self, client):
        resp = client.post(
            "/comprar",
            data=json.dumps({"produto_id": 1, "quantidade": 2}),
            content_type="application/json",
        )
        data = json.loads(resp.data)
        assert data["total"] == pytest.approx(299.90 * 2)


class TestEndpointPedidos:

    def test_get_pedidos_status_200(self, client):
        resp = client.get("/pedidos")
        assert resp.status_code == 200

    def test_get_pedidos_retorna_lista(self, client):
        data = json.loads(client.get("/pedidos").data)
        assert isinstance(data, list)

    def test_pedido_registrado_apos_compra(self, client):
        client.post(
            "/comprar",
            data=json.dumps({"produto_id": 1, "quantidade": 1}),
            content_type="application/json",
        )
        data = json.loads(client.get("/pedidos").data)
        assert len(data) == 1
        assert data[0]["status"] == "aprovado"


class TestEndpointIndex:

    def test_index_retorna_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_index_contem_geekstore(self, client):
        resp = client.get("/")
        assert b"GeekStore" in resp.data
