# language: pt
Funcionalidade: Compra de produto na GeekStore
  Como um cliente da GeekStore
  Quero comprar um produto pelo sistema
  Para que eu possa receber minha compra

  Contexto:
    Dado que o banco de dados de testes está configurado
    E o gateway de pagamento está mockado como aprovado

  Cenário: Compra com sucesso sem cupom
    Dado que existe um produto "Teclado Mecânico RGB" com preço 299.90 e estoque 10
    Quando eu compro 1 unidade do produto com id 1
    Então a compra deve ser realizada com sucesso
    E o total deve ser 299.90

  Cenário: Compra com sucesso usando cupom de desconto
    Dado que existe um produto "Teclado Mecânico RGB" com preço 299.90 e estoque 10
    E que existe um cupom "DESCONTO10" com 10 porcento de desconto
    Quando eu compro 1 unidade do produto com id 1 usando o cupom "DESCONTO10"
    Então a compra deve ser realizada com sucesso
    E o total deve ser 269.91

  Cenário: Falha na compra por falta de estoque
    Dado que existe um produto "Mouse Gamer 12000 DPI" com preço 189.90 e estoque 0
    Quando eu tento comprar 1 unidade do produto com id 2
    Então a compra deve falhar com erro "Estoque insuficiente"

  Cenário: Falha na compra com produto inexistente
    Quando eu tento comprar 1 unidade do produto com id 9999
    Então a compra deve falhar com erro "Produto não encontrado"

  Cenário: Falha na compra com cupom inválido
    Dado que existe um produto "Teclado Mecânico RGB" com preço 299.90 e estoque 10
    Quando eu tento comprar 1 unidade do produto com id 1 usando o cupom "INVALIDO"
    Então a compra deve falhar com erro "Cupom inválido"
