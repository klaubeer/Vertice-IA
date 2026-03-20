"""
Pipeline completo de RAG — orquestra recuperação, reranqueamento e geração.
"""

import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from rag.recuperador import obter_recuperador
from rag.reranqueador import obter_reranqueador
from configuracao.config import LIMIAR_CONFIANCA, TOP_K_RECUPERACAO, TOP_K_RERANQUEAMENTO


@dataclass
class ResultadoRAG:
    """Resultado de uma consulta ao pipeline RAG."""
    consulta: str
    contexto: str
    fontes: List[Dict]
    score_confianca: float
    confiavel: bool
    latencia_recuperacao_ms: int = 0
    latencia_reranqueamento_ms: int = 0
    latencia_total_ms: int = 0
    total_chunks_recuperados: int = 0
    total_chunks_reranqueados: int = 0

    def fontes_formatadas(self) -> str:
        """Retorna as fontes formatadas como string legível."""
        if not self.fontes:
            return "Nenhuma fonte encontrada."
        linhas = []
        for f in self.fontes:
            doc = f.get("documento", "desconhecido")
            secao = f.get("secao", "")
            score = f.get("score_reranqueamento", 0)
            linha = f"- {doc}.md"
            if secao:
                linha += f" (seção: {secao})"
            linha += f" [relevância: {score:.2f}]"
            linhas.append(linha)
        return "\n".join(linhas)

    def to_dict(self) -> Dict:
        """Converte para dicionário serializável."""
        return {
            "consulta": self.consulta,
            "contexto": self.contexto,
            "fontes": self.fontes,
            "score_confianca": self.score_confianca,
            "confiavel": self.confiavel,
            "latencia_recuperacao_ms": self.latencia_recuperacao_ms,
            "latencia_reranqueamento_ms": self.latencia_reranqueamento_ms,
            "latencia_total_ms": self.latencia_total_ms,
            "total_chunks_recuperados": self.total_chunks_recuperados,
            "total_chunks_reranqueados": self.total_chunks_reranqueados,
        }


class PipelineRAG:
    """Pipeline completo de Retrieval-Augmented Generation."""

    def __init__(self):
        self.recuperador = obter_recuperador()
        self.reranqueador = obter_reranqueador()

    def executar(
        self,
        consulta: str,
        top_k_recuperacao: int = TOP_K_RECUPERACAO,
        top_k_reranqueamento: int = TOP_K_RERANQUEAMENTO,
    ) -> ResultadoRAG:
        """
        Executa o pipeline completo:
        1. Recuperação híbrida (vetorial + BM25 + RRF)
        2. Reranqueamento semântico (cross-encoder)
        3. Seleção de contexto e cálculo de confiança
        """
        inicio_total = time.time()

        # Etapa 1: Recuperação híbrida
        inicio_rec = time.time()
        documentos_recuperados = self.recuperador.recuperar(
            consulta, top_k=top_k_recuperacao
        )
        latencia_rec = int((time.time() - inicio_rec) * 1000)

        if not documentos_recuperados:
            return ResultadoRAG(
                consulta=consulta,
                contexto="",
                fontes=[],
                score_confianca=0.0,
                confiavel=False,
                latencia_recuperacao_ms=latencia_rec,
                latencia_total_ms=int((time.time() - inicio_total) * 1000),
            )

        # Etapa 2: Reranqueamento
        inicio_rerank = time.time()
        documentos_reranqueados = self.reranqueador.reranquear(
            consulta, documentos_recuperados, top_k=top_k_reranqueamento
        )
        latencia_rerank = int((time.time() - inicio_rerank) * 1000)

        # Etapa 3: Monta contexto e calcula confiança
        contexto = self._montar_contexto(documentos_reranqueados)
        score = self._calcular_confianca(documentos_reranqueados)
        fontes = [
            {
                "documento": d["metadados"].get("documento", ""),
                "secao": d["metadados"].get("secao", ""),
                "score_reranqueamento": d.get("score_reranqueamento", 0),
            }
            for d in documentos_reranqueados
        ]

        latencia_total = int((time.time() - inicio_total) * 1000)

        return ResultadoRAG(
            consulta=consulta,
            contexto=contexto,
            fontes=fontes,
            score_confianca=round(score, 4),
            confiavel=score >= LIMIAR_CONFIANCA,
            latencia_recuperacao_ms=latencia_rec,
            latencia_reranqueamento_ms=latencia_rerank,
            latencia_total_ms=latencia_total,
            total_chunks_recuperados=len(documentos_recuperados),
            total_chunks_reranqueados=len(documentos_reranqueados),
        )

    def _montar_contexto(self, documentos: List[Dict]) -> str:
        """Monta o contexto concatenando os documentos reranqueados."""
        partes = []
        for i, doc in enumerate(documentos, 1):
            fonte = doc["metadados"].get("documento", "desconhecido")
            secao = doc["metadados"].get("secao", "")
            cabecalho = f"[Fonte {i}: {fonte}"
            if secao:
                cabecalho += f" — {secao}"
            cabecalho += "]"
            partes.append(f"{cabecalho}\n{doc['texto']}")
        return "\n\n---\n\n".join(partes)

    def _calcular_confianca(self, documentos: List[Dict]) -> float:
        """
        Calcula confiança usando o score vetorial (cosine similarity) do top documento.
        O score_vetorial já está em [0, 1] e é produzido pelo modelo multilingual
        paraphrase-multilingual-MiniLM-L12-v2, bem calibrado para português.
        O cross-encoder é usado apenas para ORDENAR os documentos, não para confiança.

        Faixas esperadas:
        >= 0.85 → match explícito no documento
        >= 0.65 → match semântico bom
        < 0.50 → pouca relevância recuperada
        """
        if not documentos:
            return 0.0

        # Usa o score vetorial do top documento (pós-reranqueamento)
        top_score_vetorial = documentos[0].get("score_vetorial", 0.0)

        # Garante que está em [0, 1]
        return max(0.0, min(1.0, float(top_score_vetorial)))


# Instância global
_pipeline: Optional[PipelineRAG] = None


def obter_pipeline() -> PipelineRAG:
    """Retorna a instância singleton do pipeline RAG."""
    global _pipeline
    if _pipeline is None:
        _pipeline = PipelineRAG()
    return _pipeline
