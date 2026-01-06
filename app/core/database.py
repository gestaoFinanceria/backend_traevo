import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Carrega as variáveis do arquivo .env
load_dotenv()

# Pega a URL de conexão do ambiente
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Cria o motor (Engine) para o Oracle
# pool_pre_ping ajuda a não derrubar a conexão em bancos na nuvem
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Fábrica de sessões para os Repositories usarem
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# O famoso 'Base' que estava dando erro de importação nos seus modelos
Base = declarative_base()

# Função auxiliar para abrir/fechar o banco em cada requisição da API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()