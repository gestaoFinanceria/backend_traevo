from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from app.models.database_models import Categoria

class CategoriaRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, categoria_id: str) -> Optional[Categoria]:
        """Busca uma categoria por ID."""
        return self.db.query(Categoria).filter(Categoria.ID_CATEGORIA == categoria_id).first()

    def exists_for_usuario(self, categoria_id: str, usuario_id: str) -> bool:
        """Verifica se a categoria existe e pertence ao usuário ou é padrão (global)."""
        return self.db.query(Categoria).filter(
            and_(
                Categoria.ID_CATEGORIA == categoria_id,
                or_(
                    Categoria.ID_USUARIO == usuario_id,
                    Categoria.ID_USUARIO.is_(None)
                )
            )
        ).count() > 0

    def find_all_by_usuario(self, usuario_id: str) -> List[Categoria]:
        """Retorna todas as categorias disponíveis para o usuário."""
        return self.db.query(Categoria).filter(
            or_(Categoria.ID_USUARIO == usuario_id, Categoria.ID_USUARIO.is_(None))
        ).all()