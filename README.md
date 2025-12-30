# backend_traevo
traevo-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # Aplicação FastAPI principal
│   │
│   ├── core/                        # Configurações centrais
│   │   ├── __init__.py
│   │   ├── config.py                # Variáveis de ambiente
│   │   ├── security.py              # JWT, Bcrypt, Autenticação
│   │   └── database.py              # Conexão Oracle
│   │
│   ├── models/                      # Modelos de Dados
│   │   ├── __init__.py
│   │   ├── database_models.py       # Modelos SQLAlchemy (Oracle)
│   │   └── schemas.py               # Schemas Pydantic (Request/Response)
│   │
│   ├── repositories/                # Camada de Acesso a Dados
│   │   ├── __init__.py
│   │   ├── usuario_repository.py
│   │   ├── transacao_repository.py
│   │   ├── orcamento_repository.py
│   │   ├── categoria_repository.py
│   │   ├── tipo_renda_repository.py
│   │   └── previsao_ia_repository.py
│   │
│   ├── services/                    # Lógica de Negócio
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── usuario_service.py
│   │   ├── transacao_service.py
│   │   ├── orcamento_service.py
│   │   └── ia_analysis_service.py   # Simulação de IA
│   │
│   └── api/                         # Endpoints REST
│       ├── __init__.py
│       ├── dependencies.py          # Injeção de dependências
│       └── routers/
│           ├── __init__.py
│           ├── auth.py
│           ├── user.py
│           ├── transactions.py
│           ├── budget.py
│           └── dashboard.py
│
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md