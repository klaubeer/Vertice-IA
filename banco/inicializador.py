"""
Inicializa o banco de dados SQLite e popula com dados fictícios.
Uso: python -m banco.inicializador
"""

import csv
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from banco.modelos import Base, Estoque, Funcionario
from configuracao.config import CAMINHO_BANCO, CAMINHO_DADOS


def criar_engine():
    """Cria a engine SQLAlchemy apontando para o banco SQLite."""
    CAMINHO_BANCO.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{CAMINHO_BANCO}", echo=False)


def criar_tabelas(engine):
    """Cria todas as tabelas definidas nos modelos."""
    Base.metadata.create_all(engine)
    print(f"[OK] Tabelas criadas em {CAMINHO_BANCO}")


def carregar_estoque(session):
    """Carrega dados de estoque a partir do CSV."""
    caminho_csv = CAMINHO_DADOS / "base_estoque.csv"
    if not caminho_csv.exists():
        print(f"[AVISO] Arquivo {caminho_csv} não encontrado. Pulando estoque.")
        return

    # Limpa dados existentes
    session.query(Estoque).delete()

    with open(caminho_csv, "r", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        registros = []
        for linha in leitor:
            registros.append(Estoque(
                sku=linha["sku"],
                nome=linha["nome"],
                categoria=linha["categoria"],
                cor=linha["cor"],
                tamanho=linha["tamanho"],
                preco=float(linha["preco"]),
                custo=float(linha["custo"]),
                estoque_minimo=int(linha["estoque_minimo"]),
                loja=linha["loja"],
                quantidade=int(linha["quantidade"]),
            ))
        session.add_all(registros)
        session.commit()
        print(f"[OK] {len(registros)} registros de estoque carregados")


def carregar_funcionarios(session):
    """Carrega dados de funcionários a partir do CSV."""
    caminho_csv = CAMINHO_DADOS / "base_funcionarios.csv"
    if not caminho_csv.exists():
        print(f"[AVISO] Arquivo {caminho_csv} não encontrado. Pulando funcionários.")
        return

    # Limpa dados existentes
    session.query(Funcionario).delete()

    with open(caminho_csv, "r", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        registros = []
        for linha in leitor:
            registros.append(Funcionario(
                matricula=linha["matricula"],
                nome=linha["nome"],
                cargo=linha["cargo"],
                departamento=linha["departamento"],
                unidade=linha["unidade"],
                data_admissao=linha["data_admissao"],
                salario=float(linha["salario"]),
                status=linha["status"],
            ))
        session.add_all(registros)
        session.commit()
        print(f"[OK] {len(registros)} funcionários carregados")


def inicializar():
    """Executa a inicialização completa do banco."""
    print("=" * 50)
    print("Inicializando banco de dados — Vértice IA")
    print("=" * 50)

    engine = criar_engine()
    criar_tabelas(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        carregar_estoque(session)
        carregar_funcionarios(session)
        print("=" * 50)
        print("[OK] Banco de dados inicializado com sucesso!")
    except Exception as e:
        session.rollback()
        print(f"[ERRO] Falha na inicialização: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    inicializar()
