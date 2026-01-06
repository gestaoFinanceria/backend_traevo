from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import date
from decimal import Decimal
from app.repositories.transacao_repository import TransacaoRepository
from app.repositories.categoria_repository import CategoriaRepository
from app.models.database_models import Transacao


class TransacaoService:
    """
    Serviço de Transações Financeiras.
    
    Responsabilidades:
    - Criar e validar transações
    - Aplicar regras de negócio (valor > 0, categoria válida)
    - Calcular totais e estatísticas
    - Garantir isolamento de dados por usuário
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.transacao_repo = TransacaoRepository(db)
        self.categoria_repo = CategoriaRepository(db)
    
    def create_transacao(
        self,
        usuario_id: str,
        categoria_id: str,
        descricao: str,
        valor: Decimal,
        data_transacao: date,
        tipo: str,
        recorrencia: str = "UNICA"
    ) -> Transacao:
        """
        Cria uma nova transação com validações de negócio.
        
        Validações:
        - Categoria deve existir e estar disponível para o usuário
        - Valor deve ser positivo (já validado pelo Pydantic)
        - Tipo deve ser ENTRADA ou SAIDA
        
        Args:
            usuario_id: ID do usuário autenticado
            categoria_id: ID da categoria
            descricao: Descrição da transação
            valor: Valor positivo
            data_transacao: Data da transação
            tipo: ENTRADA ou SAIDA
            recorrencia: MENSAL, UNICA ou SEMANAL
            
        Returns:
            Transacao criada
            
        Raises:
            HTTPException 400: Se categoria não existir
        """
        # Validar se a categoria existe e está disponível para o usuário
        if not self.categoria_repo.exists_for_usuario(categoria_id, usuario_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Categoria não encontrada ou não disponível"
            )
        
        # Criar transação
        transacao = self.transacao_repo.create(
            usuario_id=usuario_id,
            categoria_id=categoria_id,
            descricao=descricao,
            valor=valor,
            data_transacao=data_transacao,
            tipo=tipo,
            recorrencia=recorrencia
        )
        
        return transacao
    
    def get_transacoes_with_filters(
        self,
        usuario_id: str,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        categoria_id: Optional[str] = None,
        tipo: Optional[str] = None
    ) -> dict:
        """
        Busca transações com filtros e calcula totais.
        
        Returns:
            dict com:
            - transacoes: Lista de transações
            - total_entradas: Soma das entradas
            - total_saidas: Soma das saídas
            - saldo: Diferença entre entradas e saídas
        """
        # Buscar transações
        transacoes = self.transacao_repo.find_all_by_usuario(
            usuario_id=usuario_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            categoria_id=categoria_id,
            tipo=tipo
        )
        
        # Calcular totais
        total_entradas = sum(
            t.VALOR for t in transacoes if t.TIPO == "ENTRADA"
        )
        
        total_saidas = sum(
            t.VALOR for t in transacoes if t.TIPO == "SAIDA"
        )
        
        return {
            "transacoes": transacoes,
            "total_entradas": Decimal(str(total_entradas)),
            "total_saidas": Decimal(str(total_saidas)),
            "saldo": Decimal(str(total_entradas - total_saidas))
        }
    
    def get_estatisticas_mes_atual(self, usuario_id: str) -> dict:
        """
        Calcula estatísticas do mês atual.
        
        Usado no Dashboard para exibir KPIs.
        """
        from datetime import datetime
        now = datetime.now()
        
        return self.transacao_repo.get_totais_por_tipo(
            usuario_id=usuario_id,
            mes=now.month,
            ano=now.year
        )
    
    def delete_transacao(self, transacao_id: str, usuario_id: str):
        """
        Deleta uma transação com validação de propriedade.
        
        Raises:
            HTTPException 404: Se transação não existir ou não pertencer ao usuário
        """
        deleted = self.transacao_repo.delete(transacao_id, usuario_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transação não encontrada"
            )