from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.transacao_service import TransacaoService
from app.repositories.categoria_repository import CategoriaRepository
from app.models.database_models import Usuario
from app.models.schemas import (
    TransacaoCreateRequest,
    TransacaoResponse,
    TransacaoListResponse,
    MessageResponse
)


router = APIRouter(prefix="/transactions", tags=["Transações"])


@router.post(
    "",
    response_model=TransacaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova transação",
    description="Registra uma nova transação (receita ou despesa)"
)
def create_transaction(
    transacao_data: TransacaoCreateRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cria uma nova transação financeira.
    
    Campos obrigatórios:
    - id_categoria: ID da categoria (deve existir e estar disponível)
    - descricao: Descrição da transação
    - valor: Valor positivo
    - data_transacao: Data da transação
    - tipo: ENTRADA ou SAIDA
    
    Campo opcional:
    - recorrencia: MENSAL, UNICA ou SEMANAL (padrão: UNICA)
    """
    transacao_service = TransacaoService(db)
    
    # Criar transação
    transacao = transacao_service.create_transacao(
        usuario_id=current_user.ID_USUARIO,
        categoria_id=transacao_data.id_categoria,
        descricao=transacao_data.descricao,
        valor=transacao_data.valor,
        data_transacao=transacao_data.data_transacao,
        tipo=transacao_data.tipo,
        recorrencia=transacao_data.recorrencia
    )
    
    # Buscar nome da categoria
    categoria_repo = CategoriaRepository(db)
    categoria = categoria_repo.find_by_id(transacao.ID_CATEGORIA)
    
    return TransacaoResponse(
        id_transacao=transacao.ID_TRANSACAO,
        id_categoria=transacao.ID_CATEGORIA,
        categoria_nome=categoria.NOME if categoria else "Desconhecida",
        descricao=transacao.DESCRICAO,
        valor=transacao.VALOR,
        data_transacao=transacao.DATA_TRANSACAO,
        tipo=transacao.TIPO,
        recorrencia=transacao.RECORRENCIA
    )


@router.get(
    "",
    response_model=TransacaoListResponse,
    summary="Listar transações",
    description="Lista transações com filtros opcionais (data, categoria, tipo)"
)
def list_transactions(
    data_inicio: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    categoria_id: Optional[str] = Query(None, description="Filtrar por categoria"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: ENTRADA ou SAIDA"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todas as transações do usuário com filtros opcionais.
    
    Filtros disponíveis:
    - data_inicio: Filtra transações a partir desta data
    - data_fim: Filtra transações até esta data
    - categoria_id: Filtra por categoria específica
    - tipo: Filtra por ENTRADA ou SAIDA
    
    Retorna:
    - Lista de transações ordenadas por data (mais recente primeiro)
    - Total de entradas
    - Total de saídas
    - Saldo (entradas - saídas)
    """
    transacao_service = TransacaoService(db)
    categoria_repo = CategoriaRepository(db)
    
    # Buscar transações com filtros
    resultado = transacao_service.get_transacoes_with_filters(
        usuario_id=current_user.ID_USUARIO,
        data_inicio=data_inicio,
        data_fim=data_fim,
        categoria_id=categoria_id,
        tipo=tipo
    )
    
    # Enriquecer com nome das categorias
    transacoes_response = []
    for t in resultado["transacoes"]:
        categoria = categoria_repo.find_by_id(t.ID_CATEGORIA)
        transacoes_response.append(
            TransacaoResponse(
                id_transacao=t.ID_TRANSACAO,
                id_categoria=t.ID_CATEGORIA,
                categoria_nome=categoria.NOME if categoria else "Desconhecida",
                descricao=t.DESCRICAO,
                valor=t.VALOR,
                data_transacao=t.DATA_TRANSACAO,
                tipo=t.TIPO,
                recorrencia=t.RECORRENCIA
            )
        )
    
    return TransacaoListResponse(
        transacoes=transacoes_response,
        total_entradas=resultado["total_entradas"],
        total_saidas=resultado["total_saidas"],
        saldo=resultado["saldo"]
    )


@router.delete(
    "/{transacao_id}",
    response_model=MessageResponse,
    summary="Deletar transação",
    description="Remove uma transação específica"
)
def delete_transaction(
    transacao_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deleta uma transação do usuário.
    
    Validações:
    - Transação deve existir
    - Transação deve pertencer ao usuário logado
    """
    transacao_service = TransacaoService(db)
    
    transacao_service.delete_transacao(
        transacao_id=transacao_id,
        usuario_id=current_user.ID_USUARIO
    )
    
    return MessageResponse(message="Transação deletada com sucesso")