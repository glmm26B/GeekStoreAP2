# 🛒 GeekStore – Suíte de Testes ATS AP2

[![CI GeekStore](https://github.com/SEU_USUARIO/geekstore/actions/workflows/ci.yml/badge.svg)](https://github.com/SEU_USUARIO/geekstore/actions/workflows/ci.yml)

Projeto final da disciplina ATS AP2. Sistema de e-commerce **GeekStore** com banco SQLite, refatorado para testabilidade e coberto por uma suíte completa de testes automatizados.

---

## 🏗️ Arquitetura

```
geekstore/
├── app.py                          # Aplicação Flask (refatorada com DI)
├── conftest.py                     # Fixtures globais (banco temporário, cliente Flask, mocks)
├── requirements.txt
├── pytest.ini
├── .github/workflows/ci.yml        # Pipeline GitHub Actions
└── tests/
    ├── test_unit.py                # Testes Unitários (ServicoPedidos + Mocks)
    ├── test_db.py                  # Testes de Integração com banco SQLite
    ├── test_api.py                 # Testes de API via Flask test_client
    ├── test_extra.py               # Cobertura complementar (seed, factory)
    ├── test_api_contract.tavern.yaml  # Testes de Contrato (Tavern)
    ├── common.yaml                 # Config compartilhada Tavern
    ├── tavern_helpers.py           # Funções auxiliares Tavern
    ├── e2e/
    │   └── test_selenium.py        # Testes E2E (Selenium headless)
    └── bdd/
        ├── test_compra_steps.py    # Step definitions pytest-bdd
        └── features/
            └── compra.feature      # Cenários Gherkin (pt-BR)
```

---

## ✅ Tipos de Teste Implementados

| Tipo | Arquivo | Ferramenta |
|------|---------|-----------|
| **Unitário** | `tests/test_unit.py` | pytest + pytest-mock |
| **Integração/DB** | `tests/test_db.py` | pytest + SQLite temporário |
| **API** | `tests/test_api.py` | Flask test_client |
| **BDD** | `tests/bdd/` | pytest-bdd + Gherkin |
| **Contrato API** | `tests/test_api_contract.tavern.yaml` | Tavern |
| **E2E** | `tests/e2e/test_selenium.py` | Selenium + ChromeDriver headless |

---

## 🔧 Refatorações para Testabilidade

### 1. Injeção de Dependência – Banco de Dados
A função `get_db_path()` sempre lê `os.environ['DATABASE_URL']` no momento da chamada, permitindo que os testes redirecionem para um banco temporário sem reiniciar a aplicação.

### 2. Injeção de Dependência – Gateway de Pagamento
`ServicoPedidos` recebe o `GatewayPagamento` como parâmetro no construtor, permitindo que os testes injetem um `MagicMock` sem fazer chamadas HTTP reais.

### 3. Seed como Função
O bloco de inicialização de dados foi extraído para `seed_dev_data()`, tornando-o testável e evitando dependência do bloco `__main__`.

---

## 🚀 Como executar localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar apenas os testes rápidos (sem Tavern/Selenium)
pytest tests/test_unit.py tests/test_db.py tests/test_api.py tests/bdd/ tests/test_extra.py \
       --cov=app --cov-report=term-missing

# Rodar TODOS os testes (requer app rodando em background)
python app.py &
sleep 3
pytest --cov=app --cov-fail-under=90
```

---

## 📊 Cobertura de Código

```
Name     Stmts   Miss  Cover
-----------------------------
app.py      98      3    97%
-----------------------------
TOTAL       98      3    97%
```

Meta: **≥ 90%** ✅ Atingido: **97%**

---

## 🔄 Pipeline CI/CD (GitHub Actions)

O arquivo `.github/workflows/ci.yml` realiza automaticamente:

1. Checkout do código
2. Configuração do Python 3.10
3. Instalação das dependências
4. Instalação do Chrome + ChromeDriver (headless)
5. Seed do banco de dados
6. Inicialização da aplicação em background
7. Verificação de saúde (`curl /produtos`)
8. Execução de todos os testes com `pytest --cov=app --cov-fail-under=90`
9. Upload do relatório de cobertura (Codecov)

> **A pipeline falha automaticamente se a cobertura cair abaixo de 90%.**

---

## 📝 Cenários BDD (Gherkin)

Arquivo: `tests/bdd/features/compra.feature`

- ✅ Compra com sucesso sem cupom
- ✅ Compra com sucesso usando cupom de desconto (10%)
- ✅ Falha por falta de estoque
- ✅ Falha por produto inexistente
- ✅ Falha por cupom inválido

---

## 🎯 Fixtures Avançadas

O `conftest.py` implementa:

- **`test_db`** – banco SQLite em arquivo temporário (`tmp_path`), com seed de dados e teardown automático (deleção do arquivo após cada teste)
- **`client`** – cliente Flask de testes que herda `test_db`, garantindo isolamento total
- **`servico_com_mock`** – `ServicoPedidos` com `GatewayPagamento` mockado via `pytest-mock`

> ⚠️ Não usamos `:memory:` pois threads diferentes (Flask vs. pytest) não compartilham dados em SQLite in-memory.
