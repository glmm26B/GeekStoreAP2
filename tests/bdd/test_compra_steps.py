"""
tests/bdd/test_compra_steps.py – Step Definitions para pytest-bdd

Associa as etapas Gherkin do arquivo compra.feature às funções Python.
"""
import os
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import MagicMock

# Carrega todos os cenários do arquivo .feature (caminho relativo ao arquivo)
FEATURE_FILE = os.path.join(os.path.dirname(__file__), "features", "compra.feature")
scenarios(FEATURE_FILE)


# ─────────────────────────────────────────────────────────────────────────────
# Estado compartilhado entre steps via fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def contexto():
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# GIVEN
# ─────────────────────────────────────────────────────────────────────────────

@given("que o banco de dados de testes está configurado")
def banco_configurado(test_db):
    """O fixture test_db já garante isso; step apenas documenta o contexto."""
    pass


@given("o gateway de pagamento está mockado como aprovado")
def gateway_mockado(contexto):
    gateway = MagicMock()
    gateway.cobrar.return_value = {"status": "aprovado"}
    contexto["gateway"] = gateway


@given(parsers.parse('que existe um produto "{nome}" com preço {preco:f} e estoque {estoque:d}'))
def produto_existe(nome, preco, estoque, test_db):
    """Verifica que o produto já foi criado pelo seed do test_db."""
    row = test_db.execute(
        "SELECT * FROM produtos WHERE nome = ?", (nome,)
    ).fetchone()
    assert row is not None, f"Produto '{nome}' não encontrado no banco de testes"
    assert row["preco"] == pytest.approx(preco)
    assert row["estoque"] == estoque


@given(parsers.parse('que existe um cupom "{codigo}" com {desconto:d} porcento de desconto'))
def cupom_existe(codigo, desconto, test_db):
    row = test_db.execute(
        "SELECT * FROM cupons WHERE codigo = ?", (codigo,)
    ).fetchone()
    assert row is not None, f"Cupom '{codigo}' não encontrado"
    assert row["desconto"] == pytest.approx(desconto / 100)


# ─────────────────────────────────────────────────────────────────────────────
# WHEN
# ─────────────────────────────────────────────────────────────────────────────

@when(parsers.parse("eu compro {qtd:d} unidade do produto com id {pid:d}"))
def comprar_produto(qtd, pid, contexto, test_db):
    from app import ServicoPedidos
    db_path = os.environ["DATABASE_URL"]
    servico = ServicoPedidos(gateway=contexto["gateway"], db_path=db_path)
    contexto["resultado"] = servico.processar_compra(produto_id=pid, quantidade=qtd)


@when(parsers.parse('eu compro {qtd:d} unidade do produto com id {pid:d} usando o cupom "{cupom}"'))
def comprar_com_cupom(qtd, pid, cupom, contexto, test_db):
    from app import ServicoPedidos
    db_path = os.environ["DATABASE_URL"]
    servico = ServicoPedidos(gateway=contexto["gateway"], db_path=db_path)
    contexto["resultado"] = servico.processar_compra(produto_id=pid, quantidade=qtd, cupom=cupom)


@when(parsers.parse("eu tento comprar {qtd:d} unidade do produto com id {pid:d}"))
def tentar_comprar(qtd, pid, contexto, test_db):
    from app import ServicoPedidos
    db_path = os.environ["DATABASE_URL"]
    gateway = MagicMock()
    gateway.cobrar.return_value = {"status": "aprovado"}
    servico = ServicoPedidos(gateway=gateway, db_path=db_path)
    contexto["resultado"] = servico.processar_compra(produto_id=pid, quantidade=qtd)


@when(parsers.parse('eu tento comprar {qtd:d} unidade do produto com id {pid:d} usando o cupom "{cupom}"'))
def tentar_comprar_com_cupom(qtd, pid, cupom, contexto, test_db):
    from app import ServicoPedidos
    db_path = os.environ["DATABASE_URL"]
    gateway = MagicMock()
    gateway.cobrar.return_value = {"status": "aprovado"}
    servico = ServicoPedidos(gateway=gateway, db_path=db_path)
    contexto["resultado"] = servico.processar_compra(produto_id=pid, quantidade=qtd, cupom=cupom)


# ─────────────────────────────────────────────────────────────────────────────
# THEN
# ─────────────────────────────────────────────────────────────────────────────

@then("a compra deve ser realizada com sucesso")
def compra_sucesso(contexto):
    resultado = contexto["resultado"]
    assert resultado["status"] == 200
    assert "sucesso" in resultado["mensagem"].lower()


@then(parsers.parse("o total deve ser {total:f}"))
def verificar_total(total, contexto):
    assert contexto["resultado"]["total"] == pytest.approx(total, rel=1e-2)


@then(parsers.parse('a compra deve falhar com erro "{mensagem_erro}"'))
def compra_falhou(mensagem_erro, contexto):
    resultado = contexto["resultado"]
    assert resultado["status"] != 200
    assert mensagem_erro.lower() in resultado["erro"].lower()
