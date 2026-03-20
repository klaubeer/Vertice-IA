"""
Filtro de PII (Personally Identifiable Information).
Mascara dados sensíveis nos logs e respostas.
"""

import re
from typing import Tuple


# Padrões de PII para mascarar
PADROES_PII = {
    "cpf": {
        "regex": r"\b\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}\b",
        "mascara": "***.***.***-**",
        "descricao": "CPF",
    },
    "telefone": {
        "regex": r"\(?\d{2}\)?\s?\d{4,5}[-.]?\d{4}\b",
        "mascara": "(**) *****-****",
        "descricao": "Telefone",
    },
    "email": {
        "regex": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "mascara": "****@****.***",
        "descricao": "E-mail",
    },
    "cep": {
        "regex": r"\b\d{5}[-.]?\d{3}\b",
        "mascara": "*****-***",
        "descricao": "CEP",
    },
    "cartao_credito": {
        "regex": r"\b\d{4}[\s.-]?\d{4}[\s.-]?\d{4}[\s.-]?\d{4}\b",
        "mascara": "**** **** **** ****",
        "descricao": "Cartão de crédito",
    },
    "rg": {
        "regex": r"\b\d{2}\.?\d{3}\.?\d{3}[-.]?\d{1,2}\b",
        "mascara": "**.***.***-*",
        "descricao": "RG",
    },
}


def mascarar_pii(texto: str) -> Tuple[str, list]:
    """
    Mascara dados sensíveis em um texto.

    Args:
        texto: Texto a ser processado

    Returns:
        Tupla (texto_mascarado, lista_de_pii_encontrados)
    """
    pii_encontrados = []
    texto_mascarado = texto

    for tipo, config in PADROES_PII.items():
        matches = re.findall(config["regex"], texto_mascarado)
        if matches:
            for match in matches:
                pii_encontrados.append({
                    "tipo": tipo,
                    "descricao": config["descricao"],
                    "valor_mascarado": config["mascara"],
                })
            texto_mascarado = re.sub(
                config["regex"],
                config["mascara"],
                texto_mascarado
            )

    return texto_mascarado, pii_encontrados


def contem_pii(texto: str) -> bool:
    """Verifica se o texto contém dados sensíveis."""
    for config in PADROES_PII.values():
        if re.search(config["regex"], texto):
            return True
    return False
