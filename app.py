import os
import sqlite3
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

DEFAULT_DB = 'geekstore.db'


# ── Dependency Injection: DB ──────────────────────────────────────────────────

def get_db_path():
    """Sempre lê a configuração do app ou a variável de ambiente no momento da chamada."""
    db_path = app.config.get("DATABASE_URL")
    if db_path:
        return db_path
    return os.environ.get('DATABASE_URL', DEFAULT_DB)


def get_connection(db_path=None):
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS produtos (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nome    TEXT    NOT NULL,
            preco   REAL    NOT NULL,
            estoque INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS pedidos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id  INTEGER NOT NULL,
            quantidade  INTEGER NOT NULL,
            total       REAL    NOT NULL,
            status      TEXT    NOT NULL DEFAULT 'aprovado',
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        );
        CREATE TABLE IF NOT EXISTS cupons (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo      TEXT    NOT NULL UNIQUE,
            desconto    REAL    NOT NULL
        );
    """)
    conn.commit()
    conn.close()


# ── Gateway de Pagamento ──────────────────────────────────────────────────────

class GatewayPagamento:
    """Gateway real – nunca deve ser chamado nos testes."""

    def cobrar(self, valor: float) -> dict:
        # Simularia uma chamada HTTP real a um serviço externo
        raise NotImplementedError("Chamada real ao gateway bloqueada em teste!")


class GatewayPagamentoMock(GatewayPagamento):
    """Gateway falso para testes de integração e ambiente de desenvolvimento."""

    def cobrar(self, valor: float) -> dict:
        return {"status": "aprovado"}


# ── Serviço de Pedidos (com DI) ───────────────────────────────────────────────

class ServicoPedidos:
    def __init__(self, gateway: GatewayPagamento, db_path: str = None):
        self.gateway = gateway
        self.db_path = db_path or get_db_path()

    def processar_compra(self, produto_id: int, quantidade: int, cupom: str = None) -> dict:
        conn = get_connection(self.db_path)
        try:
            produto = conn.execute(
                "SELECT * FROM produtos WHERE id = ?", (produto_id,)
            ).fetchone()

            if produto is None:
                return {"erro": "Produto não encontrado", "status": 404}

            if produto["estoque"] < quantidade:
                return {"erro": "Estoque insuficiente", "status": 400}

            total = produto["preco"] * quantidade

            # Aplicar cupom de desconto
            if cupom:
                row = conn.execute(
                    "SELECT desconto FROM cupons WHERE codigo = ?", (cupom,)
                ).fetchone()
                if row:
                    total = total * (1 - row["desconto"])
                else:
                    return {"erro": "Cupom inválido", "status": 400}

            # Cobrar via gateway (injetado)
            resultado_gateway = self.gateway.cobrar(total)

            if resultado_gateway.get("status") != "aprovado":
                return {"erro": "Pagamento recusado", "status": 402}

            # Atualizar estoque e registrar pedido
            conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (quantidade, produto_id),
            )
            conn.execute(
                "INSERT INTO pedidos (produto_id, quantidade, total, status) VALUES (?,?,?,?)",
                (produto_id, quantidade, total, "aprovado"),
            )
            conn.commit()

            return {
                "mensagem": "Compra realizada com sucesso!",
                "total": total,
                "status": 200,
            }
        finally:
            conn.close()


# ── Rotas Flask ───────────────────────────────────────────────────────────────

def _make_servico():
    """Factory usada nas rotas para criar ServicoPedidos com gateway correto."""
    if app.config.get("TESTING") or os.environ.get("USE_TEST_GATEWAY") == "1":
        return ServicoPedidos(gateway=GatewayPagamentoMock())
    return ServicoPedidos(gateway=GatewayPagamento())


@app.route("/produtos", methods=["GET"])
def listar_produtos():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM produtos").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/produtos/<int:produto_id>", methods=["GET"])
def obter_produto(produto_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify(dict(row))


@app.route("/comprar", methods=["POST"])
def comprar():
    dados = request.get_json(force=True)
    produto_id = dados.get("produto_id")
    quantidade = dados.get("quantidade", 1)
    cupom = dados.get("cupom")

    if not produto_id:
        return jsonify({"erro": "produto_id é obrigatório"}), 400

    servico = _make_servico()
    resultado = servico.processar_compra(produto_id, quantidade, cupom)

    status_code = resultado.pop("status", 200)
    return jsonify(resultado), status_code


@app.route("/pedidos", methods=["GET"])
def listar_pedidos():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM pedidos").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ── Frontend ──────────────────────────────────────────────────────────────────

INDEX_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>GeekStore</title>
<style>
  body { font-family: sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; }
  h1 { color: #333; }
  input, select, button { display: block; margin: 8px 0; padding: 8px; width: 100%; box-sizing: border-box; }
  button { background: #4CAF50; color: white; border: none; cursor: pointer; font-size: 16px; }
  button:hover { background: #45a049; }
  #resultado { margin-top: 20px; padding: 12px; border-radius: 4px; display: none; }
  .sucesso { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
  .erro    { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
</style>
</head>
<body>
<h1>🛒 GeekStore</h1>
<label>ID do Produto:
  <input type="number" id="produto_id" value="1" min="1">
</label>
<label>Quantidade:
  <input type="number" id="quantidade" value="1" min="1">
</label>
<label>Cupom (opcional):
  <input type="text" id="cupom" placeholder="ex: DESCONTO10">
</label>
<button id="btn-comprar">Comprar</button>
<div id="resultado"></div>

<script>
document.getElementById('btn-comprar').addEventListener('click', async () => {
  const payload = {
    produto_id: parseInt(document.getElementById('produto_id').value),
    quantidade: parseInt(document.getElementById('quantidade').value),
    cupom: document.getElementById('cupom').value || null
  };
  const res = await fetch('/comprar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  const div = document.getElementById('resultado');
  div.style.display = 'block';
  if (res.ok) {
    div.className = 'sucesso';
    div.textContent = data.mensagem + ' Total: R$ ' + (data.total || 0).toFixed(2);
  } else {
    div.className = 'erro';
    div.textContent = 'Erro: ' + (data.erro || 'desconhecido');
  }
});
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(INDEX_HTML)


# ── Entrypoint ────────────────────────────────────────────────────────────────

def seed_dev_data(db_path=None):
    """Popula o banco com dados de desenvolvimento se estiver vazio."""
    conn = get_connection(db_path)
    existing = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    if existing == 0:
        conn.execute("INSERT INTO produtos (nome, preco, estoque) VALUES (?,?,?)",
                     ("Teclado Mecânico RGB", 299.90, 10))
        conn.execute("INSERT INTO produtos (nome, preco, estoque) VALUES (?,?,?)",
                     ("Mouse Gamer 12000 DPI", 189.90, 5))
        conn.execute("INSERT INTO cupons (codigo, desconto) VALUES (?,?)",
                     ("DESCONTO10", 0.10))
        conn.commit()
    conn.close()
    return existing == 0  # True se inseriu dados


if __name__ == "__main__":
    init_db()
    seed_dev_data()
    app.run(host="0.0.0.0", debug=False, port=5000)
