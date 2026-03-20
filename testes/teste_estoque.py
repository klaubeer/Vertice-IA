"""
Testes de consulta de estoque.
Requer banco inicializado: python -m banco.inicializador
"""

import pytest
from ferramentas.consulta_estoque import (
    consultar_estoque, obter_estoque_critico, resumo_estoque_por_loja
)


class TestConsultaEstoque:
    """Testa consultas ao banco de estoque."""

    def test_consulta_por_sku(self):
        resultados = consultar_estoque(sku="VTX-CAM-001")
        assert len(resultados) > 0
        assert all(r["sku"] == "VTX-CAM-001" for r in resultados)

    def test_consulta_por_categoria(self):
        resultados = consultar_estoque(categoria="bone")
        assert len(resultados) > 0
        assert all(r["categoria"] == "bone" for r in resultados)

    def test_consulta_por_loja(self):
        resultados = consultar_estoque(loja="Paulista")
        assert len(resultados) > 0
        assert all("Paulista" in r["loja"] for r in resultados)

    def test_consulta_por_tamanho(self):
        resultados = consultar_estoque(tamanho="M")
        assert len(resultados) > 0
        assert all(r["tamanho"] == "M" for r in resultados)

    def test_consulta_multiplos_filtros(self):
        resultados = consultar_estoque(sku="VTX-CAM-001", tamanho="M", loja="Paulista")
        assert len(resultados) == 1
        assert resultados[0]["quantidade"] > 0

    def test_consulta_sem_resultado(self):
        resultados = consultar_estoque(sku="INEXISTENTE")
        assert len(resultados) == 0

    def test_estoque_critico(self):
        resultados = obter_estoque_critico()
        # Deve haver itens com estoque crítico nos dados fictícios
        assert isinstance(resultados, list)
        for r in resultados:
            assert r["quantidade"] <= r["estoque_minimo"]

    def test_resumo_por_loja(self):
        resultados = resumo_estoque_por_loja()
        assert len(resultados) == 20  # 20 lojas
        for r in resultados:
            assert "loja" in r
            assert "total_pecas" in r
            assert "valor_total" in r
            assert r["total_pecas"] > 0
