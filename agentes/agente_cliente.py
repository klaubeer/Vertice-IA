"""
Agente Cliente — responde dúvidas sobre políticas, produtos e serviços.
Utiliza RAG para fundamentar respostas em documentos.
"""

import time
import json
import anthropic
from typing import Dict

from configuracao.config import ANTHROPIC_API_KEY, MODELO_CLAUDE, LIMIAR_CONFIANCA
from rag.pipeline import obter_pipeline
from guardrails.validador_resposta import validar_resposta
from guardrails.filtro_pii import mascarar_pii
from observabilidade.rastreador import obter_rastreador
from observabilidade.sentinela import enviar_trace as sentinela_trace

PROMPT_SISTEMA = """Você é o assistente de atendimento ao cliente da Vértice, uma marca brasileira de moda urbana.

## Suas responsabilidades:
- Responder dúvidas sobre políticas de devolução, troca, envio e garantia
- Informar sobre prazos, condições e processos
- Orientar clientes sobre como resolver problemas com pedidos
- Ser cordial, claro e objetivo

## Regras importantes:
- SEMPRE baseie suas respostas no CONTEXTO fornecido abaixo
- Se o contexto não contém a informação necessária, diga claramente que não encontrou a informação e sugira contato com o SAC
- NUNCA invente informações que não estejam no contexto
- Cite as fontes quando relevante (ex: "De acordo com nossa política de devolução...")
- Seja empático com o cliente
- Use linguagem acessível, evite jargões técnicos

## Contexto recuperado dos documentos:
{contexto}

## Fontes disponíveis:
{fontes}
"""


class AgenteCliente:
    """Agente especializado em atendimento ao cliente via RAG."""

    def __init__(self):
        self.cliente_api = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.pipeline_rag = obter_pipeline()
        self.rastreador = obter_rastreador()

    def responder(self, mensagem: str, historico: list = None) -> Dict:
        """
        Processa a mensagem do cliente e gera resposta fundamentada.

        Args:
            mensagem: Pergunta do cliente
            historico: Histórico de mensagens da conversa

        Returns:
            Dict com resposta, fontes, confiança e métricas
        """
        inicio = time.time()

        with self.rastreador.trace("agente_cliente", {"mensagem": mensagem[:100]}) as trace:
            # 1. Pipeline RAG — recupera e reranqueia documentos
            resultado_rag = self.pipeline_rag.executar(mensagem)

            trace.span(
                "rag_pipeline",
                input=mensagem,
                output=f"{resultado_rag.total_chunks_reranqueados} chunks",
                metadata={
                    "score_confianca": resultado_rag.score_confianca,
                    "latencia_ms": resultado_rag.latencia_total_ms,
                },
            )

            # 2. Monta o prompt com contexto
            prompt_sistema = PROMPT_SISTEMA.format(
                contexto=resultado_rag.contexto or "Nenhum contexto encontrado.",
                fontes=resultado_rag.fontes_formatadas(),
            )

            # 3. Prepara mensagens
            mensagens = []
            if historico:
                for msg in historico[-6:]:  # Últimas 6 mensagens
                    mensagens.append(msg)
            mensagens.append({"role": "user", "content": mensagem})

            # 4. Geração com Claude
            inicio_gen = time.time()
            resposta_api = self.cliente_api.messages.create(
                model=MODELO_CLAUDE,
                max_tokens=1024,
                temperature=0.3,
                system=prompt_sistema,
                messages=mensagens,
            )
            latencia_gen = int((time.time() - inicio_gen) * 1000)

            texto_resposta = resposta_api.content[0].text

            trace.generation(
                "geracao_resposta",
                modelo=MODELO_CLAUDE,
                input=mensagem,
                output=texto_resposta[:300],
                tokens_entrada=resposta_api.usage.input_tokens,
                tokens_saida=resposta_api.usage.output_tokens,
            )

            # 5. Mascarar PII nos logs
            texto_log, _ = mascarar_pii(texto_resposta)

            # 6. Validar fundamentação
            validacao = validar_resposta(
                texto_resposta,
                resultado_rag.score_confianca,
                resultado_rag.fontes,
            )

            # Se confiança baixa, adiciona aviso
            if not validacao["confiavel"] and validacao["recomendacao"]:
                texto_resposta += f"\n\n⚠️ {validacao['recomendacao']}"

            latencia_total = int((time.time() - inicio) * 1000)

            # Envia trace ao Sentinela para avaliação automática (fire-and-forget)
            sentinela_trace(
                nome="agente-cliente",
                input=mensagem,
                output=texto_resposta,
                contexto=resultado_rag.contexto,
                modelo=MODELO_CLAUDE,
                tokens_entrada=resposta_api.usage.input_tokens,
                tokens_saida=resposta_api.usage.output_tokens,
                latencia_ms=latencia_total,
                metadata={
                    "score_confianca_rag": resultado_rag.score_confianca,
                    "confiavel": resultado_rag.confiavel,
                    "chunks_recuperados": resultado_rag.total_chunks_recuperados,
                    "chunks_reranqueados": resultado_rag.total_chunks_reranqueados,
                },
            )

            return {
                "resposta": texto_resposta,
                "agente": "cliente",
                "fontes": resultado_rag.fontes,
                "score_confianca": resultado_rag.score_confianca,
                "nivel_confianca": validacao["nivel"],
                "confiavel": validacao["confiavel"],
                "tokens_entrada": resposta_api.usage.input_tokens,
                "tokens_saida": resposta_api.usage.output_tokens,
                "latencia_rag_ms": resultado_rag.latencia_total_ms,
                "latencia_geracao_ms": latencia_gen,
                "latencia_total_ms": latencia_total,
            }
