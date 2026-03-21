"""
Integração com Sentinela AI — envia traces para avaliação e observabilidade.

Usa threading (fire-and-forget) para não bloquear o fluxo principal.
Compatível com Streamlit, FastAPI e código síncrono puro.
"""

import logging
import threading
import uuid
from datetime import datetime
from typing import Any, Optional

import httpx

from configuracao.config import SENTINELA_API_KEY, SENTINELA_URL

logger = logging.getLogger("vertice.sentinela")

_habilitado = bool(SENTINELA_URL and SENTINELA_API_KEY)

if _habilitado:
    logger.info("Sentinela AI habilitado: %s", SENTINELA_URL)
else:
    logger.info("Sentinela AI desabilitado (SENTINELA_URL ou SENTINELA_API_KEY ausentes)")


def enviar_trace(
    nome: str,
    input: Any,
    output: Any,
    contexto: Optional[str] = None,
    modelo: Optional[str] = None,
    tokens_entrada: Optional[int] = None,
    tokens_saida: Optional[int] = None,
    latencia_ms: Optional[float] = None,
    custo_usd: Optional[float] = None,
    metadata: Optional[dict] = None,
) -> None:
    """
    Envia um trace ao Sentinela em background (fire-and-forget).

    Nunca lança exceções — o sistema monitorado não pode ser afetado
    por problemas de observabilidade.

    Args:
        nome: Nome da operação (ex: "agente-cliente", "roteador")
        input: Texto de entrada / pergunta do usuário
        output: Texto de saída / resposta gerada
        contexto: Contexto RAG recuperado (para avaliação de faithfulness)
        modelo: Identificador do modelo LLM usado
        tokens_entrada: Tokens consumidos na entrada
        tokens_saida: Tokens consumidos na saída
        latencia_ms: Latência total em milissegundos
        custo_usd: Custo estimado em USD
        metadata: Metadados adicionais (dict)
    """
    if not _habilitado:
        return

    payload = {
        "id": str(uuid.uuid4()),
        "projeto": "vertice-ai",
        "nome": nome,
        "input": input if isinstance(input, str) else str(input),
        "output": output if isinstance(output, str) else str(output),
        "contexto": contexto,
        "modelo": modelo,
        "tokens_entrada": tokens_entrada,
        "tokens_saida": tokens_saida,
        "latencia_ms": latencia_ms,
        "custo_usd": custo_usd,
        "metadata": metadata or {},
        "criado_em": datetime.utcnow().isoformat(),
    }

    def _enviar() -> None:
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.post(
                    f"{SENTINELA_URL}/traces",
                    json=payload,
                    headers={
                        "X-Api-Key": SENTINELA_API_KEY,
                        "Content-Type": "application/json",
                    },
                )
                r.raise_for_status()
                logger.debug("Sentinela: trace %s enviado", payload["id"])
        except Exception as exc:
            # Falha silenciosa — observabilidade nunca afeta o produto
            logger.debug("Sentinela: falha ao enviar trace — %s", exc)

    threading.Thread(target=_enviar, daemon=True).start()
