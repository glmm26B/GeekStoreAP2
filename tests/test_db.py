"""
tests/test_db.py – Testes de Integração com Banco de Dados

Verifica operações diretas no banco temporário (fixtures com teardown).
"""
import sqlite3
import pytest


class TestBancoDeDados:
    """Testa a camada de persistência isolada do Flask."""

    def test_fixture_cria_produtos(self, test_db):
        rows = test_db.execute("SELECT * FROM produtos").fetchall()
        assert len(rows) == 2

    def test_produto_teclado_existe(self, test_db):
        row = test_db.execute(
            "SELECT * FROM produtos WHERE nome = ?", ("Teclado Mecânico RGB",)
        ).fetchone()
        assert row is not None
        assert row["preco"] == pytest.approx(299.90)
        assert row["estoque"] == 10

    def test_produto_mouse_sem_estoque(self, test_db):
        row = test_db.execute(
            "SELECT * FROM produtos WHERE nome = ?", ("Mouse Gamer 12000 DPI",)
        ).fetchone()
        assert row is not None
        assert row["estoque"] == 0

    def test_cupom_desconto10_existe(self, test_db):
        row = test_db.execute(
            "SELECT * FROM cupons WHERE codigo = ?", ("DESCONTO10",)
        ).fetchone()
        assert row is not None
        assert row["desconto"] == pytest.approx(0.10)

    def test_inserir_pedido(self, test_db):
        test_db.execute(
            "INSERT INTO pedidos (produto_id, quantidade, total, status) VALUES (?,?,?,?)",
            (1, 2, 599.80, "aprovado"),
        )
        test_db.commit()

        row = test_db.execute("SELECT * FROM pedidos WHERE produto_id = 1").fetchone()
        assert row["total"] == pytest.approx(599.80)
        assert row["status"] == "aprovado"

    def test_atualizar_estoque(self, test_db):
        test_db.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = 1", (3,)
        )
        test_db.commit()

        row = test_db.execute("SELECT estoque FROM produtos WHERE id = 1").fetchone()
        assert row["estoque"] == 7

    def test_unicidade_codigo_cupom(self, test_db):
        with pytest.raises(sqlite3.IntegrityError):
            test_db.execute(
                "INSERT INTO cupons (codigo, desconto) VALUES (?,?)",
                ("DESCONTO10", 0.20),
            )
            test_db.commit()

    def test_banco_isolado_entre_testes(self, test_db):
        """Garante que cada teste começa com um banco limpo."""
        count = test_db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        assert count == 0

    def test_init_db_cria_tabelas(self, tmp_path):
        """Verifica que init_db cria todas as tabelas necessárias."""
        import os
        from app import init_db, get_connection

        db_path = str(tmp_path / "novo.db")
        os.environ["DATABASE_URL"] = db_path
        init_db(db_path)

        conn = get_connection(db_path)
        tabelas = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        nomes = {r[0] for r in tabelas}
        conn.close()
        os.remove(db_path)
        os.environ.pop("DATABASE_URL", None)

        assert "produtos" in nomes
        assert "pedidos" in nomes
        assert "cupons" in nomes
