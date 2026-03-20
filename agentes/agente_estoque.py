"""
Agente Estoque — consulta disponibilidade de produtos via tool calling.
Usa SQL direto no banco, sem RAG.
"""

import time
import json
import anthropic
from typing import Dict

from configuracao.config import ANTHROPIC_API_KEY, MODELO_CLAUDE
from ferramentas.consulta_estoque import (
    consultar_estoque, obter_estoque_critico, resumo_estoque_por_loja
)
from observabilidade.rastreador import obter_rastreador

PROMPT_SISTEMA = """Você é o assistente de consulta de estoque da Vértice, uma empresa de moda urbana com 20 lojas próprias.

## Suas responsabilidades:
- Consultar disponibilidade de produtos por referência (SKU), tamanho, cor e loja
- Informar sobre estoque crítico (abaixo do mínimo)
- Fornecer resumos de estoque por loja
- Ajudar vendedores e gerentes com informações precisas

## Lojas da Vértice (20 unidades):
### São Paulo (8): Av. Paulista, Shopping Ibirapuera, Shopping Eldorado, Rua Oscar Freire, Shopping Morumbi, Shopping Center Norte, Jardins, Shopping Anália Franco
### Rio de Janeiro (4): Shopping RioSul, Barra Shopping, Shopping Tijuca, Village Mall
### Curitiba (4): Shopping Curitiba, Pátio Batel, Shopping Mueller, Rua XV de Novembro
### Florianópolis (4): Shopping Iguatemi, Beiramar Shopping, Shopping Itaguaçu, Norte Shopping Floripa

## Formato de SKU:
- Camisetas: VTX-CAM-001 a VTX-CAM-007
- Calças: VTX-CLC-001 a VTX-CLC-004
- Bonés: VTX-BON-001 a VTX-BON-004

## Regras:
- Sempre informe a quantidade exata encontrada
- Indique se o estoque está crítico (abaixo do mínimo configurado)
- Se não encontrar resultados, sugira verificar o SKU ou os filtros
- Seja preciso e objetivo — vendedores precisam de informação rápida
"""

# Definição das tools para Claude
TOOLS = [
    {
        "name": "consultar_estoque",
        "description": "Consulta o estoque de produtos com filtros opcionais. Use para verificar disponibilidade de produtos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "Código SKU do produto (ex: VTX-CAM-001)"
                },
                "nome": {
                    "type": "string",
                    "description": "Nome parcial do produto para busca"
                },
                "categoria": {
                    "type": "string",
                    "enum": ["camiseta", "calca", "bone"],
                    "description": "Categoria do produto"
                },
                "cor": {
                    "type": "string",
                    "description": "Cor do produto"
                },
                "tamanho": {
                    "type": "string",
                    "enum": ["PP", "P", "M", "G", "GG", "U"],
                    "description": "Tamanho do produto"
                },
                "loja": {
                    "type": "string",
                    "description": "Nome da loja (parcial aceito)"
                },
            },
            "required": [],
        },
    },
    {
        "name": "obter_estoque_critico",
        "description": "Retorna resumo de produtos com estoque abaixo do mínimo, agrupado por produto (SKU). Mostra quantas lojas estão afetadas e o deficit total. Use para identificar itens que precisam de reposição urgente.",
        "input_schema": {
            "type": "object",
            "properties": {
                "loja": {
                    "type": "string",
                    "description": "Filtrar por loja específica (opcional)"
                },
            },
            "required": [],
        },
    },
    {
        "name": "resumo_estoque_por_loja",
        "description": "Retorna um resumo do estoque total agrupado por loja, incluindo total de peças, SKUs e valor.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


class AgenteEstoque:
    """Agente especializado em consultas de estoque via tool calling."""

    def __init__(self):
        self.cliente_api = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.rastreador = obter_rastreador()

    def responder(self, mensagem: str, historico: list = None) -> Dict:
        """
        Processa consulta de estoque usando tool calling.

        Args:
            mensagem: Pergunta sobre estoque
            historico: Histórico da conversa

        Returns:
            Dict com resposta e métricas
        """
        inicio = time.time()

        with self.rastreador.trace("agente_estoque", {"mensagem": mensagem[:100]}) as trace:
            mensagens = []
            if historico:
                for msg in historico[-4:]:
                    mensagens.append(msg)
            mensagens.append({"role": "user", "content": mensagem})

            # Primeira chamada — Claude decide qual tool usar
            resposta = self.cliente_api.messages.create(
                model=MODELO_CLAUDE,
                max_tokens=1024,
                temperature=0,
                system=PROMPT_SISTEMA,
                messages=mensagens,
                tools=TOOLS,
            )

            tokens_total_entrada = resposta.usage.input_tokens
            tokens_total_saida = resposta.usage.output_tokens

            # Processa tool calls
            while resposta.stop_reason == "tool_use":
                tool_results = []
                for bloco in resposta.content:
                    if bloco.type == "tool_use":
                        resultado_tool = self._executar_tool(bloco.name, bloco.input)

                        trace.span(
                            f"tool_{bloco.name}",
                            input=json.dumps(bloco.input, ensure_ascii=False),
                            output=f"{len(resultado_tool)} resultados",
                        )

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": bloco.id,
                            "content": json.dumps(resultado_tool, ensure_ascii=False),
                        })

                # Segunda chamada com resultados das tools
                mensagens.append({"role": "assistant", "content": resposta.content})
                mensagens.append({"role": "user", "content": tool_results})

                resposta = self.cliente_api.messages.create(
                    model=MODELO_CLAUDE,
                    max_tokens=1024,
                    temperature=0,
                    system=PROMPT_SISTEMA,
                    messages=mensagens,
                    tools=TOOLS,
                )

                tokens_total_entrada += resposta.usage.input_tokens
                tokens_total_saida += resposta.usage.output_tokens

            # Extrai texto da resposta final
            texto_resposta = ""
            for bloco in resposta.content:
                if hasattr(bloco, "text"):
                    texto_resposta += bloco.text

            latencia_total = int((time.time() - inicio) * 1000)

            trace.generation(
                "geracao_estoque",
                modelo=MODELO_CLAUDE,
                input=mensagem,
                output=texto_resposta[:300],
                tokens_entrada=tokens_total_entrada,
                tokens_saida=tokens_total_saida,
            )

            return {
                "resposta": texto_resposta,
                "agente": "estoque",
                "fontes": [{"documento": "banco_estoque", "secao": "consulta SQL"}],
                "score_confianca": 0.95,
                "nivel_confianca": "alto",
                "confiavel": True,
                "tokens_entrada": tokens_total_entrada,
                "tokens_saida": tokens_total_saida,
                "latencia_total_ms": latencia_total,
            }

    def _executar_tool(self, nome: str, parametros: dict) -> list:
        """Executa a ferramenta solicitada pelo Claude."""
        if nome == "consultar_estoque":
            return consultar_estoque(**parametros)
        elif nome == "obter_estoque_critico":
            return obter_estoque_critico(**parametros)
        elif nome == "resumo_estoque_por_loja":
            return resumo_estoque_por_loja()
        else:
            return [{"erro": f"Ferramenta '{nome}' não encontrada"}]
