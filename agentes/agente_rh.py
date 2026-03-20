"""
Agente RH — responde dúvidas sobre benefícios, férias, jornada e políticas internas.
Utiliza RAG para fundamentar respostas no manual de RH.
"""

import time
import anthropic
from typing import Dict

from configuracao.config import ANTHROPIC_API_KEY, MODELO_CLAUDE
from rag.pipeline import obter_pipeline
from guardrails.validador_resposta import validar_resposta
from guardrails.filtro_pii import mascarar_pii
from observabilidade.rastreador import obter_rastreador

PROMPT_SISTEMA = """Você é o assistente de RH da empresa Vértice, uma empresa de moda urbana com ~1000 funcionários.

## Suas responsabilidades:
- Responder dúvidas sobre benefícios (VR, plano de saúde, desconto em produtos, etc.)
- Informar sobre política de férias (prazos, restrições, fracionamento)
- Esclarecer jornada de trabalho por unidade (sede, lojas, fábrica, CD)
- Orientar sobre horas extras e banco de horas
- Informar sobre processo de admissão e avaliação de desempenho
- Esclarecer código de conduta e medidas disciplinares
- Indicar canais de comunicação interna

## Regras:
- SEMPRE baseie suas respostas no CONTEXTO fornecido (manual de RH e documentos internos)
- Se a informação não estiver no contexto, oriente o funcionário a contatar o RH diretamente
- NUNCA divulgue informações salariais individuais de funcionários
- Seja profissional e acolhedor
- Para questões sensíveis (demissão, assédio, processos), oriente a buscar o RH presencialmente

## Contexto recuperado dos documentos:
{contexto}

## Fontes disponíveis:
{fontes}
"""


class AgenteRH:
    """Agente especializado em atendimento de RH via RAG."""

    def __init__(self):
        self.cliente_api = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.pipeline_rag = obter_pipeline()
        self.rastreador = obter_rastreador()

    def responder(self, mensagem: str, historico: list = None) -> Dict:
        """
        Processa dúvida de RH e gera resposta fundamentada.

        Args:
            mensagem: Pergunta do funcionário
            historico: Histórico da conversa

        Returns:
            Dict com resposta, fontes, confiança e métricas
        """
        inicio = time.time()

        with self.rastreador.trace("agente_rh", {"mensagem": mensagem[:100]}) as trace:
            # 1. Pipeline RAG
            resultado_rag = self.pipeline_rag.executar(mensagem)

            trace.span(
                "rag_pipeline",
                input=mensagem,
                output=f"{resultado_rag.total_chunks_reranqueados} chunks",
                metadata={"score": resultado_rag.score_confianca},
            )

            # 2. Monta prompt
            prompt_sistema = PROMPT_SISTEMA.format(
                contexto=resultado_rag.contexto or "Nenhum contexto encontrado.",
                fontes=resultado_rag.fontes_formatadas(),
            )

            # 3. Mensagens
            mensagens = []
            if historico:
                for msg in historico[-6:]:
                    mensagens.append(msg)
            mensagens.append({"role": "user", "content": mensagem})

            # 4. Geração
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

            # 5. Mascarar PII
            texto_log, pii = mascarar_pii(texto_resposta)

            trace.generation(
                "geracao_rh",
                modelo=MODELO_CLAUDE,
                input=mensagem,
                output=texto_log[:300],
                tokens_entrada=resposta_api.usage.input_tokens,
                tokens_saida=resposta_api.usage.output_tokens,
            )

            # 6. Validar
            validacao = validar_resposta(
                texto_resposta,
                resultado_rag.score_confianca,
                resultado_rag.fontes,
            )

            if not validacao["confiavel"] and validacao["recomendacao"]:
                texto_resposta += f"\n\n⚠️ {validacao['recomendacao']}"

            latencia_total = int((time.time() - inicio) * 1000)

            return {
                "resposta": texto_resposta,
                "agente": "rh",
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
