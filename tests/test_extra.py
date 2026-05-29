"""
tests/test_extra.py – Testes complementares para atingir ≥90% de cobertura.

Cobre seed_dev_data e a factory _make_servico.
"""
import os
import pytest


class TestSeedDevData:
    """Cobre a função seed_dev_data de app.py."""

    def test_seed_insere_quando_banco_vazio(self, tmp_path):
        db_path = str(tmp_path / "seed_test.db")
        os.environ["DATABASE_URL"] = db_path

        from app import init_db, seed_dev_data, get_connection
        init_db(db_path)

        inseriu = seed_dev_data(db_path)
        assert inseriu is True

        conn = get_connection(db_path)
        count = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        conn.close()
        assert count == 2

        os.environ.pop("DATABASE_URL", None)

    def test_seed_nao_insere_quando_banco_cheio(self, tmp_path):
        db_path = str(tmp_path / "seed_cheio.db")
        os.environ["DATABASE_URL"] = db_path

        from app import init_db, seed_dev_data, get_connection
        init_db(db_path)

        conn = get_connection(db_path)
        conn.execute("INSERT INTO produtos (nome, preco, estoque) VALUES (?,?,?)",
                     ("Produto Existente", 99.90, 3))
        conn.commit()
        conn.close()

        inseriu = seed_dev_data(db_path)
        assert inseriu is False

        conn2 = get_connection(db_path)
        count = conn2.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        conn2.close()
        assert count == 1  # sem seed extra

        os.environ.pop("DATABASE_URL", None)


class TestMakeServico:
    """Cobre a factory _make_servico usada nas rotas."""

    def test_make_servico_retorna_servico_pedidos(self, test_db):
        from app import _make_servico, ServicoPedidos
        servico = _make_servico()
        assert isinstance(servico, ServicoPedidos)

    def test_make_servico_gateway_e_real(self, test_db):
        from app import _make_servico, GatewayPagamento
        servico = _make_servico()
        assert isinstance(servico.gateway, GatewayPagamento)
