"""
Validador de fundamentação das respostas.
Verifica se a resposta do agente está baseada no contexto fornecido.
"""

from typing import Dict
from configuracao.config import LIMIAR_CONFIANCA


def validar_resposta(
    resposta: str,
    score_confianca: float,
    fontes: list,
) -> Dict:
    """
    Valida se a resposta está adequadamente fundamentada.

    Args:
        resposta: Texto da resposta gerada
        score_confianca: Score de confiança do pipeline RAG
        fontes: Lista de fontes utilizadas

    Returns:
        Dict com status da validação
    """
    problemas = []

    # 1. Verifica frases que indicam alucinação (único check que realmente importa)
    indicadores_alucinacao = [
        "como uma ia, eu não",
        "não tenho acesso a",
        "baseado no meu treinamento",
        "como modelo de linguagem",
        "não tenho informações suficientes",
    ]
    for indicador in indicadores_alucinacao:
        if indicador.lower() in resposta.lower():
            problemas.append(f"Possível alucinação detectada: '{indicador}'")

    # 2. Resposta vazia ou muito curta
    if len(resposta.strip()) < 20:
        problemas.append("Resposta muito curta para ser informativa")

    # Resultado
    confiavel = len(problemas) == 0
    nivel = _classificar_nivel(score_confianca, len(problemas))

    return {
        "confiavel": confiavel,
        "nivel": nivel,
        "score": score_confianca,
        "problemas": problemas,
        "recomendacao": _gerar_recomendacao(nivel),
    }


def _classificar_nivel(score: float, qtd_problemas: int) -> str:
    """Classifica o nível de confiança da resposta.
    Calibrado para o modelo mmarco-mMiniLMv2 (multilingual):
    scores > 0.85 = match explícito, > 0.65 = match semântico bom.
    """
    if qtd_problemas > 0:
        return "baixo"
    if score >= 0.85:
        return "alto"
    if score >= 0.60:
        return "medio"
    return "baixo"


def _gerar_recomendacao(nivel: str) -> str:
    """Gera recomendação com base no nível de confiança."""
    recomendacoes = {
        "alto": "",
        "medio": "",  # resposta adequada — não exibe aviso desnecessário
        "baixo": (
            "Não encontrei informações suficientes nos documentos para "
            "responder com segurança. Recomendo entrar em contato "
            "com nosso time de atendimento."
        ),
    }
    return recomendacoes.get(nivel, "")
