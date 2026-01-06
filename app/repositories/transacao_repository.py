from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from app.models.database_models import Transacao

class TransacaoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Transacao:
        transacao = Transacao(
            ID_USUARIO=kwargs.get("usuario_id"),
            ID_CATEGORIA=kwargs.get("categoria_id"),
            DESCRICAO=kwargs.get("descricao"),
            VALOR=kwargs.get("valor"),
            DATA_TRANSACAO=kwargs.get("data_transacao"),
            TIPO=kwargs.get("tipo"),
            RECORRENCIA=kwargs.get("recorrencia", "UNICA")
        )
        self.db.add(transacao)
        self.db.commit()
        self.db.refresh(transacao)
        return transacao

    def find_all_by_usuario(self, usuario_id: str, data_inicio: Optional[date] = None, 
                            data_fim: Optional[date] = None, categoria_id: Optional[str] = None, 
                            tipo: Optional[str] = None) -> List[Transacao]:
        query = self.db.query(Transacao).filter(Transacao.ID_USUARIO == usuario_id)
        if data_inicio: query = query.filter(Transacao.DATA_TRANSACAO >= data_inicio)
        if data_fim: query = query.filter(Transacao.DATA_TRANSACAO <= data_fim)
        if categoria_id: query = query.filter(Transacao.ID_CATEGORIA == categoria_id)
        if tipo: query = query.filter(Transacao.TIPO == tipo)
        return query.order_by(Transacao.DATA_TRANSACAO.desc()).all()

    def get_totais_por_tipo(self, usuario_id: str, mes: int, ano: int) -> dict:
        filtro = and_(
            Transacao.ID_USUARIO == usuario_id,
            func.extract('month', Transacao.DATA_TRANSACAO) == mes,
            func.extract('year', Transacao.DATA_TRANSACAO) == ano
        )
        entradas = self.db.query(func.sum(Transacao.VALOR)).filter(filtro, Transacao.TIPO == "ENTRADA").scalar() or 0
        saidas = self.db.query(func.sum(Transacao.VALOR)).filter(filtro, Transacao.TIPO == "SAIDA").scalar() or 0
        return {"total_entradas": Decimal(str(entradas)), "total_saidas": Decimal(str(saidas)), "saldo": Decimal(str(entradas - saidas))}

    def get_gasto_por_categoria(self, usuario_id: str, categoria_id: str, mes: int, ano: int) -> Decimal:
        resultado = self.db.query(func.sum(Transacao.VALOR)).filter(
            and_(Transacao.ID_USUARIO == usuario_id, Transacao.ID_CATEGORIA == categoria_id,
                 Transacao.TIPO == "SAIDA", func.extract('month', Transacao.DATA_TRANSACAO) == mes,
                 func.extract('year', Transacao.DATA_TRANSACAO) == ano)
        ).scalar()
        return Decimal(str(resultado or 0))

    def get_historico_para_ia(self, usuario_id: str, meses_anteriores: int = 6) -> List[Transacao]:
        """Método exigido pelo IAAnalysisService"""
        data_limite = datetime.now() - timedelta(days=meses_anteriores * 30)
        return self.db.query(Transacao).filter(
            and_(Transacao.ID_USUARIO == usuario_id, Transacao.DATA_TRANSACAO >= data_limite)
        ).order_by(Transacao.DATA_TRANSACAO.asc()).all()

    def delete(self, transacao_id: str, usuario_id: str) -> bool:
        obj = self.db.query(Transacao).filter(and_(Transacao.ID_TRANSACAO == transacao_id, Transacao.ID_USUARIO == usuario_id)).first()
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False