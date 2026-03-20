"""
Recuperador híbrido — combina busca vetorial (ChromaDB) com busca léxica (BM25).
Utiliza Reciprocal Rank Fusion para fundir os rankings.
"""

from typing import List, Dict, Optional
import json

import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

from configuracao.config import (
    CAMINHO_CHROMA, MODELO_EMBEDDINGS, TOP_K_RECUPERACAO
)
from rag.indexador import NOME_COLECAO


class RecuperadorHibrido:
    """Recuperador que combina busca vetorial e BM25."""

    def __init__(self):
        self._modelo_embeddings: Optional[SentenceTransformer] = None
        self._cliente_chroma: Optional[chromadb.PersistentClient] = None
        self._colecao = None
        self._bm25: Optional[BM25Okapi] = None
        self._documentos_bm25: List[Dict] = []
        self._inicializado = False

    def _inicializar(self):
        """Carrega modelos e índices sob demanda."""
        if self._inicializado:
            return

        # Modelo de embeddings
        self._modelo_embeddings = SentenceTransformer(MODELO_EMBEDDINGS)

        # ChromaDB
        self._cliente_chroma = chromadb.PersistentClient(path=str(CAMINHO_CHROMA))
        self._colecao = self._cliente_chroma.get_collection(NOME_COLECAO)

        # Carrega todos os documentos para BM25
        todos = self._colecao.get(include=["documents", "metadatas"])
        self._documentos_bm25 = [
            {
                "id": todos["ids"][i],
                "texto": todos["documents"][i],
                "metadados": todos["metadatas"][i],
            }
            for i in range(len(todos["ids"]))
        ]

        # Constrói índice BM25
        corpus_tokenizado = [
            doc["texto"].lower().split() for doc in self._documentos_bm25
        ]
        self._bm25 = BM25Okapi(corpus_tokenizado)

        self._inicializado = True

    def busca_vetorial(self, consulta: str, top_k: int = TOP_K_RECUPERACAO) -> List[Dict]:
        """Busca por similaridade semântica no ChromaDB."""
        self._inicializar()

        embedding = self._modelo_embeddings.encode([consulta]).tolist()
        resultados = self._colecao.query(
            query_embeddings=embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documentos = []
        for i in range(len(resultados["ids"][0])):
            score = 1 - resultados["distances"][0][i]  # cosine similarity
            documentos.append({
                "id": resultados["ids"][0][i],
                "texto": resultados["documents"][0][i],
                "metadados": resultados["metadatas"][0][i],
                "score_vetorial": round(score, 4),
                "origem": "vetorial",
            })
        return documentos

    def busca_bm25(self, consulta: str, top_k: int = TOP_K_RECUPERACAO) -> List[Dict]:
        """Busca léxica com BM25."""
        self._inicializar()

        tokens_consulta = consulta.lower().split()
        scores = self._bm25.get_scores(tokens_consulta)

        # Ordena por score e pega top_k
        indices_ordenados = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]

        documentos = []
        for idx in indices_ordenados:
            if scores[idx] > 0:
                doc = self._documentos_bm25[idx]
                documentos.append({
                    "id": doc["id"],
                    "texto": doc["texto"],
                    "metadados": doc["metadados"],
                    "score_bm25": round(float(scores[idx]), 4),
                    "origem": "bm25",
                })
        return documentos

    def reciprocal_rank_fusion(
        self,
        resultados_vetorial: List[Dict],
        resultados_bm25: List[Dict],
        k: int = 60
    ) -> List[Dict]:
        """
        Funde os rankings usando Reciprocal Rank Fusion (RRF).
        RRF(d) = sum(1 / (k + rank_i(d))) para cada ranking i.
        """
        scores_rrf = {}
        docs_por_id = {}

        # Score do ranking vetorial
        for rank, doc in enumerate(resultados_vetorial):
            doc_id = doc["id"]
            scores_rrf[doc_id] = scores_rrf.get(doc_id, 0) + 1 / (k + rank + 1)
            docs_por_id[doc_id] = doc

        # Score do ranking BM25
        for rank, doc in enumerate(resultados_bm25):
            doc_id = doc["id"]
            scores_rrf[doc_id] = scores_rrf.get(doc_id, 0) + 1 / (k + rank + 1)
            if doc_id not in docs_por_id:
                docs_por_id[doc_id] = doc

        # Ordena por score RRF
        ids_ordenados = sorted(scores_rrf, key=scores_rrf.get, reverse=True)

        resultados = []
        for doc_id in ids_ordenados:
            doc = docs_por_id[doc_id].copy()
            doc["score_rrf"] = round(scores_rrf[doc_id], 6)
            doc["origem"] = "hibrido"
            resultados.append(doc)

        return resultados

    def recuperar(self, consulta: str, top_k: int = TOP_K_RECUPERACAO) -> List[Dict]:
        """
        Pipeline completo de recuperação híbrida.
        1. Busca vetorial
        2. Busca BM25
        3. Fusão com RRF
        """
        self._inicializar()

        resultados_vetorial = self.busca_vetorial(consulta, top_k=top_k)
        resultados_bm25 = self.busca_bm25(consulta, top_k=top_k)

        # Funde os rankings
        resultados_fundidos = self.reciprocal_rank_fusion(
            resultados_vetorial, resultados_bm25
        )

        return resultados_fundidos[:top_k]


# Instância global (singleton)
_recuperador: Optional[RecuperadorHibrido] = None


def obter_recuperador() -> RecuperadorHibrido:
    """Retorna a instância singleton do recuperador."""
    global _recuperador
    if _recuperador is None:
        _recuperador = RecuperadorHibrido()
    return _recuperador
