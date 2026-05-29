"""
tests/e2e/test_selenium.py – Testes End-to-End com Selenium

Abre o navegador em modo headless, interage com a interface
e valida as mensagens exibidas ao usuário.

Requisito: aplicação rodando em localhost:5000
"""
import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException


BASE_URL = "http://127.0.0.1:5000"


def criar_driver():
    """Cria um ChromeDriver em modo headless para CI."""
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,720")
    return webdriver.Chrome(options=opts)


@pytest.fixture(scope="module")
def driver():
    """Fixture de driver Selenium – compartilhado no módulo."""
    d = criar_driver()
    yield d
    d.quit()


def aguardar_resultado(driver, timeout=10):
    """Aguarda o div#resultado ficar visível."""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.ID, "resultado"))
    )


class TestE2EGeekStore:

    def test_pagina_carrega(self, driver):
        driver.get(BASE_URL)
        assert "GeekStore" in driver.title

    def test_botao_comprar_existe(self, driver):
        driver.get(BASE_URL)
        btn = driver.find_element(By.ID, "btn-comprar")
        assert btn is not None
        assert btn.is_displayed()

    def test_compra_com_sucesso(self, driver):
        driver.get(BASE_URL)

        # Preenche produto_id = 1, quantidade = 1
        campo_id = driver.find_element(By.ID, "produto_id")
        campo_id.clear()
        campo_id.send_keys("1")

        campo_qtd = driver.find_element(By.ID, "quantidade")
        campo_qtd.clear()
        campo_qtd.send_keys("1")

        driver.find_element(By.ID, "btn-comprar").click()

        resultado = aguardar_resultado(driver)
        texto = resultado.text
        assert "sucesso" in texto.lower() or "Compra" in texto

    def test_resultado_visivel_apos_compra(self, driver):
        driver.get(BASE_URL)

        driver.find_element(By.ID, "produto_id").clear()
        driver.find_element(By.ID, "produto_id").send_keys("1")
        driver.find_element(By.ID, "btn-comprar").click()

        resultado = aguardar_resultado(driver)
        assert resultado.is_displayed()

    def test_compra_com_cupom(self, driver):
        driver.get(BASE_URL)

        driver.find_element(By.ID, "produto_id").clear()
        driver.find_element(By.ID, "produto_id").send_keys("1")
        driver.find_element(By.ID, "cupom").send_keys("DESCONTO10")
        driver.find_element(By.ID, "btn-comprar").click()

        resultado = aguardar_resultado(driver)
        texto = resultado.text
        # Deve mostrar sucesso e mencionar valor
        assert "sucesso" in texto.lower() or "R$" in texto

    def test_erro_sem_estoque(self, driver):
        """Produto 2 não tem estoque – deve exibir mensagem de erro."""
        driver.get(BASE_URL)

        driver.find_element(By.ID, "produto_id").clear()
        driver.find_element(By.ID, "produto_id").send_keys("2")
        driver.find_element(By.ID, "btn-comprar").click()

        resultado = aguardar_resultado(driver)
        texto = resultado.text
        assert "erro" in texto.lower() or "insuficiente" in texto.lower()

    def test_campos_existem(self, driver):
        driver.get(BASE_URL)

        assert driver.find_element(By.ID, "produto_id")
        assert driver.find_element(By.ID, "quantidade")
        assert driver.find_element(By.ID, "cupom")
        assert driver.find_element(By.ID, "btn-comprar")
