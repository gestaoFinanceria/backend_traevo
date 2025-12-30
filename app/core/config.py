from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Configurações centralizadas da aplicação Traevo.
    Carrega variáveis de ambiente automaticamente.
    """
    
    # Banco de Dados Oracle
    ORACLE_USER: str
    ORACLE_PASSWORD: str
    ORACLE_DSN: str
    ORACLE_POOL_MIN: int = 2
    ORACLE_POOL_MAX: int = 10
    
    # Segurança JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Aplicação
    APP_NAME: str = "Traevo"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # Porta para deploy
    PORT: int = 8000
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Retorna lista de origens permitidas para CORS"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instância global de configurações
settings = Settings()