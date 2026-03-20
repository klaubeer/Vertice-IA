"""
Métricas de avaliação do RAG.
Implementa Faithfulness, Relevância do Contexto e Correção.
"""

import json
import anthropic
from typing import Dict, List

from configuracao.config import ANTHROPIC_API_KEY, MODELO_CLAUDE


def avaliar_fidelidade(resposta: str, contexto: str) -> float:
    """
    Avalia se a resposta é fiel ao contexto recuperado (Faithfulness).
    Score de 0 a 1.
    """
    cliente = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Avalie se a RESPOSTA abaixo é fiel ao CONTEXTO fornecido.
A resposta deve conter apenas informações presentes no contexto.

CONTEXTO:
{contexto[:2000]}

RESPOSTA:
{resposta}

Responda APENAS com um JSON: {{"score": 0.0, "justificativa": "..."}}
Score: 1.0 = totalmente fiel, 0.0 = totalmente inventada."""

    resp = cliente.messages.create(
        model=MODELO_CLAUDE,
        max_tokens=200,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        resultado = json.loads(resp.content[0].text)
        return float(resultado.get("score", 0))
    except (json.JSONDecodeError, ValueError):
        return 0.0


def avaliar_relevancia_contexto(pergunta: str, contexto: str) -> float:
    """
    Avalia se o contexto recuperado é relevante para a pergunta.
    Score de 0 a 1.
    """
    cliente = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Avalie se o CONTEXTO recuperado é relevante para responder a PERGUNTA.

PERGUNTA:
{pergunta}

CONTEXTO:
{contexto[:2000]}

Responda APENAS com um JSON: {{"score": 0.0, "justificativa": "..."}}
Score: 1.0 = totalmente relevante, 0.0 = irrelevante."""

    resp = cliente.messages.create(
        model=MODELO_CLAUDE,
        max_tokens=200,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        resultado = json.loads(resp.content[0].text)
        return float(resultado.get("score", 0))
    except (json.JSONDecodeError, ValueError):
        return 0.0


def avaliar_correcao(pergunta: str, resposta: str, resposta_esperada: str) -> float:
    """
    Avalia se a resposta está factualmente correta comparando com a esperada.
    Score de 0 a 1.
    """
    cliente = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Compare a RESPOSTA GERADA com a RESPOSTA ESPERADA para a pergunta abaixo.
Avalie se a resposta gerada transmite a mesma informação essencial.

PERGUNTA:
{pergunta}

RESPOSTA ESPERADA:
{resposta_esperada}

RESPOSTA GERADA:
{resposta}

Responda APENAS com um JSON: {{"score": 0.0, "justificativa": "..."}}
Score: 1.0 = informação idêntica, 0.5 = parcialmente correta, 0.0 = incorreta."""

    resp = cliente.messages.create(
        model=MODELO_CLAUDE,
        max_tokens=200,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        resultado = json.loads(resp.content[0].text)
        return float(resultado.get("score", 0))
    except (json.JSONDecodeError, ValueError):
        return 0.0


def avaliar_fundamentacao(resposta: str, fontes: List[Dict]) -> float:
    """
    Avalia se a resposta cita ou é rastreável às fontes.
    Score de 0 a 1.
    """
    if not fontes:
        return 0.0

    # Verifica se algum nome de documento aparece na resposta ou se há fontes
    nomes_fontes = [f.get("documento", "") for f in fontes]
    score_base = min(1.0, len(fontes) / 3)  # Ter 3+ fontes = score base 1.0

    # Bonus se a resposta menciona fontes
    mencoes = sum(1 for nome in nomes_fontes if nome.lower() in resposta.lower())
    bonus = min(0.2, mencoes * 0.1)

    return min(1.0, score_base + bonus)
