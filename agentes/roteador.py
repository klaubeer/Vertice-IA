"""
Agente Roteador — classifica a intenção do usuário e direciona ao agente correto.
Primeiro ponto de contato do sistema multi-agente.
"""

import anthropic
from typing import Dict, Tuple

from configuracao.config import ANTHROPIC_API_KEY, MODELO_CLAUDE
from guardrails.detector_injection import detectar_injection, mensagem_bloqueio

PROMPT_ROTEADOR = """Você é o roteador de um sistema de atendimento da Vértice, uma empresa de moda urbana.

Sua função é analisar a mensagem do usuário e classificar:
1. O PERFIL do usuário (quem está perguntando)
2. A INTENÇÃO da mensagem (sobre o que é a dúvida)
3. O AGENTE mais adequado para responder

## Perfis possíveis:
- "cliente": pessoa que compra ou quer comprar produtos
- "vendedor": funcionário de loja que atende clientes
- "gerente": gerente de loja ou gestor
- "rh": funcionário com dúvida sobre RH/benefícios
- "sac": atendente do SAC buscando informações

## Agentes disponíveis:
- "cliente": dúvidas sobre políticas (devolução, envio, garantia), produtos, compras
- "estoque": consultas sobre quantidade em estoque, disponibilidade, estoque crítico
- "rh": dúvidas sobre benefícios, férias, jornada, código de conduta, processos RH
- "bi": métricas de atendimento, estatísticas, dashboards, performance

## Regras (em ordem de prioridade):
- Se menciona nome de produto + loja, ou pergunta sobre quantidade/disponibilidade de peça → agente "estoque"
- Se menciona SKU (ex: VTX-CAM-001), tamanho (P/M/G/GG), cor de produto + loja → agente "estoque"
- Se menciona "tem no estoque", "disponível na loja", "quantas peças", "estoque crítico" → agente "estoque"
- Se é sobre políticas, devolução, troca, envio, garantia, prazo de entrega → agente "cliente"
- Se é sobre férias, benefícios, vale, salário, jornada, RH, folga → agente "rh"
- Se pede métricas, estatísticas, relatórios, dashboard, performance → agente "bi"
- Se não for claro, use agente "cliente" como padrão

Responda APENAS no formato JSON (sem markdown):
{"perfil": "...", "intencao": "breve descrição", "agente": "...", "confianca": 0.0}
"""


class Roteador:
    """Classifica intenções e roteia para o agente adequado."""

    def __init__(self):
        self.cliente = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def classificar(self, mensagem: str) -> Dict:
        """
        Classifica a mensagem do usuário.

        Args:
            mensagem: Texto da mensagem

        Returns:
            Dict com perfil, intenção, agente e confiança
        """
        # Guardrail: verifica injection
        bloqueado, motivo, _ = detectar_injection(mensagem)
        if bloqueado:
            return {
                "perfil": "desconhecido",
                "intencao": "bloqueado",
                "agente": "bloqueado",
                "confianca": 0.0,
                "bloqueado": True,
                "motivo": motivo,
                "resposta_bloqueio": mensagem_bloqueio(),
            }

        # Classifica com Claude
        try:
            resposta = self.cliente.messages.create(
                model=MODELO_CLAUDE,
                max_tokens=200,
                temperature=0,
                system=PROMPT_ROTEADOR,
                messages=[{"role": "user", "content": mensagem}],
            )

            import json
            texto = resposta.content[0].text.strip()
            classificacao = json.loads(texto)

            # Valida campos
            agentes_validos = ["cliente", "estoque", "rh", "bi"]
            if classificacao.get("agente") not in agentes_validos:
                classificacao["agente"] = "cliente"

            classificacao["bloqueado"] = False
            classificacao["tokens_entrada"] = resposta.usage.input_tokens
            classificacao["tokens_saida"] = resposta.usage.output_tokens

            return classificacao

        except Exception as e:
            # Fallback: roteamento baseado em palavras-chave
            return self._classificar_fallback(mensagem)

    def _classificar_fallback(self, mensagem: str) -> Dict:
        """Classificação por palavras-chave quando a API falha."""
        msg = mensagem.lower()

        # Estoque
        palavras_estoque = [
            "estoque", "quantidade", "disponível", "referência", "ref.",
            "tem no", "tem na", "peça", "unidade", "sku",
            "vtx-", "jogger", "camiseta", "calça", "boné", "polo",
            "shopping", "loja", "tamanho", "preta", "branca", "cinza",
            "crítico", "reposição", "pp", " pg ", " mg ", " gg "
        ]
        if any(p in msg for p in palavras_estoque):
            return {
                "perfil": "vendedor",
                "intencao": "consulta de estoque",
                "agente": "estoque",
                "confianca": 0.6,
                "bloqueado": False,
            }

        # RH
        palavras_rh = [
            "férias", "benefício", "vale", "salário", "folha",
            "jornada", "hora extra", "admissão", "rh"
        ]
        if any(p in msg for p in palavras_rh):
            return {
                "perfil": "rh",
                "intencao": "dúvida de RH",
                "agente": "rh",
                "confianca": 0.6,
                "bloqueado": False,
            }

        # BI
        palavras_bi = [
            "métrica", "estatística", "relatório", "dashboard",
            "atendimento", "performance", "kpi"
        ]
        if any(p in msg for p in palavras_bi):
            return {
                "perfil": "gerente",
                "intencao": "consulta de métricas",
                "agente": "bi",
                "confianca": 0.6,
                "bloqueado": False,
            }

        # Default: cliente
        return {
            "perfil": "cliente",
            "intencao": "dúvida geral",
            "agente": "cliente",
            "confianca": 0.5,
            "bloqueado": False,
        }
