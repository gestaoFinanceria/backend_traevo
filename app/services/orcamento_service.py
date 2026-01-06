from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from decimal import Decimal
from datetime import datetime
from app.repositories.orcamento_repository import OrcamentoRepository
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.transacao_repository import TransacaoRepository
from app.models.database_models import Orcamento


class OrcamentoService:
    """
    Serviço de Orçamentos.
    
    Responsabilidades:
    - Criar e gerenciar orçamentos mensais
    - Calcular percentual de uso e saldo disponível
    - Validar unicidade por categoria/mês/ano
    - Fornecer dados para o Dashboard
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.orcamento_repo = OrcamentoRepository(db)
        self.categoria_repo = CategoriaRepository(db)
        self.transacao_repo = TransacaoRepository(db)
    
    def create_orcamento(
        self,
        usuario_id: str,
        categoria_id: str,
        mes_referencia: int,
        ano_referencia: int,
        limite_total: Decimal,
        tipo_renda_id: str = None
    ) -> Orcamento:
        """
        Cria um novo orçamento com validações de negócio.
        
        Validações:
        - Categoria deve existir e estar disponível
        - Não pode haver orçamento duplicado para mesma categoria/mês/ano
        
        Raises:
            HTTPException 400: Se validações falharem
        """
        # Validar categoria
        if not self.categoria_repo.exists_for_usuario(categoria_id, usuario_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Categoria não encontrada ou não disponível"
            )
        
        # Validar unicidade
        if self.orcamento_repo.exists_for_categoria_mes_ano(
            usuario_id=usuario_id,
            categoria_id=categoria_id,
            mes=mes_referencia,
            ano=ano_referencia
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe orçamento para esta categoria neste mês/ano"
            )
        
        # Criar orçamento
        orcamento = self.orcamento_repo.create(
            usuario_id=usuario_id,
            categoria_id=categoria_id,
            mes_referencia=mes_referencia,
            ano_referencia=ano_referencia,
            limite_total=limite_total,
            tipo_renda_id=tipo_renda_id
        )
        
        return orcamento
    
    def get_orcamentos_com_status(
        self,
        usuario_id: str,
        mes: int = None,
        ano: int = None
    ) -> List[dict]:
        """
        Busca orçamentos e calcula status (gasto atual, percentual, saldo).
        
        Se mês/ano não informados, usa mês/ano atual.
        
        Returns:
            Lista de dicts com:
            - orcamento: Objeto Orcamento
            - categoria_nome: Nome da categoria
            - gasto_atual: Valor gasto até o momento
            - percentual_uso: Percentual do limite usado
            - saldo_disponivel: Quanto ainda pode gastar
        """
        # Usar mês/ano atual se não especificado
        if mes is None or ano is None:
            now = datetime.now()
            mes = mes or now.month
            ano = ano or now.year
        
        # Buscar orçamentos
        orcamentos = self.orcamento_repo.find_all_by_mes_ano(
            usuario_id=usuario_id,
            mes=mes,
            ano=ano
        )
        
        # Enriquecer com dados de gasto
        resultado = []
        for orcamento in orcamentos:
            # Calcular gasto atual na categoria
            gasto_atual = self.transacao_repo.get_gasto_por_categoria(
                usuario_id=usuario_id,
                categoria_id=orcamento.ID_CATEGORIA,
                mes=mes,
                ano=ano
            )
            
            # Calcular percentual e saldo
            percentual_uso = (gasto_atual / orcamento.LIMITE_TOTAL * 100) if orcamento.LIMITE_TOTAL > 0 else 0
            saldo_disponivel = orcamento.LIMITE_TOTAL - gasto_atual
            
            # Buscar nome da categoria
            categoria = self.categoria_repo.find_by_id(orcamento.ID_CATEGORIA)
            
            resultado.append({
                "orcamento": orcamento,
                "categoria_nome": categoria.NOME if categoria else "Desconhecida",
                "gasto_atual": gasto_atual,
                "percentual_uso": percentual_uso,
                "saldo_disponivel": saldo_disponivel
            })
        
        return resultado
    
    def get_orcamento_mes_atual(self, usuario_id: str) -> dict:
        """
        Busca orçamentos do mês atual com status.
        
        Usado no Dashboard.
        """
        now = datetime.now()
        return self.get_orcamentos_com_status(
            usuario_id=usuario_id,
            mes=now.month,
            ano=now.year
        )
    
    def update_limite(
        self,
        orcamento_id: str,
        usuario_id: str,
        novo_limite: Decimal
    ) -> Orcamento:
        """
        Atualiza o limite de um orçamento existente.
        
        Raises:
            HTTPException 404: Se orçamento não existir
        """
        orcamento = self.orcamento_repo.find_by_id(orcamento_id, usuario_id)
        
        if not orcamento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orçamento não encontrado"
            )
        
        orcamento.LIMITE_TOTAL = novo_limite
        return self.orcamento_repo.update(orcamento)
    
    def delete_orcamento(self, orcamento_id: str, usuario_id: str):
        """
        Deleta um orçamento.
        
        Raises:
            HTTPException 404: Se orçamento não existir
        """
        deleted = self.orcamento_repo.delete(orcamento_id, usuario_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Orçamento não encontrado"
            )