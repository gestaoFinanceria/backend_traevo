from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional
from decimal import Decimal
from datetime import datetime
from app.models.database_models import PrevisaoIA


class PrevisaoIARepository:
    """
    Repositório para operações CRUD de Previsões da IA.
    
    As previsões são geradas por um job em background e
    consultadas pelos endpoints de Dashboard.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self,
        usuario_id: str,
        valor_projetado: Decimal,
        indice_risco: str,
        mensagem_insight: str,
        mes_alvo: int,
        ano_alvo: int
    ) -> PrevisaoIA:
        """
        Cria uma nova previsão da IA.
        
        Args:
            usuario_id: ID do usuário
            valor_projetado: Valor projetado de gastos
            indice_risco: VERDE, AMARELO ou VERMELHO
            mensagem_insight: Mensagem personalizada da IA
            mes_alvo: Mês da previsão
            ano_alvo: Ano da previsão
        """
        previsao = PrevisaoIA(
            ID_USUARIO=usuario_id,
            VALOR_PROJETADO=valor_projetado,
            INDICE_RISCO=indice_risco,
            MENSAGEM_INSIGHT=mensagem_insight,
            MES_ALVO=mes_alvo,
            ANO_ALVO=ano_alvo
        )
        
        self.db.add(previsao)
        self.db.commit()
        self.db.refresh(previsao)
        
        return previsao
    
    def find_mais_recente_por_usuario(self, usuario_id: str) -> Optional[PrevisaoIA]:
        """
        Busca a previsão mais recente de um usuário.
        
        Usado no Dashboard para exibir o insight atual.
        """
        return self.db.query(PrevisaoIA).filter(
            PrevisaoIA.ID_USUARIO == usuario_id
        ).order_by(
            PrevisaoIA.DATA_GERACAO.desc()
        ).first()
    
    def find_por_mes_ano(
        self,
        usuario_id: str,
        mes: int,
        ano: int
    ) -> Optional[PrevisaoIA]:
        """
        Busca a previsão mais recente para um mês/ano específico.
        """
        return self.db.query(PrevisaoIA).filter(
            and_(
                PrevisaoIA.ID_USUARIO == usuario_id,
                PrevisaoIA.MES_ALVO == mes,
                PrevisaoIA.ANO_ALVO == ano
            )
        ).order_by(
            PrevisaoIA.DATA_GERACAO.desc()
        ).first()
    
    def delete_antigas(self, usuario_id: str, dias_retencao: int = 90):
        """
        Deleta previsões antigas para economizar espaço.
        
        Mantém apenas previsões dos últimos N dias.
        """
        from datetime import timedelta
        
        data_limite = datetime.now() - timedelta(days=dias_retencao)
        
        self.db.query(PrevisaoIA).filter(
            and_(
                PrevisaoIA.ID_USUARIO == usuario_id,
                PrevisaoIA.DATA_GERACAO < data_limite
            )
        ).delete()
        
        self.db.commit()