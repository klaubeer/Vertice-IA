"""
Rastreador de observabilidade — integração com LangFuse.
Registra traces, spans e métricas de cada interação.
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from configuracao.config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST


class Rastreador:
    """Rastreia interações com o sistema para observabilidade."""

    def __init__(self):
        self._langfuse = None
        self._habilitado = bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)

        if self._habilitado:
            try:
                from langfuse import Langfuse
                self._langfuse = Langfuse(
                    public_key=LANGFUSE_PUBLIC_KEY,
                    secret_key=LANGFUSE_SECRET_KEY,
                    host=LANGFUSE_HOST,
                )
                print("[OK] LangFuse conectado")
            except Exception as e:
                print(f"[AVISO] LangFuse não disponível: {e}")
                self._habilitado = False

    @contextmanager
    def trace(self, nome: str, metadata: Optional[Dict] = None):
        """
        Context manager para rastrear uma operação completa.

        Uso:
            with rastreador.trace("atendimento_cliente") as t:
                t.span("recuperacao", input=consulta, output=docs)
                t.span("geracao", input=prompt, output=resposta)
        """
        trace_obj = TraceLocal(nome, metadata)

        if self._habilitado and self._langfuse:
            try:
                langfuse_trace = self._langfuse.trace(
                    name=nome,
                    metadata=metadata or {},
                )
                trace_obj._langfuse_trace = langfuse_trace
            except Exception:
                pass

        try:
            yield trace_obj
        finally:
            trace_obj.finalizar()
            if self._habilitado and self._langfuse:
                try:
                    self._langfuse.flush()
                except Exception:
                    pass

    def registrar_feedback(self, trace_id: str, score: float, comentario: str = ""):
        """Registra feedback do usuário para um trace."""
        if self._habilitado and self._langfuse:
            try:
                self._langfuse.score(
                    trace_id=trace_id,
                    name="feedback_usuario",
                    value=score,
                    comment=comentario,
                )
            except Exception:
                pass


class TraceLocal:
    """Trace local que registra spans e métricas."""

    def __init__(self, nome: str, metadata: Optional[Dict] = None):
        self.nome = nome
        self.metadata = metadata or {}
        self.spans: list = []
        self.inicio = time.time()
        self._langfuse_trace = None

    def span(
        self,
        nome: str,
        input: Any = None,
        output: Any = None,
        metadata: Optional[Dict] = None,
    ):
        """Registra um span (etapa) dentro do trace."""
        span_data = {
            "nome": nome,
            "timestamp": datetime.utcnow().isoformat(),
            "input": str(input)[:500] if input else None,
            "output": str(output)[:500] if output else None,
            "metadata": metadata or {},
        }
        self.spans.append(span_data)

        # Registra no LangFuse se disponível
        if self._langfuse_trace:
            try:
                self._langfuse_trace.span(
                    name=nome,
                    input=input,
                    output=output,
                    metadata=metadata or {},
                )
            except Exception:
                pass

    def generation(
        self,
        nome: str,
        modelo: str,
        input: Any = None,
        output: Any = None,
        tokens_entrada: int = 0,
        tokens_saida: int = 0,
        metadata: Optional[Dict] = None,
    ):
        """Registra uma chamada de geração (LLM)."""
        gen_data = {
            "nome": nome,
            "modelo": modelo,
            "tokens_entrada": tokens_entrada,
            "tokens_saida": tokens_saida,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.spans.append(gen_data)

        if self._langfuse_trace:
            try:
                self._langfuse_trace.generation(
                    name=nome,
                    model=modelo,
                    input=input,
                    output=output,
                    usage={
                        "input": tokens_entrada,
                        "output": tokens_saida,
                    },
                    metadata=metadata or {},
                )
            except Exception:
                pass

    def finalizar(self):
        """Finaliza o trace e calcula duração."""
        self.duracao_ms = int((time.time() - self.inicio) * 1000)

    def to_dict(self) -> Dict:
        """Exporta como dicionário."""
        return {
            "nome": self.nome,
            "metadata": self.metadata,
            "spans": self.spans,
            "duracao_ms": getattr(self, "duracao_ms", None),
        }


# Instância global
_rastreador: Optional[Rastreador] = None


def obter_rastreador() -> Rastreador:
    """Retorna a instância singleton do rastreador."""
    global _rastreador
    if _rastreador is None:
        _rastreador = Rastreador()
    return _rastreador
