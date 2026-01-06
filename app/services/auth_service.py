from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Tuple
from app.repositories.usuario_repository import UsuarioRepository
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from app.models.database_models import Usuario


class AuthService:
    """
    Serviço de Autenticação e Autorização.
    
    Responsabilidades:
    - Registro de novos usuários
    - Login e emissão de tokens JWT
    - Refresh de tokens
    - Validação de credenciais
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.usuario_repo = UsuarioRepository(db)
    
    def register_user(self, nome: str, email: str, senha: str) -> Usuario:
        """
        Registra um novo usuário no sistema.
        
        Args:
            nome: Nome completo do usuário
            email: Email único
            senha: Senha em texto plano (será hasheada)
            
        Returns:
            Objeto Usuario criado
            
        Raises:
            HTTPException 400: Se o email já estiver cadastrado
        """
        # Validar se o email já existe
        if self.usuario_repo.exists_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado no sistema"
            )
        
        # Criar usuário (senha será hasheada no repositório)
        usuario = self.usuario_repo.create(
            nome=nome,
            email=email,
            senha=senha
        )
        
        return usuario
    
    def authenticate_user(self, email: str, senha: str) -> Usuario:
        """
        Autentica um usuário verificando email e senha.
        
        Args:
            email: Email do usuário
            senha: Senha em texto plano
            
        Returns:
            Objeto Usuario se credenciais válidas
            
        Raises:
            HTTPException 401: Se credenciais inválidas
        """
        # Buscar usuário por email
        usuario = self.usuario_repo.find_by_email(email)
        
        # Validar usuário e senha
        if not usuario or not verify_password(senha, usuario.SENHA_HASH):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return usuario
    
    def generate_tokens(self, usuario_id: str) -> Tuple[str, str]:
        """
        Gera Access Token e Refresh Token para um usuário.
        
        Args:
            usuario_id: ID do usuário
            
        Returns:
            Tupla (access_token, refresh_token)
        """
        access_token = create_access_token(data={"sub": usuario_id})
        refresh_token = create_refresh_token(data={"sub": usuario_id})
        
        return access_token, refresh_token
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """
        Gera um novo Access Token usando um Refresh Token válido.
        
        Args:
            refresh_token: Refresh Token válido
            
        Returns:
            Tupla (novo_access_token, novo_refresh_token)
            
        Raises:
            HTTPException 401: Se o Refresh Token for inválido
        """
        try:
            # Decodificar e validar o Refresh Token
            payload = decode_token(refresh_token)
            
            # Verificar se é realmente um Refresh Token
            if not verify_token_type(payload, "refresh"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido"
                )
            
            # Extrair usuário do token
            usuario_id: str = payload.get("sub")
            if not usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido"
                )
            
            # Validar se o usuário ainda existe
            usuario = self.usuario_repo.find_by_id(usuario_id)
            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuário não encontrado"
                )
            
            # Gerar novos tokens
            return self.generate_tokens(usuario_id)
            
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado"
            )
    
    def get_current_user(self, token: str) -> Usuario:
        """
        Obtém o usuário atual baseado no Access Token.
        
        Usado como dependência nos endpoints protegidos.
        
        Args:
            token: Access Token JWT
            
        Returns:
            Objeto Usuario
            
        Raises:
            HTTPException 401: Se o token for inválido
        """
        try:
            # Decodificar token
            payload = decode_token(token)
            
            # Verificar se é um Access Token
            if not verify_token_type(payload, "access"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido"
                )
            
            # Extrair usuário
            usuario_id: str = payload.get("sub")
            if not usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido"
                )
            
            # Buscar usuário no banco
            usuario = self.usuario_repo.find_by_id(usuario_id)
            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuário não encontrado"
                )
            
            return usuario
            
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
                headers={"WWW-Authenticate": "Bearer"}
            )