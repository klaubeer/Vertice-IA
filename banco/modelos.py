"""
Modelos do banco de dados — SQLAlchemy.
Tabelas: estoque, funcionarios, atendimentos, mensagens.
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean,
    ForeignKey, create_engine
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Estoque(Base):
    """Estoque de produtos por loja."""
    __tablename__ = "estoque"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(20), nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    categoria = Column(String(30), nullable=False)  # camiseta, calca, bone
    cor = Column(String(30), nullable=False)
    tamanho = Column(String(5), nullable=False)      # PP, P, M, G, GG, U
    preco = Column(Float, nullable=False)
    custo = Column(Float, nullable=False)
    estoque_minimo = Column(Integer, default=5)
    loja = Column(String(50), nullable=False)
    quantidade = Column(Integer, default=0)

    def __repr__(self):
        return f"<Estoque {self.sku} | {self.nome} | {self.cor} {self.tamanho} | {self.loja}: {self.quantidade}>"

    @property
    def estoque_critico(self) -> bool:
        return self.quantidade <= self.estoque_minimo


class Funcionario(Base):
    """Funcionários da empresa."""
    __tablename__ = "funcionarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    matricula = Column(String(10), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    cargo = Column(String(60), nullable=False)
    departamento = Column(String(40), nullable=False)
    unidade = Column(String(50), nullable=False)
    data_admissao = Column(String(10), nullable=False)
    salario = Column(Float, nullable=False)
    status = Column(String(10), default="ativo")

    def __repr__(self):
        return f"<Funcionario {self.matricula} | {self.nome} | {self.cargo}>"


class Atendimento(Base):
    """Registro de atendimentos realizados pelo sistema."""
    __tablename__ = "atendimentos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_inicio = Column(DateTime, default=datetime.utcnow)
    data_fim = Column(DateTime, nullable=True)
    perfil_usuario = Column(String(30), nullable=False)  # cliente, vendedor, gerente, rh
    agente_utilizado = Column(String(30), nullable=False)  # cliente, estoque, rh, bi
    resolvido = Column(Boolean, default=False)
    encaminhado_humano = Column(Boolean, default=False)
    score_confianca_medio = Column(Float, nullable=True)
    feedback_usuario = Column(String(10), nullable=True)  # positivo, negativo, nulo
    total_mensagens = Column(Integer, default=0)

    mensagens = relationship("Mensagem", back_populates="atendimento")

    def __repr__(self):
        return f"<Atendimento #{self.id} | {self.perfil_usuario} | {self.agente_utilizado}>"

    @property
    def duracao_segundos(self) -> float | None:
        if self.data_fim and self.data_inicio:
            return (self.data_fim - self.data_inicio).total_seconds()
        return None


class Mensagem(Base):
    """Mensagens individuais de cada atendimento."""
    __tablename__ = "mensagens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    atendimento_id = Column(Integer, ForeignKey("atendimentos.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    papel = Column(String(15), nullable=False)  # usuario, assistente, sistema
    conteudo = Column(Text, nullable=False)
    agente = Column(String(30), nullable=True)
    fontes = Column(Text, nullable=True)          # JSON com fontes usadas
    score_confianca = Column(Float, nullable=True)
    tokens_entrada = Column(Integer, nullable=True)
    tokens_saida = Column(Integer, nullable=True)
    latencia_ms = Column(Integer, nullable=True)

    atendimento = relationship("Atendimento", back_populates="mensagens")

    def __repr__(self):
        return f"<Mensagem #{self.id} | {self.papel} | atend={self.atendimento_id}>"
