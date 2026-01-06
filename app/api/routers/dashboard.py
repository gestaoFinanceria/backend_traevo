from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.transacao_service import TransacaoService
from app.services.orcamento_service import OrcamentoService
from app.services.ia_analysis_service import IAAnalysisService
from app.models.database_models import Usuario
from app.models.schemas import (
    DashboardOverviewResponse,
    OrcamentoResponse,
    PrevisaoIAResponse
)


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
    summary="Overview do Dashboard",
    description="Retorna todos os dados necessários para a tela inicial (Home)"
)
def get_dashboard_overview(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint principal do Dashboard "anti-ansiedade".
    
    Retorna em uma única chamada:
    1. KPIs do mês atual:
       - Total de entradas
       - Total de saídas
       - Saldo do mês
    
    2. Orçamentos ativos:
       - Lista de orçamentos do mês
       - Gasto atual por categoria
       - Percentual usado
       - Saldo disponível
    
    3. Previsão da IA:
       - Valor projetado para o mês
       - Índice de risco (VERDE/AMARELO/VERMELHO)
       - Mensagem de insight personalizada
    
    4. Estatísticas adicionais:
       - Percentual de gasto total
       - Dias restantes no mês
       - Média de gasto diário
    
    Este endpoint é otimizado para carregar rapidamente e fornecer
    todas as informações críticas de uma só vez.
    """
    transacao_service = TransacaoService(db)
    orcamento_service = OrcamentoService(db)
    ia_service = IAAnalysisService(db)
    
    now = datetime.now()
    
    # 1. Calcular KPIs do mês atual
    estatisticas_mes = transacao_service.get_estatisticas_mes_atual(
        usuario_id=current_user.ID_USUARIO
    )
    
    # 2. Buscar orçamentos ativos com status
    orcamentos_com_status = orcamento_service.get_orcamento_mes_atual(
        usuario_id=current_user.ID_USUARIO
    )
    
    # Converter orçamentos para response model
    orcamentos_response = [
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
    
    # 3. Buscar ou gerar previsão da IA
    previsao_ia = ia_service.get_ultima_previsao(
        usuario_id=current_user.ID_USUARIO
    )
    
    previsao_response = PrevisaoIAResponse(
        id_previsao=previsao_ia.ID_PREVISAO,
        data_geracao=previsao_ia.DATA_GERACAO,
        valor_projetado=previsao_ia.VALOR_PROJETADO,
        indice_risco=previsao_ia.INDICE_RISCO,
        mensagem_insight=previsao_ia.MENSAGEM_INSIGHT,
        mes_alvo=previsao_ia.MES_ALVO,
        ano_alvo=previsao_ia.ANO_ALVO
    ) if previsao_ia else None
    
    # 4. Calcular estatísticas adicionais
    
    # Calcular percentual de gasto total (soma de todos os orçamentos)
    limite_total_orcamentos = sum(o.limite_total for o in orcamentos_response)
    total_saidas = estatisticas_mes["total_saidas"]
    
    percentual_gasto_total = (
        (total_saidas / limite_total_orcamentos * 100) 
        if limite_total_orcamentos > 0 
        else Decimal("0")
    )
    
    # Calcular dias restantes no mês
    ultimo_dia_mes = (
        datetime(now.year, now.month + 1, 1) - timedelta(days=1)
    ).day if now.month < 12 else 31
    dias_restantes = ultimo_dia_mes - now.day
    
    # Calcular média de gasto diário
    media_gasto_diario = (
        total_saidas / Decimal(str(now.day))
        if now.day > 0
        else Decimal("0")
    )
    
    # Retornar dashboard completo
    return DashboardOverviewResponse(
        total_entradas_mes=estatisticas_mes["total_entradas"],
        total_saidas_mes=estatisticas_mes["total_saidas"],
        saldo_mes=estatisticas_mes["saldo"],
        orcamentos=orcamentos_response,
        previsao_ia=previsao_response,
        percentual_gasto_total=percentual_gasto_total.quantize(Decimal("0.01")),
        dias_restantes_mes=dias_restantes,
        media_gasto_diario=media_gasto_diario.quantize(Decimal("0.01"))
    )


@router.post(
    "/refresh-prediction",
    response_model=PrevisaoIAResponse,
    summary="Atualizar previsão da IA",
    description="Força a geração de uma nova previsão da IA"
)
def refresh_prediction(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Força a geração de uma nova previsão da IA.
    
    Útil quando o usuário:
    - Adiciona muitas transações novas
    - Quer ver previsão atualizada
    - Mudou significativamente seu comportamento financeiro
    """
    ia_service = IAAnalysisService(db)
    
    # Gerar nova previsão
    nova_previsao = ia_service.gerar_previsao(
        usuario_id=current_user.ID_USUARIO
    )
    
    return PrevisaoIAResponse(
        id_previsao=nova_previsao.ID_PREVISAO,
        data_geracao=nova_previsao.DATA_GERACAO,
        valor_projetado=nova_previsao.VALOR_PROJETADO,
        indice_risco=nova_previsao.INDICE_RISCO,
        mensagem_insight=nova_previsao.MENSAGEM_INSIGHT,
        mes_alvo=nova_previsao.MES_ALVO,
        ano_alvo=nova_previsao.ANO_ALVO
    )


# Import necessário para timedelta
from datetime import timedelta