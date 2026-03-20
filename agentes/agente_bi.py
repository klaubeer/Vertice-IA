"""
Agente BI — fornece métricas e analytics sobre atendimentos via tool calling.
"""

import time
import json
import anthropic
from typing import Dict

from configuracao.config import ANTHROPIC_API_KEY, MODELO_CLAUDE
from ferramentas.consulta_metricas import (
    resumo_atendimentos, atendimentos_por_agente,
    atendimentos_por_perfil, perguntas_frequentes
)
from ferramentas.consulta_estoque import obter_estoque_critico, resumo_estoque_por_loja
from observabilidade.rastreador import obter_rastreador

PROMPT_SISTEMA = """Você é o assistente de Business Intelligence da Vértice.

## Suas responsabilidades:
- Fornecer métricas sobre atendimentos realizados pela IA
- Informar taxa de resolução, tempo médio, volume de atendimentos
- Identificar padrões: dúvidas mais comuns, agentes mais acionados
- Apresentar dados de estoque crítico para gestores
- Apoiar decisões com dados concretos

## Regras:
- Sempre apresente números concretos dos dados consultados
- Formate os dados de forma clara (use listas ou tabelas quando apropriado)
- Compare com períodos anteriores quando possível
- Destaque alertas (estoque crítico, taxa de resolução baixa)
- Seja analítico e objetivo — gestores querem dados, não narrativa
"""

TOOLS = [
    {
        "name": "resumo_atendimentos",
        "description": "Retorna métricas agregadas dos atendimentos: total, taxa de resolução, tempo médio, feedbacks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dias": {
                    "type": "integer",
                    "description": "Número de dias para analisar (padrão: 30)",
                    "default": 30,
                },
            },
            "required": [],
        },
    },
    {
        "name": "atendimentos_por_agente",
        "description": "Retorna a quantidade de atendimentos distribuída por agente (cliente, estoque, rh, bi).",
        "input_schema": {
            "type": "object",
            "properties": {
                "dias": {"type": "integer", "default": 30},
            },
            "required": [],
        },
    },
    {
        "name": "atendimentos_por_perfil",
        "description": "Retorna a quantidade de atendimentos por perfil de usuário (cliente, vendedor, gerente, rh).",
        "input_schema": {
            "type": "object",
            "properties": {
                "dias": {"type": "integer", "default": 30},
            },
            "required": [],
        },
    },
    {
        "name": "perguntas_frequentes",
        "description": "Retorna as perguntas mais recentes e frequentes feitas ao sistema.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dias": {"type": "integer", "default": 30},
                "top_k": {"type": "integer", "default": 10},
            },
            "required": [],
        },
    },
    {
        "name": "obter_estoque_critico",
        "description": "Retorna produtos com estoque abaixo do mínimo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "loja": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name": "resumo_estoque_por_loja",
        "description": "Retorna resumo do estoque por loja (total peças, valor).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

# Mapeamento de tools para funções
FUNCOES_TOOLS = {
    "resumo_atendimentos": resumo_atendimentos,
    "atendimentos_por_agente": atendimentos_por_agente,
    "atendimentos_por_perfil": atendimentos_por_perfil,
    "perguntas_frequentes": perguntas_frequentes,
    "obter_estoque_critico": obter_estoque_critico,
    "resumo_estoque_por_loja": resumo_estoque_por_loja,
}


class AgenteBI:
    """Agente de BI com tool calling para métricas."""

    def __init__(self):
        self.cliente_api = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.rastreador = obter_rastreador()

    def responder(self, mensagem: str, historico: list = None) -> Dict:
        inicio = time.time()

        with self.rastreador.trace("agente_bi", {"mensagem": mensagem[:100]}) as trace:
            mensagens = []
            if historico:
                for msg in historico[-4:]:
                    mensagens.append(msg)
            mensagens.append({"role": "user", "content": mensagem})

            resposta = self.cliente_api.messages.create(
                model=MODELO_CLAUDE,
                max_tokens=1500,
                temperature=0,
                system=PROMPT_SISTEMA,
                messages=mensagens,
                tools=TOOLS,
            )

            tokens_entrada = resposta.usage.input_tokens
            tokens_saida = resposta.usage.output_tokens

            # Processa tool calls
            while resposta.stop_reason == "tool_use":
                tool_results = []
                for bloco in resposta.content:
                    if bloco.type == "tool_use":
                        func = FUNCOES_TOOLS.get(bloco.name)
                        resultado = func(**bloco.input) if func else {"erro": "tool não encontrada"}

                        trace.span(
                            f"tool_{bloco.name}",
                            input=json.dumps(bloco.input, ensure_ascii=False),
                            output=str(resultado)[:300],
                        )

                        # Serializa resultado
                        if isinstance(resultado, dict):
                            resultado_str = json.dumps(resultado, ensure_ascii=False)
                        elif isinstance(resultado, list):
                            resultado_str = json.dumps(resultado, ensure_ascii=False)
                        else:
                            resultado_str = str(resultado)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": bloco.id,
                            "content": resultado_str,
                        })

                mensagens.append({"role": "assistant", "content": resposta.content})
                mensagens.append({"role": "user", "content": tool_results})

                resposta = self.cliente_api.messages.create(
                    model=MODELO_CLAUDE,
                    max_tokens=1500,
                    temperature=0,
                    system=PROMPT_SISTEMA,
                    messages=mensagens,
                    tools=TOOLS,
                )
                tokens_entrada += resposta.usage.input_tokens
                tokens_saida += resposta.usage.output_tokens

            texto_resposta = ""
            for bloco in resposta.content:
                if hasattr(bloco, "text"):
                    texto_resposta += bloco.text

            latencia_total = int((time.time() - inicio) * 1000)

            trace.generation(
                "geracao_bi",
                modelo=MODELO_CLAUDE,
                input=mensagem,
                output=texto_resposta[:300],
                tokens_entrada=tokens_entrada,
                tokens_saida=tokens_saida,
            )

            return {
                "resposta": texto_resposta,
                "agente": "bi",
                "fontes": [{"documento": "banco_metricas", "secao": "analytics"}],
                "score_confianca": 0.90,
                "nivel_confianca": "alto",
                "confiavel": True,
                "tokens_entrada": tokens_entrada,
                "tokens_saida": tokens_saida,
                "latencia_total_ms": latencia_total,
            }
