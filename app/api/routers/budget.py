from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.orcamento_service import OrcamentoService
from app.models.database_models import Usuario
from app.models.schemas import (
    OrcamentoCreateRequest,
    OrcamentoResponse,
    MessageResponse
)


router = APIRouter(prefix="/budget", tags=["Orçamentos"])


@router.post(
    "",
    response_model=OrcamentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar orçamento",
    description="Define um novo orçamento para uma categoria em um mês/ano"
)
def create_budget(
    orcamento_data: OrcamentoCreateRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cria um novo orçamento mensal para uma categoria.
    
    Campos obrigatórios:
    - id_categoria: ID da categoria a orçar
    - mes_referencia: Mês (1-12)
    - ano_referencia: Ano (>= 2025)
    - limite_total: Valor limite do orçamento
    
    Validações:
    - Categoria deve existir e estar disponível
    - Não pode haver orçamento duplicado para mesma categoria/mês/ano
    """
    orcamento_service = OrcamentoService(db)
    
    # Criar orçamento
    orcamento = orcamento_service.create_orcamento(
        usuario_id=current_user.ID_USUARIO,
        categoria_id=orcamento_data.id_categoria,
        mes_referencia=orcamento_data.mes_referencia,
        ano_referencia=orcamento_data.ano_referencia,
        limite_total=orcamento_data.limite_total,
        tipo_renda_id=orcamento_data.id_tipo_renda
    )
    
    # Obter status do orçamento (gasto atual, percentual, etc.)
    orcamentos_com_status = orcamento_service.get_orcamentos_com_status(
        usuario_id=current_user.ID_USUARIO,
        mes=orcamento_data.mes_referencia,
        ano=orcamento_data.ano_referencia
    )
    
    # Encontrar o orçamento recém-criado
    orcamento_status = next(
        (o for o in orcamentos_com_status if o["orcamento"].ID_ORCAMENTO == orcamento.ID_ORCAMENTO),
        None
    )
    
    if orcamento_status:
        return OrcamentoResponse(
            id_orcamento=orcamento.ID_ORCAMENTO,
            id_categoria=orcamento.ID_CATEGORIA,
            categoria_nome=orcamento_status["categoria_nome"],
            mes_referencia=orcamento.MES_REFERENCIA,
            ano_referencia=orcamento.ANO_REFERENCIA,
            limite_total=orcamento.LIMITE_TOTAL,
            gasto_atual=orcamento_status["gasto_atual"],
            percentual_uso=orcamento_status["percentual_uso"],
            saldo_disponivel=orcamento_status["saldo_disponivel"]
        )
    
    # Fallback caso não encontre no status
    return OrcamentoResponse(
        id_orcamento=orcamento.ID_ORCAMENTO,
        id_categoria=orcamento.ID_CATEGORIA,
        categoria_nome="",
        mes_referencia=orcamento.MES_REFERENCIA,
        ano_referencia=orcamento.ANO_REFERENCIA,
        limite_total=orcamento.LIMITE_TOTAL,
        gasto_atual=0,
        percentual_uso=0,
        saldo_disponivel=orcamento.LIMITE_TOTAL
    )


@router.get(
    "",
    response_model=List[OrcamentoResponse],
    summary="Listar orçamentos",
    description="Lista orçamentos de um mês/ano específico ou do mês atual"
)
def list_budgets(
    mes: Optional[int] = Query(None, ge=1, le=12, description="Mês (1-12)"),
    ano: Optional[int] = Query(None, ge=2025, description="Ano"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos os orçamentos do usuário para um mês/ano.
    
    Se mês/ano não forem especificados, retorna orçamentos do mês atual.
    
    Retorna para cada orçamento:
    - Dados básicos (categoria, limite)
    - Gasto atual na categoria
    - Percentual do limite usado
    - Saldo disponível
    """
    orcamento_service = OrcamentoService(db)
    
    # Usar mês/ano atual se não especificado
    if mes is None or ano is None:
        now = datetime.now()
        mes = mes or now.month
        ano = ano or now.year
    
    # Buscar orçamentos com status
    orcamentos_com_status = orcamento_service.get_orcamentos_com_status(
        usuario_id=current_user.ID_USUARIO,
        mes=mes,
        ano=ano
    )
    
    # Converter para response model
    return [
        OrcamentoResponse(
            id_orcamento=o["orcamento"].ID_ORCAMENTO,
            id_categoria=o["orcamento"].ID_CATEGORIA,
            categoria_nome=o["categoria_nome"],
            mes_referencia=o["orcamento"].MES_REFERENCIA,
            ano_referencia=o["orcamento"].ANO_REFERENCIA,
            limite_total=o["orcamento"].LIMITE_TOTAL,
            gasto_atual=o["gasto_atual"],
            percentual_uso=o["percentual_uso"],
            saldo_disponivel=o["saldo_disponivel"]
        )
        for o in orcamentos_com_status
    ]


@router.delete(
    "/{orcamento_id}",
    response_model=MessageResponse,
    summary="Deletar orçamento",
    description="Remove um orçamento específico"
)
def delete_budget(
    orcamento_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deleta um orçamento do usuário.
    
    Validações:
    - Orçamento deve existir
    - Orçamento deve pertencer ao usuário logado
    """
    orcamento_service = OrcamentoService(db)
    
    orcamento_service.delete_orcamento(
        orcamento_id=orcamento_id,
        usuario_id=current_user.ID_USUARIO
    )
    
    return MessageResponse(message="Orçamento deletado com sucesso")