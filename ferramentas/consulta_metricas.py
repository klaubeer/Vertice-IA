"""
Ferramenta de consulta de métricas — usada pelo Agente BI via tool calling.
"""

from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from banco.modelos import Atendimento, Mensagem
from configuracao.config import CAMINHO_BANCO


def _obter_session():
    engine = create_engine(f"sqlite:///{CAMINHO_BANCO}", echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def resumo_atendimentos(dias: int = 30) -> Dict:
    """
    Retorna resumo dos atendimentos dos últimos N dias.

    Args:
        dias: Número de dias para considerar

    Returns:
        Dict com métricas agregadas
    """
    session = _obter_session()
    try:
        data_inicio = datetime.utcnow() - timedelta(days=dias)

        atendimentos = (
            session.query(Atendimento)
            .filter(Atendimento.data_inicio >= data_inicio)
            .all()
        )

        if not atendimentos:
            return {
                "periodo_dias": dias,
                "total_atendimentos": 0,
                "mensagem": "Nenhum atendimento registrado no período.",
            }

        total = len(atendimentos)
        resolvidos = sum(1 for a in atendimentos if a.resolvido)
        encaminhados = sum(1 for a in atendimentos if a.encaminhado_humano)
        feedbacks_positivos = sum(
            1 for a in atendimentos if a.feedback_usuario == "positivo"
        )
        feedbacks_negativos = sum(
            1 for a in atendimentos if a.feedback_usuario == "negativo"
        )

        # Duração média
        duracoes = [
            a.duracao_segundos for a in atendimentos
            if a.duracao_segundos is not None
        ]
        duracao_media = sum(duracoes) / len(duracoes) if duracoes else 0

        # Score médio
        scores = [
            a.score_confianca_medio for a in atendimentos
            if a.score_confianca_medio is not None
        ]
        score_medio = sum(scores) / len(scores) if scores else 0

        return {
            "periodo_dias": dias,
            "total_atendimentos": total,
            "resolvidos": resolvidos,
            "taxa_resolucao": round(resolvidos / total * 100, 1) if total else 0,
            "encaminhados_humano": encaminhados,
            "taxa_encaminhamento": round(encaminhados / total * 100, 1) if total else 0,
            "feedbacks_positivos": feedbacks_positivos,
            "feedbacks_negativos": feedbacks_negativos,
            "duracao_media_segundos": round(duracao_media, 1),
            "score_confianca_medio": round(score_medio, 4),
        }
    finally:
        session.close()


def atendimentos_por_agente(dias: int = 30) -> List[Dict]:
    """Retorna contagem de atendimentos por agente."""
    session = _obter_session()
    try:
        data_inicio = datetime.utcnow() - timedelta(days=dias)

        resultados = (
            session.query(
                Atendimento.agente_utilizado,
                func.count(Atendimento.id).label("total"),
            )
            .filter(Atendimento.data_inicio >= data_inicio)
            .group_by(Atendimento.agente_utilizado)
            .all()
        )

        return [
            {"agente": r.agente_utilizado, "total": r.total}
            for r in resultados
        ]
    finally:
        session.close()


def atendimentos_por_perfil(dias: int = 30) -> List[Dict]:
    """Retorna contagem de atendimentos por perfil de usuário."""
    session = _obter_session()
    try:
        data_inicio = datetime.utcnow() - timedelta(days=dias)

        resultados = (
            session.query(
                Atendimento.perfil_usuario,
                func.count(Atendimento.id).label("total"),
            )
            .filter(Atendimento.data_inicio >= data_inicio)
            .group_by(Atendimento.perfil_usuario)
            .all()
        )

        return [
            {"perfil": r.perfil_usuario, "total": r.total}
            for r in resultados
        ]
    finally:
        session.close()


def perguntas_frequentes(dias: int = 30, top_k: int = 10) -> List[Dict]:
    """Retorna as perguntas mais frequentes dos atendimentos."""
    session = _obter_session()
    try:
        data_inicio = datetime.utcnow() - timedelta(days=dias)

        mensagens = (
            session.query(Mensagem)
            .join(Atendimento)
            .filter(
                Atendimento.data_inicio >= data_inicio,
                Mensagem.papel == "usuario",
            )
            .order_by(Mensagem.timestamp.desc())
            .limit(200)
            .all()
        )

        return [
            {
                "mensagem": m.conteudo[:150],
                "agente": m.agente,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            }
            for m in mensagens[:top_k]
        ]
    finally:
        session.close()
