"""
conftest.py – Fixtures compartilhadas entre toda a suíte de testes.
"""
import os
import sqlite3
import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Constante que aponta para o banco temporário de testes
# ─────────────────────────────────────────────────────────────────────────────
TEST_DB = "test.db"


# ─────────────────────────────────────────────────────────────────────────────
# Fixture: banco de dados em arquivo temporário
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def test_db(tmp_path):
    """
    Cria um banco SQLite temporário, popula com dados fictícios,
    redireciona a aplicação para usá-lo e o remove após cada teste.
    """
    db_path = str(tmp_path / TEST_DB)

    # Força o app a usar o banco de testes via variável de ambiente
    os.environ["DATABASE_URL"] = db_path

    # Importa DEPOIS de setar a env var, para garantir que o módulo leia o valor correto
    from app import init_db

    init_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # ── Seed de dados fictícios ──────────────────────────────────────────────
    conn.execute(
        "INSERT INTO produtos (nome, preco, estoque) VALUES (?,?,?)",
        ("Teclado Mecânico RGB", 299.90, 10),
    )
    conn.execute(
        "INSERT INTO produtos (nome, preco, estoque) VALUES (?,?,?)",
        ("Mouse Gamer 12000 DPI", 189.90, 0),          # sem estoque
    )
    conn.execute(
        "INSERT INTO cupons (codigo, desconto) VALUES (?,?)",
        ("DESCONTO10", 0.10),
    )
    conn.commit()

    yield conn  # ← ponto de uso nos testes

    # ── Teardown ─────────────────────────────────────────────────────────────
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    os.environ.pop("DATABASE_URL", None)


# ─────────────────────────────────────────────────────────────────────────────
# Fixture: cliente Flask de testes
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def client(test_db):
    """
    Retorna um cliente de teste do Flask já conectado ao banco temporário.
    O `test_db` fixture garante que DATABASE_URL está apontado corretamente.
    """
    from app import app

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ─────────────────────────────────────────────────────────────────────────────
# Fixture: ServicoPedidos com gateway mockado
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def servico_com_mock(test_db, mocker):
    """
    Retorna um ServicoPedidos com GatewayPagamento mockado (aprovado por padrão).
    """
    from app import ServicoPedidos

    gateway_mock = mocker.MagicMock()
    gateway_mock.cobrar.return_value = {"status": "aprovado"}

    db_path = os.environ["DATABASE_URL"]
    return ServicoPedidos(gateway=gateway_mock, db_path=db_path), gateway_mock
