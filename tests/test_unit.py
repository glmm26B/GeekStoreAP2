"""
tests/test_unit.py – Testes Unitários

Testa regras de negócio do ServicoPedidos isoladas do banco real,
usando mocks para o gateway e um banco temporário via fixture.
"""
import pytest


class TestProcessarCompra:
    """Regras de negócio do ServicoPedidos."""

    def test_compra_sucesso(self, servico_com_mock):
        servico, gateway_mock = servico_com_mock
        resultado = servico.processar_compra(produto_id=1, quantidade=1)

        assert resultado["status"] == 200
        assert "Compra realizada" in resultado["mensagem"]
        assert resultado["total"] == pytest.approx(299.90)

    def test_compra_sucesso_chama_gateway_uma_vez(self, servico_com_mock):
        servico, gateway_mock = servico_com_mock
        servico.processar_compra(produto_id=1, quantidade=2)

        gateway_mock.cobrar.assert_called_once()

    def test_compra_sucesso_valor_correto_no_gateway(self, servico_com_mock):
        servico, gateway_mock = servico_com_mock
        servico.processar_compra(produto_id=1, quantidade=3)

        # 299.90 × 3 = 899.70
        gateway_mock.cobrar.assert_called_once_with(pytest.approx(899.70))

    def test_produto_nao_encontrado(self, servico_com_mock):
        servico, gateway_mock = servico_com_mock
        resultado = servico.processar_compra(produto_id=9999, quantidade=1)

        assert resultado["status"] == 404
        assert "não encontrado" in resultado["erro"]
        gateway_mock.cobrar.assert_not_called()

    def test_estoque_insuficiente(self, servico_com_mock):
        """Produto 2 tem estoque = 0."""
        servico, gateway_mock = servico_com_mock
        resultado = servico.processar_compra(produto_id=2, quantidade=1)

        assert resultado["status"] == 400
        assert "insuficiente" in resultado["erro"]
        gateway_mock.cobrar.assert_not_called()

    def test_cupom_valido_aplica_desconto(self, servico_com_mock):
        servico, gateway_mock = servico_com_mock
        resultado = servico.processar_compra(produto_id=1, quantidade=1, cupom="DESCONTO10")

        # 299.90 × 0.90 = 269.91
        assert resultado["status"] == 200
        assert resultado["total"] == pytest.approx(299.90 * 0.90)

    def test_cupom_invalido_retorna_erro(self, servico_com_mock):
        servico, gateway_mock = servico_com_mock
        resultado = servico.processar_compra(produto_id=1, quantidade=1, cupom="INVALIDO")

        assert resultado["status"] == 400
        assert "Cupom" in resultado["erro"]
        gateway_mock.cobrar.assert_not_called()

    def test_gateway_recusado_retorna_erro(self, servico_com_mock):
        servico, gateway_mock = servico_com_mock
        gateway_mock.cobrar.return_value = {"status": "recusado"}

        resultado = servico.processar_compra(produto_id=1, quantidade=1)

        assert resultado["status"] == 402
        assert "Pagamento recusado" in resultado["erro"]

    def test_compra_reduz_estoque(self, servico_com_mock, test_db):
        """Verifica se o estoque é decrementado após compra bem-sucedida."""
        servico, _ = servico_com_mock
        servico.processar_compra(produto_id=1, quantidade=3)

        row = test_db.execute("SELECT estoque FROM produtos WHERE id = 1").fetchone()
        assert row["estoque"] == 7  # 10 - 3

    def test_compra_registra_pedido(self, servico_com_mock, test_db):
        """Verifica se o pedido é gravado no banco após compra."""
        servico, _ = servico_com_mock
        servico.processar_compra(produto_id=1, quantidade=2)

        count = test_db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        assert count == 1

    def test_compra_multiplas_quantidades(self, servico_com_mock):
        servico, gateway_mock = servico_com_mock
        resultado = servico.processar_compra(produto_id=1, quantidade=5)

        assert resultado["status"] == 200
        assert resultado["total"] == pytest.approx(299.90 * 5)

    def test_quantidade_exata_no_estoque(self, servico_com_mock):
        """Comprar exatamente o que há em estoque deve funcionar."""
        servico, _ = servico_com_mock
        resultado = servico.processar_compra(produto_id=1, quantidade=10)

        assert resultado["status"] == 200

    def test_quantidade_acima_do_estoque(self, servico_com_mock):
        """Comprar mais do que há em estoque deve falhar."""
        servico, _ = servico_com_mock
        resultado = servico.processar_compra(produto_id=1, quantidade=11)

        assert resultado["status"] == 400


class TestGatewayPagamento:
    """Garante que o GatewayPagamento real lança exceção (nunca deve ser usado em testes)."""

    def test_gateway_real_nao_implementado(self):
        from app import GatewayPagamento

        gw = GatewayPagamento()
        with pytest.raises(NotImplementedError):
            gw.cobrar(100.0)
