"""
Reranqueador semântico usando Cross-Encoder.
Reordena os documentos recuperados por relevância real em relação à consulta.
"""

from typing import List, Dict, Optional

from sentence_transformers import CrossEncoder

from configuracao.config import MODELO_RERANQUEADOR, TOP_K_RERANQUEAMENTO


class Reranqueador:
    """Reranqueia documentos usando um cross-encoder."""

    def __init__(self):
        self._modelo: Optional[CrossEncoder] = None

    def _inicializar(self):
        """Carrega o modelo sob demanda."""
        if self._modelo is None:
            self._modelo = CrossEncoder(MODELO_RERANQUEADOR)

    def reranquear(
        self,
        consulta: str,
        documentos: List[Dict],
        top_k: int = TOP_K_RERANQUEAMENTO
    ) -> List[Dict]:
        """
        Reranqueia documentos usando cross-encoder.

        Args:
            consulta: Pergunta do usuário
            documentos: Lista de documentos recuperados
            top_k: Número de documentos a retornar

        Returns:
            Documentos reranqueados, do mais relevante ao menos relevante
        """
        self._inicializar()

        if not documentos:
            return []

        # Prepara pares (consulta, documento) para o cross-encoder
        pares = [(consulta, doc["texto"]) for doc in documentos]

        # Calcula scores
        scores = self._modelo.predict(pares)

        # Associa scores aos documentos
        for i, doc in enumerate(documentos):
            doc["score_reranqueamento"] = round(float(scores[i]), 4)

        # Ordena por score de reranqueamento (maior = mais relevante)
        documentos_ranqueados = sorted(
            documentos,
            key=lambda d: d["score_reranqueamento"],
            reverse=True
        )

        return documentos_ranqueados[:top_k]


# Instância global (singleton)
_reranqueador: Optional[Reranqueador] = None


def obter_reranqueador() -> Reranqueador:
    """Retorna a instância singleton do reranqueador."""
    global _reranqueador
    if _reranqueador is None:
        _reranqueador = Reranqueador()
    return _reranqueador
