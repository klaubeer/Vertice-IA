"""
Detector de prompt injection.
Analisa mensagens do usuário antes de enviar aos agentes.
"""

import re
from typing import Tuple

# Padrões suspeitos que indicam tentativa de injection
PADROES_SUSPEITOS = [
    # Tentativas de alterar o comportamento do sistema
    r"(?i)ignor[ea]\s+(todas?\s+)?as?\s+(instru[çc][õo]es|regras|diretrizes)",
    r"(?i)esque[çc]a\s+(tudo|todas?\s+as?\s+instru)",
    r"(?i)voc[eê]\s+agora\s+[eé]\s+",
    r"(?i)finja\s+que\s+voc[eê]",
    r"(?i)a\s+partir\s+de\s+agora",
    r"(?i)novo\s+modo",
    r"(?i)modo\s+(desenvolvedor|admin|root|debug|jailbreak)",
    r"(?i)override\s+(system|instruc)",
    r"(?i)ignore\s+(previous|all|above|prior)\s+(instruc|prompt|rules)",
    r"(?i)you\s+are\s+now\s+",
    r"(?i)pretend\s+(you|to\s+be)",
    r"(?i)forget\s+(everything|all|previous)",
    r"(?i)jailbreak",
    r"(?i)dan\s+mode",
    r"(?i)system\s*prompt",

    # Tentativas de extração de informações do sistema
    r"(?i)qual\s+[eé]\s+seu\s+(prompt|system|instru[çc])",
    r"(?i)mostre?\s+(seu\s+)?(prompt|system|instruc)",
    r"(?i)repita\s+(seu\s+)?(prompt|system|instruc)",
    r"(?i)what\s+is\s+your\s+(system|prompt|instruc)",
    r"(?i)repeat\s+(your|the)\s+(system|prompt|instruc)",

    # Tentativas de execução de código
    r"(?i)(exec|eval|import\s+os|subprocess|__import__)",
    r"(?i)execute\s+(this|the\s+following)\s+code",
]

# Limiar de padrões detectados para bloquear
LIMIAR_BLOQUEIO = 1


def detectar_injection(mensagem: str) -> Tuple[bool, str, int]:
    """
    Analisa uma mensagem para detectar tentativas de prompt injection.

    Args:
        mensagem: Texto da mensagem do usuário

    Returns:
        Tupla (bloqueado, motivo, quantidade_padroes)
    """
    padroes_encontrados = []

    for padrao in PADROES_SUSPEITOS:
        if re.search(padrao, mensagem):
            padroes_encontrados.append(padrao)

    quantidade = len(padroes_encontrados)
    bloqueado = quantidade >= LIMIAR_BLOQUEIO

    if bloqueado:
        motivo = (
            "Mensagem bloqueada por suspeita de prompt injection. "
            f"{quantidade} padrão(ões) suspeito(s) detectado(s)."
        )
    else:
        motivo = ""

    return bloqueado, motivo, quantidade


def mensagem_bloqueio() -> str:
    """Retorna a mensagem padrão para quando uma injection é detectada."""
    return (
        "Desculpe, não posso processar essa solicitação. "
        "Sua mensagem contém padrões que não são compatíveis "
        "com o escopo do atendimento. "
        "Por favor, reformule sua pergunta sobre nossos produtos, "
        "políticas ou serviços."
    )
