from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List, Optional
from app.models.database_models import Orcamento

class OrcamentoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Orcamento:
        orcamento = Orcamento(
            ID_USUARIO=kwargs.get("usuario_id"),
            ID_CATEGORIA=kwargs.get("categoria_id"),
            MES_REFERENCIA=kwargs.get("mes_referencia"),
            ANO_REFERENCIA=kwargs.get("ano_referencia"),
            LIMITE_TOTAL=kwargs.get("limite_total"),
            ID_TIPO_RENDA=kwargs.get("tipo_renda_id")
        )
        self.db.add(orcamento)
        self.db.commit()
        self.db.refresh(orcamento)
        return orcamento

    def find_all_ativos(self, usuario_id: str) -> List[Orcamento]:
        """Método exigido pelo IAAnalysisService para o mês vigente"""
        now = datetime.now()
        return self.find_all_by_mes_ano(usuario_id, now.month, now.year)

    def find_all_by_mes_ano(self, usuario_id: str, mes: int, ano: int) -> List[Orcamento]:
        return self.db.query(Orcamento).filter(
            and_(Orcamento.ID_USUARIO == usuario_id, Orcamento.MES_REFERENCIA == mes, Orcamento.ANO_REFERENCIA == ano)
        ).all()

    def exists_for_categoria_mes_ano(self, usuario_id: str, categoria_id: str, mes: int, ano: int) -> bool:
        return self.db.query(Orcamento).filter(
            and_(Orcamento.ID_USUARIO == usuario_id, Orcamento.ID_CATEGORIA == categoria_id,
                 Orcamento.MES_REFERENCIA == mes, Orcamento.ANO_REFERENCIA == ano)
        ).count() > 0

    def find_by_id(self, orcamento_id: str, usuario_id: str) -> Optional[Orcamento]:
        return self.db.query(Orcamento).filter(and_(Orcamento.ID_ORCAMENTO == orcamento_id, Orcamento.ID_USUARIO == usuario_id)).first()

    def update(self, orcamento: Orcamento) -> Orcamento:
        self.db.commit()
        self.db.refresh(orcamento)
        return orcamento

    def delete(self, orcamento_id: str, usuario_id: str) -> bool:
        obj = self.find_by_id(orcamento_id, usuario_id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False