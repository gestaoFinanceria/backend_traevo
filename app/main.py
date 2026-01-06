from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.routers import auth, user, transactions, budget, dashboard


# Criar tabelas no banco (apenas para desenvolvimento)
# Em produção, use migrations (Alembic)
Base.metadata.create_all(bind=engine)


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    # Traevo - Finanças Inteligentes 💰
    
    API REST para gerenciamento financeiro pessoal com análise inteligente.
    
    ## Funcionalidades
    
    - **Autenticação JWT**: Registro, login e refresh de tokens
    - **Gestão de Transações**: Registre receitas e despesas
    - **Orçamentos Mensais**: Defina e acompanhe seus limites
    - **Análise Inteligente**: IA que monitora seus gastos e alerta riscos
    - **Dashboard Completo**: Visão consolidada das suas finanças
    
    ## Segurança
    
    - Tokens JWT em cookies HttpOnly
    - Senhas com hash Bcrypt
    - Isolamento total de dados por usuário
    
    ## Como usar
    
    1. Registre-se em `/auth/register`
    2. Faça login em `/auth/login` (tokens são setados automaticamente)
    3. Use os endpoints protegidos com o token no header: `Authorization: Bearer <token>`
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,  # Importante para cookies HttpOnly
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(transactions.router)
app.include_router(budget.router)
app.include_router(dashboard.router)


# Endpoint de health check
@app.get("/", tags=["Health"])
def root():
    """
    Endpoint raiz - verifica se a API está online.
    """
    return {
        "message": "Traevo API está online! 🚀",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check para monitoramento (ex: Render, AWS ELB).
    """
    return {"status": "ok"}


# Event handlers
@app.on_event("startup")
async def startup_event():
    """
    Executado quando a aplicação inicia.
    
    Aqui você pode:
    - Seed de categorias padrão
    - Inicializar conexões
    - Configurar jobs em background
    """
    from app.repositories.categoria_repository import CategoriaRepository
    from app.core.database import SessionLocal
    
    # Seed de categorias padrão
    db = SessionLocal()
    try:
        categoria_repo = CategoriaRepository(db)
        categoria_repo.seed_categorias_padrao()
        print("✅ Categorias padrão inicializadas")
    except Exception as e:
        print(f"⚠️ Erro ao inicializar categorias: {e}")
    finally:
        db.close()
    
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} iniciado!")
    print(f"📚 Documentação disponível em: http://localhost:{settings.PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Executado quando a aplicação é encerrada.
    """
    print(f"👋 {settings.APP_NAME} encerrado")


# Tratamento de erros global
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler customizado para erros de validação do Pydantic.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Dados inválidos",
            "errors": exc.errors()
        }
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    Handler para erros de integridade do banco (ex: violação de unique).
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Erro de integridade: registro duplicado ou constraint violada"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )