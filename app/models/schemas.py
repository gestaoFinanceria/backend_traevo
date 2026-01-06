from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal


# ============================================================================
# SCHEMAS DE AUTENTICAÇÃO
# ============================================================================

class UserRegisterRequest(BaseModel):
    """Schema para registro de novo usuário"""
    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    senha: str = Field(..., min_length=6, max_length=50)
    
    @validator('nome')
    def nome_nao_vazio(cls, v):
        if not v.strip():
            raise ValueError('Nome não pode ser vazio')
        return v.strip()


class UserLoginRequest(BaseModel):
    """Schema para login"""
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    """Schema de resposta com tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Schema genérico para mensagens de sucesso"""
    message: str


# ============================================================================
# SCHEMAS DE USUÁRIO
# ============================================================================

class UserResponse(BaseModel):
    """Schema de resposta com dados do usuário (sem senha)"""
    id_usuario: str
    nome: str
    email: str
    data_cadastro: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id_usuario": "123e4567-e89b-12d3-a456-426614174000",
                "nome": "João Silva",
                "email": "joao@example.com",
                "data_cadastro": "2025-01-15T10:30:00Z"
            }
        }


class UserUpdateRequest(BaseModel):
    """Schema para atualização de dados do usuário"""
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    
    @validator('nome')
    def nome_nao_vazio(cls, v):
        if v and not v.strip():
            raise ValueError('Nome não pode ser vazio')
        return v.strip() if v else None


# ============================================================================
# SCHEMAS DE CATEGORIA
# ============================================================================

class CategoriaResponse(BaseModel):
    """Schema de resposta de categoria"""
    id_categoria: str
    nome: str
    is_padrao: bool  # True se ID_USUARIO for NULL (categoria padrão do sistema)
    
    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS DE TRANSAÇÃO
# ============================================================================

class TransacaoCreateRequest(BaseModel):
    """Schema para criar nova transação"""
    id_categoria: str
    descricao: str = Field(..., min_length=1, max_length=255)
    valor: Decimal = Field(..., gt=0, decimal_places=2)
    data_transacao: date
    tipo: str = Field(..., pattern="^(ENTRADA|SAIDA)$")
    recorrencia: str = Field(default="UNICA", pattern="^(MENSAL|UNICA|SEMANAL)$")
    
    @validator('descricao')
    def descricao_nao_vazia(cls, v):
        if not v.strip():
            raise ValueError('Descrição não pode ser vazia')
        return v.strip()


class TransacaoResponse(BaseModel):
    """Schema de resposta de transação"""
    id_transacao: str
    id_categoria: str
    categoria_nome: str
    descricao: str
    valor: Decimal
    data_transacao: date
    tipo: str
    recorrencia: str
    
    class Config:
        from_attributes = True


class TransacaoListResponse(BaseModel):
    """Schema de resposta para lista de transações"""
    transacoes: List[TransacaoResponse]
    total_entradas: Decimal
    total_saidas: Decimal
    saldo: Decimal


# ============================================================================
# SCHEMAS DE ORÇAMENTO
# ============================================================================

class OrcamentoCreateRequest(BaseModel):
    """Schema para criar orçamento"""
    id_categoria: str
    mes_referencia: int = Field(..., ge=1, le=12)
    ano_referencia: int = Field(..., ge=2025)
    limite_total: Decimal = Field(..., gt=0, decimal_places=2)
    id_tipo_renda: Optional[str] = None


class OrcamentoResponse(BaseModel):
    """Schema de resposta de orçamento"""
    id_orcamento: str
    id_categoria: str
    categoria_nome: str
    mes_referencia: int
    ano_referencia: int
    limite_total: Decimal
    gasto_atual: Decimal
    percentual_uso: Decimal
    saldo_disponivel: Decimal
    
    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS DE PREVISÃO IA
# ============================================================================

class PrevisaoIAResponse(BaseModel):
    """Schema de resposta de previsão da IA"""
    id_previsao: str
    data_geracao: datetime
    valor_projetado: Decimal
    indice_risco: str  # VERDE, AMARELO, VERMELHO
    mensagem_insight: str
    mes_alvo: int
    ano_alvo: int
    
    class Config:
        from_attributes = True


# ============================================================================
# SCHEMAS DE DASHBOARD
# ============================================================================

class DashboardOverviewResponse(BaseModel):
    """Schema completo do Dashboard (Home)"""
    # KPIs do mês atual
    total_entradas_mes: Decimal
    total_saidas_mes: Decimal
    saldo_mes: Decimal
    
    # Orçamentos ativos
    orcamentos: List[OrcamentoResponse]
    
    # Previsão da IA mais recente
    previsao_ia: Optional[PrevisaoIAResponse] = None
    
    # Estatísticas adicionais
    percentual_gasto_total: Decimal
    dias_restantes_mes: int
    media_gasto_diario: Decimal


# ============================================================================
# SCHEMAS DE TIPO DE RENDA
# ============================================================================

class TipoRendaCreateRequest(BaseModel):
    """Schema para criar tipo de renda"""
    nome: str = Field(..., min_length=1, max_length=50)
    recorrencia: str = Field(..., pattern="^(MENSAL|UNICA|SEMANAL)$")
    valor_estimado: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    dia_salario: Optional[int] = Field(None, ge=1, le=31)


class TipoRendaResponse(BaseModel):
    """Schema de resposta de tipo de renda"""
    id_tipo_renda: str
    nome: str
    recorrencia: str
    valor_estimado: Optional[Decimal]
    dia_salario: Optional[int]
    
    class Config:
        from_attributes = True