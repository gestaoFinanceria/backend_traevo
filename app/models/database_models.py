from sqlalchemy import (
    Column, String, Numeric, DateTime, Date, Integer,
    ForeignKey, CheckConstraint, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


def generate_uuid():
    """Gera UUID para chaves primárias"""
    return str(uuid.uuid4())


class Usuario(Base):
    """Modelo de Usuário do Sistema"""
    __tablename__ = "TRAEVO_USUARIOS"
    
    ID_USUARIO = Column(String(36), primary_key=True, default=generate_uuid)
    TOKEN = Column(String(36), nullable=False, default=generate_uuid)
    NOME = Column(String(100), nullable=False)
    EMAIL = Column(String(100), nullable=False, unique=True)
    SENHA_HASH = Column(String(255), nullable=False)
    DATA_CADASTRO = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relacionamentos
    tipo_rendas = relationship("TipoRenda", back_populates="usuario", cascade="all, delete-orphan")
    categorias = relationship("Categoria", back_populates="usuario", cascade="all, delete-orphan")
    transacoes = relationship("Transacao", back_populates="usuario", cascade="all, delete-orphan")
    orcamentos = relationship("Orcamento", back_populates="usuario", cascade="all, delete-orphan")
    previsoes = relationship("PrevisaoIA", back_populates="usuario", cascade="all, delete-orphan")


class TipoRenda(Base):
    """Tipos de Renda do Usuário (Salário, Freelance, etc.)"""
    __tablename__ = "TRAEVO_TIPO_RENDAS"
    
    ID_TIPO_RENDA = Column(String(36), primary_key=True, default=generate_uuid)
    ID_USUARIO = Column(String(36), ForeignKey("TRAEVO_USUARIOS.ID_USUARIO", ondelete="CASCADE"), nullable=False)
    NOME = Column(String(50), nullable=False)
    RECORRENCIA = Column(String(20), nullable=False)
    VALOR_ESTIMADO = Column(Numeric(10, 2))
    DIA_SALARIO = Column(Integer)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("RECORRENCIA IN ('MENSAL', 'UNICA', 'SEMANAL')", name="CHK_RECORRENCIA"),
        CheckConstraint("DIA_SALARIO IS NULL OR (DIA_SALARIO >= 1 AND DIA_SALARIO <= 31)", name="CHK_DIA_SALARIO"),
        UniqueConstraint("ID_USUARIO", "NOME", name="UK_RENDA_NOME_USUARIO"),
    )
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="tipo_rendas")
    orcamentos = relationship("Orcamento", back_populates="tipo_renda")


class Categoria(Base):
    """Categorias de Transações (Alimentação, Transporte, etc.)"""
    __tablename__ = "TRAEVO_CATEGORIAS"
    
    ID_CATEGORIA = Column(String(36), primary_key=True, default=generate_uuid)
    NOME = Column(String(50), nullable=False)
    ID_USUARIO = Column(String(36), ForeignKey("TRAEVO_USUARIOS.ID_USUARIO", ondelete="CASCADE"))
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("NOME", "ID_USUARIO", name="UK_CATEGORIA_NOME_USUARIO"),
    )
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="categorias")
    transacoes = relationship("Transacao", back_populates="categoria")
    orcamentos = relationship("Orcamento", back_populates="categoria")


class Transacao(Base):
    """Transações Financeiras (Receitas e Despesas)"""
    __tablename__ = "TRAEVO_TRANSACOES"
    
    ID_TRANSACAO = Column(String(36), primary_key=True, default=generate_uuid)
    ID_USUARIO = Column(String(36), ForeignKey("TRAEVO_USUARIOS.ID_USUARIO", ondelete="CASCADE"), nullable=False)
    ID_CATEGORIA = Column(String(36), ForeignKey("TRAEVO_CATEGORIAS.ID_CATEGORIA"), nullable=False)
    DESCRICAO = Column(String(255), nullable=False)
    VALOR = Column(Numeric(10, 2), nullable=False)
    DATA_TRANSACAO = Column(Date, nullable=False)
    RECORRENCIA = Column(String(20), nullable=False, default="UNICA")
    TIPO = Column(String(10), nullable=False)  # ENTRADA ou SAIDA
    
    # Constraints
    __table_args__ = (
        CheckConstraint("VALOR > 0", name="CHK_TRANSACAO_VALOR"),
        CheckConstraint("TIPO IN ('ENTRADA', 'SAIDA')", name="CHK_TRANSACAO_TIPO"),
    )
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="transacoes")
    categoria = relationship("Categoria", back_populates="transacoes")


class Orcamento(Base):
    """Orçamentos Mensais por Categoria"""
    __tablename__ = "TRAEVO_ORCAMENTOS"
    
    ID_ORCAMENTO = Column(String(36), primary_key=True, default=generate_uuid)
    ID_USUARIO = Column(String(36), ForeignKey("TRAEVO_USUARIOS.ID_USUARIO", ondelete="CASCADE"), nullable=False)
    ID_CATEGORIA = Column(String(36), ForeignKey("TRAEVO_CATEGORIAS.ID_CATEGORIA"), nullable=False)
    ID_TIPO_RENDA = Column(String(36), ForeignKey("TRAEVO_TIPO_RENDAS.ID_TIPO_RENDA"))
    MES_REFERENCIA = Column(Integer, nullable=False)
    ANO_REFERENCIA = Column(Integer, nullable=False)
    LIMITE_TOTAL = Column(Numeric(10, 2), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("MES_REFERENCIA >= 1 AND MES_REFERENCIA <= 12", name="CHK_MES_ORCAMENTO"),
        CheckConstraint("ANO_REFERENCIA >= 2025", name="CHK_ANO_ORCAMENTO"),
        CheckConstraint("LIMITE_TOTAL > 0", name="CHK_LIMITE_ORCAMENTO"),
        UniqueConstraint("ID_USUARIO", "MES_REFERENCIA", "ANO_REFERENCIA", "ID_CATEGORIA", name="UK_ORCAMENTO_MES_ANO_CATEGORIA"),
    )
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="orcamentos")
    categoria = relationship("Categoria", back_populates="orcamentos")
    tipo_renda = relationship("TipoRenda", back_populates="orcamentos")


class PrevisaoIA(Base):
    """Previsões e Insights Gerados pela IA"""
    __tablename__ = "TRAEVO_PREVISOES_IA"
    
    ID_PREVISAO = Column(String(36), primary_key=True, default=generate_uuid)
    ID_USUARIO = Column(String(36), ForeignKey("TRAEVO_USUARIOS.ID_USUARIO", ondelete="CASCADE"), nullable=False)
    DATA_GERACAO = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    VALOR_PROJETADO = Column(Numeric(10, 2), nullable=False)
    INDICE_RISCO = Column(String(10), nullable=False)
    MENSAGEM_INSIGHT = Column(String(500), nullable=False)
    MES_ALVO = Column(Integer, nullable=False)
    ANO_ALVO = Column(Integer, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("INDICE_RISCO IN ('VERDE', 'AMARELO', 'VERMELHO')", name="CHK_INDICE_RISCO"),
    )
    
    # Relacionamentos
    usuario = relationship("Usuario", back_populates="previsoes")