from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.database_models import Usuario


# Esquema de segurança Bearer Token
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependência para obter o usuário autenticado a partir do token JWT.
    
    Uso nos endpoints:
        @app.get("/protected-route")
        def protected_route(current_user: Usuario = Depends(get_current_user)):
            return {"user_id": current_user.ID_USUARIO}
    
    Raises:
        HTTPException 401: Se o token for inválido ou expirado
    """
    auth_service = AuthService(db)
    
    # Extrair token do header Authorization: Bearer <token>
    token = credentials.credentials
    
    # Validar e obter usuário
    return auth_service.get_current_user(token)
ob

def get_current_user_from_cookie(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependência alternativa que extrai o token do cookie HttpOnly.
    
    Útil quando o frontend armazena tokens em cookies em vez de localStorage.
    
    Raises:
        HTTPException 401: Se o cookie não existir ou token for inválido
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso não encontrado"
        )
    
    auth_service = AuthService(db)
    return auth_service.get_current_user(access_token)