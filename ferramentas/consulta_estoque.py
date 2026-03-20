"""
Ferramenta de consulta de estoque — usada pelo Agente Estoque via tool calling.
"""

from typing import Optional, List, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from banco.modelos import Estoque
from configuracao.config import CAMINHO_BANCO


def _obter_session():
    """Cria uma sessão com o banco de dados."""
    engine = create_engine(f"sqlite:///{CAMINHO_BANCO}", echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def consultar_estoque(
    sku: Optional[str] = None,
    nome: Optional[str] = None,
    categoria: Optional[str] = None,
    cor: Optional[str] = None,
    tamanho: Optional[str] = None,
    loja: Optional[str] = None,
) -> List[Dict]:
    """
    Consulta o estoque com filtros opcionais.

    Args:
        sku: Código SKU do produto (ex: VTX-CAM-001)
        nome: Nome parcial do produto
        categoria: camiseta, calca ou bone
        cor: Cor do produto
        tamanho: PP, P, M, G, GG ou U
        loja: Nome da loja

    Returns:
        Lista de itens encontrados
    """
    session = _obter_session()
    try:
        query = session.query(Estoque)

        if sku:
            query = query.filter(Estoque.sku.ilike(f"%{sku}%"))
        if nome:
            query = query.filter(Estoque.nome.ilike(f"%{nome}%"))
        if categoria:
            query = query.filter(Estoque.categoria.ilike(f"%{categoria}%"))
        if cor:
            query = query.filter(Estoque.cor.ilike(f"%{cor}%"))
        if tamanho:
            query = query.filter(Estoque.tamanho.ilike(f"%{tamanho}%"))
        if loja:
            query = query.filter(Estoque.loja.ilike(f"%{loja}%"))

        resultados = query.limit(100).all()

        return [
            {
                "sku": r.sku,
                "nome": r.nome,
                "categoria": r.categoria,
                "cor": r.cor,
                "tamanho": r.tamanho,
                "preco": r.preco,
                "loja": r.loja,
                "quantidade": r.quantidade,
                "estoque_minimo": r.estoque_minimo,
                "estoque_critico": r.estoque_critico,
            }
            for r in resultados
        ]
    finally:
        session.close()


def obter_estoque_critico(loja: Optional[str] = None) -> List[Dict]:
    """
    Retorna resumo de produtos com estoque crítico, agrupado por SKU/produto.
    Evita retornar centenas de linhas individuais — agrega por produto.

    Args:
        loja: Filtrar por loja específica (opcional)

    Returns:
        Lista de produtos críticos com contagem de lojas afetadas (máx. 30 itens)
    """
    session = _obter_session()
    try:
        from sqlalchemy import func, case

        query = session.query(
            Estoque.sku,
            Estoque.nome,
            Estoque.categoria,
            Estoque.cor,
            func.count(Estoque.id).label("registros_criticos"),
            func.min(Estoque.quantidade).label("qtd_minima"),
            func.max(Estoque.quantidade).label("qtd_maxima"),
            func.min(Estoque.estoque_minimo).label("minimo_config"),
            func.sum(Estoque.estoque_minimo - Estoque.quantidade).label("deficit_total"),
        ).filter(
            Estoque.quantidade < Estoque.estoque_minimo
        )

        if loja:
            query = query.filter(Estoque.loja.ilike(f"%{loja}%"))

        resultados = (
            query
            .group_by(Estoque.sku, Estoque.nome, Estoque.categoria, Estoque.cor)
            .order_by(func.sum(Estoque.estoque_minimo - Estoque.quantidade).desc())
            .limit(30)
            .all()
        )

        return [
            {
                "sku": r.sku,
                "nome": r.nome,
                "categoria": r.categoria,
                "cor": r.cor,
                "lojas_afetadas": int(r.registros_criticos),
                "quantidade_minima": int(r.qtd_minima),
                "quantidade_maxima": int(r.qtd_maxima),
                "estoque_minimo_configurado": int(r.minimo_config),
                "deficit_total": int(r.deficit_total),
            }
            for r in resultados
        ]
    finally:
        session.close()


def resumo_estoque_por_loja() -> List[Dict]:
    """Retorna resumo de estoque agrupado por loja."""
    session = _obter_session()
    try:
        from sqlalchemy import func
        resultados = (
            session.query(
                Estoque.loja,
                func.sum(Estoque.quantidade).label("total_pecas"),
                func.count(Estoque.id).label("total_skus"),
                func.sum(
                    Estoque.quantidade * Estoque.preco
                ).label("valor_total"),
            )
            .group_by(Estoque.loja)
            .all()
        )

        return [
            {
                "loja": r.loja,
                "total_pecas": int(r.total_pecas),
                "total_skus": int(r.total_skus),
                "valor_total": round(float(r.valor_total), 2),
            }
            for r in resultados
        ]
    finally:
        session.close()
