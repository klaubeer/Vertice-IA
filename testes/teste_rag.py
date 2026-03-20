"""
Testes do pipeline RAG.
Requer índice criado: python -m rag.indexador
"""

import pytest
from rag.recuperador import RecuperadorHibrido
from rag.reranqueador import Reranqueador


class TestRecuperador:
    """Testa o recuperador híbrido."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.recuperador = RecuperadorHibrido()

    def test_busca_vetorial_retorna_resultados(self):
        resultados = self.recuperador.busca_vetorial("prazo de devolução", top_k=5)
        assert len(resultados) > 0
        assert "texto" in resultados[0]
        assert "score_vetorial" in resultados[0]

    def test_busca_bm25_retorna_resultados(self):
        resultados = self.recuperador.busca_bm25("férias funcionário", top_k=5)
        assert len(resultados) > 0
        assert "score_bm25" in resultados[0]

    def test_recuperacao_hibrida(self):
        resultados = self.recuperador.recuperar("garantia produto defeito", top_k=5)
        assert len(resultados) > 0
        assert "score_rrf" in resultados[0]
        assert resultados[0]["origem"] == "hibrido"

    def test_rrf_fusao(self):
        vet = [{"id": "a", "texto": "t", "metadados": {}}, {"id": "b", "texto": "t", "metadados": {}}]
        bm = [{"id": "b", "texto": "t", "metadados": {}}, {"id": "c", "texto": "t", "metadados": {}}]
        fusao = self.recuperador.reciprocal_rank_fusion(vet, bm)

        # "b" aparece em ambos, deve ter score maior
        ids = [d["id"] for d in fusao]
        assert "b" in ids
        score_b = next(d["score_rrf"] for d in fusao if d["id"] == "b")
        score_a = next(d["score_rrf"] for d in fusao if d["id"] == "a")
        assert score_b > score_a  # b aparece em ambos os rankings


class TestReranqueador:
    """Testa o reranqueador semântico."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.reranqueador = Reranqueador()

    def test_reranqueamento_ordena_por_relevancia(self):
        docs = [
            {"id": "1", "texto": "O céu é azul e o sol brilha.", "metadados": {}},
            {"id": "2", "texto": "A política de devolução permite troca em 30 dias.", "metadados": {}},
            {"id": "3", "texto": "Python é uma linguagem de programação.", "metadados": {}},
        ]
        resultado = self.reranqueador.reranquear("prazo de devolução", docs, top_k=3)

        assert len(resultado) == 3
        assert "score_reranqueamento" in resultado[0]
        # Documento sobre devolução deve ser o mais relevante
        assert resultado[0]["id"] == "2"

    def test_reranqueamento_lista_vazia(self):
        resultado = self.reranqueador.reranquear("teste", [], top_k=3)
        assert resultado == []

    def test_top_k_limita_resultados(self):
        docs = [{"id": str(i), "texto": f"Documento {i}", "metadados": {}} for i in range(10)]
        resultado = self.reranqueador.reranquear("documento", docs, top_k=3)
        assert len(resultado) == 3
