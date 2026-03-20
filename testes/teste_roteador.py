"""
Testes do roteador — classificação por fallback (sem API).
"""

import pytest
from agentes.roteador import Roteador


class TestRoteadorFallback:
    """Testa a classificação por palavras-chave (fallback)."""

    def setup_method(self):
        self.roteador = Roteador()

    def test_classifica_estoque(self):
        resultado = self.roteador._classificar_fallback(
            "Quantas camisetas pretas M tem no estoque?"
        )
        assert resultado["agente"] == "estoque"

    def test_classifica_rh(self):
        resultado = self.roteador._classificar_fallback(
            "Qual o valor do vale-refeição?"
        )
        assert resultado["agente"] == "rh"

    def test_classifica_bi(self):
        resultado = self.roteador._classificar_fallback(
            "Qual a taxa de resolução dos atendimentos?"
        )
        assert resultado["agente"] == "bi"

    def test_classifica_cliente_default(self):
        resultado = self.roteador._classificar_fallback(
            "Posso devolver uma roupa?"
        )
        assert resultado["agente"] == "cliente"

    def test_classifica_ferias_como_rh(self):
        resultado = self.roteador._classificar_fallback(
            "Como funciona o fracionamento de férias?"
        )
        assert resultado["agente"] == "rh"

    def test_classifica_metricas_como_bi(self):
        resultado = self.roteador._classificar_fallback(
            "Me mostra o relatório de performance do mês"
        )
        assert resultado["agente"] == "bi"

    def test_classifica_disponibilidade_como_estoque(self):
        resultado = self.roteador._classificar_fallback(
            "Essa referência está disponível na loja do Ibirapuera?"
        )
        assert resultado["agente"] == "estoque"

    def test_nao_bloqueia_mensagem_normal(self):
        resultado = self.roteador._classificar_fallback(
            "Bom dia, gostaria de saber sobre prazos de entrega"
        )
        assert resultado["bloqueado"] is False
