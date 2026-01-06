from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from app.models.database_models import Usuario
from app.core.security import hash_password


class UsuarioRepository:
    """
    Repositório para operações CRUD de Usuários.
    
    IMPORTANTE: Em Python, ao invés de findAllById(), usamos métodos
    mais expressivos como:
    - get(): busca por PK
    - filter_by(): busca simples por atributos
    - filter(): busca complexa com condições SQL
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, nome: str, email: str, senha: str) -> Usuario:
        """
        Cria um novo usuário no banco de dados.
        
        Args:
            nome: Nome completo do usuário
            email: Email único do usuário
            senha: Senha em texto plano (será hasheada)
            
        Returns:
            Objeto Usuario criado
            
        Raises:
            IntegrityError: Se o email já existir
        """
        usuario = Usuario(
            NOME=nome,
            EMAIL=email.lower(),
            SENHA_HASH=hash_password(senha)
        )
        
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        
        return usuario
    
    def find_by_id(self, usuario_id: str) -> Optional[Usuario]:
        """
        Busca usuário por ID (Primary Key).
        
        Este é o equivalente ao findById() do Java/Spring.
        """
        return self.db.query(Usuario).filter(
            Usuario.ID_USUARIO == usuario_id
        ).first()
    
    def find_by_email(self, email: str) -> Optional[Usuario]:
        """
        Busca usuário por email.
        
        Este é o equivalente ao findByEmail() do Java/Spring.
        """
        return self.db.query(Usuario).filter(
            Usuario.EMAIL == email.lower()
        ).first()
    
    def exists_by_email(self, email: str) -> bool:
        """
        Verifica se um email já está cadastrado.
        
        Mais eficiente que buscar o objeto completo.
        """
        return self.db.query(Usuario).filter(
            Usuario.EMAIL == email.lower()
        ).count() > 0
    
    def update(self, usuario: Usuario) -> Usuario:
        """
        Atualiza um usuário existente.
        
        Args:
            usuario: Objeto Usuario com dados atualizados
            
        Returns:
            Objeto Usuario atualizado
        """
        self.db.commit()
        self.db.refresh(usuario)
        return usuario
    
    def delete(self, usuario_id: str) -> bool:
        """
        Deleta um usuário (soft ou hard delete).
        
        Returns:
            True se deletado com sucesso
        """
        usuario = self.find_by_id(usuario_id)
        if usuario:
            self.db.delete(usuario)
            self.db.commit()
            return True
        return False