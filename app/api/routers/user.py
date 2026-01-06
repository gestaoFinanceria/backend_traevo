from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.repositories.usuario_repository import UsuarioRepository
from app.models.database_models import Usuario
from app.models.schemas import UserResponse, UserUpdateRequest, MessageResponse


router = APIRouter(prefix="/me", tags=["Usuário"])


@router.get(
    "",
    response_model=UserResponse,
    summary="Obter dados do usuário logado",
    description="Retorna os dados do usuário autenticado (exceto senha)"
)
def get_user_profile(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna os dados do perfil do usuário logado.
    
    Requer autenticação via token JWT no header:
    Authorization: Bearer <access_token>
    """
    return UserResponse(
        id_usuario=current_user.ID_USUARIO,
        nome=current_user.NOME,
        email=current_user.EMAIL,
        data_cadastro=current_user.DATA_CADASTRO
    )


@router.patch(
    "",
    response_model=UserResponse,
    summary="Atualizar dados do usuário",
    description="Atualiza nome e/ou email do usuário logado"
)
def update_user_profile(
    update_data: UserUpdateRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza os dados do usuário logado.
    
    Campos que podem ser atualizados:
    - nome: Novo nome (opcional)
    - email: Novo email (opcional, deve ser único)
    
    Validações:
    - Se email for alterado, verifica se já não está em uso
    - Nome deve ter no mínimo 3 caracteres
    """
    usuario_repo = UsuarioRepository(db)
    
    # Atualizar nome se fornecido
    if update_data.nome:
        current_user.NOME = update_data.nome
    
    # Atualizar email se fornecido
    if update_data.email:
        # Verificar se o novo email já está em uso
        if update_data.email.lower() != current_user.EMAIL.lower():
            if usuario_repo.exists_by_email(update_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email já está em uso"
                )
            current_user.EMAIL = update_data.email.lower()
    
    # Salvar alterações
    usuario_atualizado = usuario_repo.update(current_user)
    
    return UserResponse(
        id_usuario=usuario_atualizado.ID_USUARIO,
        nome=usuario_atualizado.NOME,
        email=usuario_atualizado.EMAIL,
        data_cadastro=usuario_atualizado.DATA_CADASTRO
    )