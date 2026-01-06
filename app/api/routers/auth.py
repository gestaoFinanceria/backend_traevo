from fastapi import APIRouter, Depends, Response, Cookie, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    MessageResponse,
    UserResponse
)


router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
    description="Cria uma nova conta de usuário no sistema"
)
def register(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registra um novo usuário no sistema.
    
    Validações:
    - Email deve ser único
    - Senha mínima de 6 caracteres
    - Nome mínimo de 3 caracteres
    """
    auth_service = AuthService(db)
    
    # Criar usuário
    usuario = auth_service.register_user(
        nome=user_data.nome,
        email=user_data.email,
        senha=user_data.senha
    )
    
    return UserResponse(
        id_usuario=usuario.ID_USUARIO,
        nome=usuario.NOME,
        email=usuario.EMAIL,
        data_cadastro=usuario.DATA_CADASTRO
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Fazer login",
    description="Autentica um usuário e retorna tokens JWT em cookies HttpOnly"
)
def login(
    login_data: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Autentica um usuário e emite tokens JWT.
    
    Os tokens são armazenados em cookies HttpOnly para segurança:
    - access_token: Válido por 30 minutos
    - refresh_token: Válido por 7 dias
    """
    auth_service = AuthService(db)
    
    # Validar credenciais
    usuario = auth_service.authenticate_user(
        email=login_data.email,
        senha=login_data.senha
    )
    
    # Gerar tokens
    access_token, refresh_token = auth_service.generate_tokens(usuario.ID_USUARIO)
    
    # Setar tokens em cookies HttpOnly
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Apenas HTTPS em produção
        samesite="lax",
        max_age=30 * 60  # 30 minutos
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 dias
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar token de acesso",
    description="Gera um novo access_token usando o refresh_token"
)
def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Renova o access_token usando um refresh_token válido.
    
    O refresh_token é extraído do cookie HttpOnly.
    """
    if not refresh_token:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token não encontrado"
        )
    
    auth_service = AuthService(db)
    
    # Gerar novos tokens
    new_access_token, new_refresh_token = auth_service.refresh_access_token(refresh_token)
    
    # Atualizar cookies
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 60
    )
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Fazer logout",
    description="Remove os tokens de autenticação dos cookies"
)
def logout(response: Response):
    """
    Faz logout do usuário removendo os cookies de autenticação.
    """
    # Limpar cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    return MessageResponse(message="Logout realizado com sucesso")