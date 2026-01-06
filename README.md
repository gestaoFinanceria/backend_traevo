# 💰 Traevo - Backend FastAPI

Backend completo para o aplicativo **Traevo**, uma plataforma de finanças inteligentes focada em simplicidade e acessibilidade.

## 🚀 Stack Tecnológica

- **Python +**
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para Oracle Database
- **Oracle Database** - Banco de dados corporativo
- **JWT** - Autenticação com tokens
- **Bcrypt** - Hashing seguro de senhas
- **Pydantic** - Validação de dados

## 📁 Estrutura do Projeto

```
traevo-backend/
├── app/
│   ├── core/              # Configurações e segurança
│   │   ├── config.py      # Variáveis de ambiente
│   │   ├── database.py    # Conexão Oracle
│   │   └── security.py    # JWT e Bcrypt
│   ├── models/            # Modelos de dados
│   │   ├── database_models.py  # SQLAlchemy models
│   │   └── schemas.py          # Pydantic schemas
│   ├── repositories/      # Acesso a dados (CRUD)
│   ├── services/          # Lógica de negócio
│   ├── api/routers/       # Endpoints REST
│   └── main.py            # Aplicação principal
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## 🛠️ Instalação Local

### 1. Pré-requisitos

- Python 3.11+
- Oracle Database (ou acesso remoto)
- Oracle Instant Client

### 2. Clonar repositório

```bash
git clone <seu-repositorio>
cd traevo-backend
```

### 3. Criar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 4. Instalar dependências

```bash
pip install -r requirements.txt
```

### 5. Configurar variáveis de ambiente

Copie `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

```env
ORACLE_USER=seu_usuario
ORACLE_PASSWORD=sua_senha
ORACLE_DSN=localhost:1521/XEPDB1
JWT_SECRET_KEY=sua_chave_secreta_super_segura
```

### 6. Executar a aplicação

```bash
uvicorn app.main:app --reload
```

A API estará disponível em: `http://localhost:8000`

Documentação interativa: `http://localhost:8000/docs`

## 🔑 Endpoints Principais

### Autenticação

- `POST /auth/register` - Registrar novo usuário
- `POST /auth/login` - Fazer login (tokens em cookies)
- `POST /auth/refresh` - Renovar token de acesso
- `POST /auth/logout` - Fazer logout

### Usuário

- `GET /me` - Obter perfil do usuário
- `PATCH /me` - Atualizar perfil

### Transações

- `POST /transactions` - Criar transação
- `GET /transactions` - Listar transações (com filtros)
- `DELETE /transactions/{id}` - Deletar transação

### Orçamentos

- `POST /budget` - Criar orçamento
- `GET /budget` - Listar orçamentos do mês
- `DELETE /budget/{id}` - Deletar orçamento

### Dashboard

- `GET /dashboard/overview` - **Endpoint principal!** Retorna:
  - KPIs do mês (entradas, saídas, saldo)
  - Orçamentos com status
  - Previsão da IA (risco e insights)
  - Estatísticas adicionais

- `POST /dashboard/refresh-prediction` - Atualizar previsão da IA

## 📊 Simulação de IA

O serviço `IAAnalysisService` implementa uma **simulação de IA** que:

1. **Coleta histórico** de 6 meses de transações
2. **Calcula média móvel** de gastos
3. **Projeta gastos futuros** baseado em tendências
4. **Determina índice de risco**:
   - 🟢 **VERDE**: Gastos < 70% do orçamento
   - 🟡 **AMARELO**: Gastos entre 70-90%
   - 🔴 **VERMELHO**: Gastos > 90% ou tendência crítica
5. **Gera insights personalizados** com mensagens encorajadoras

### Regras de Negócio da IA

```python
# VERMELHO: Situação crítica
- Gasto projetado > 90% do orçamento total
- Gastou > 70% antes do dia 20 do mês

# AMARELO: Atenção necessária
- Gasto projetado entre 70-90%
- Tendência crescente + gasto atual > 50%

# VERDE: Situação saudável
- Gasto projetado < 70%
- Tendência estável ou decrescente
```

## 🐳 Deploy com Docker

### 1. Build da imagem

```bash
docker build -t traevo-backend .
```

### 2. Executar container

```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name traevo-api \
  traevo-backend
```

## 🚢 Deploy no Render

### 1. Configurar no Render

1. Crie um novo **Web Service**
2. Conecte seu repositório GitHub
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 2. Variáveis de ambiente

Adicione no Render:

```
ORACLE_USER=seu_usuario
ORACLE_PASSWORD=sua_senha
ORACLE_DSN=seu_dsn_oracle
JWT_SECRET_KEY=sua_chave_secreta
ALLOWED_ORIGINS=https://seu-frontend.com
```

## 🔒 Segurança

### Autenticação JWT

- **Access Token**: Válido por 30 minutos
- **Refresh Token**: Válido por 7 dias
- Tokens armazenados em **cookies HttpOnly** (não acessíveis via JavaScript)

### Isolamento de Dados

- **Todas** as queries filtram por `ID_USUARIO`
- Usuário nunca acessa dados de outros usuários
- Validação em todas as camadas (Repository, Service, Router)

### Senhas

- Hash com **Bcrypt** (salt automático)
- Senha nunca retornada nas APIs
- Mínimo de 6 caracteres (configurável)

## 📈 Próximos Passos (Roadmap)

### MVP Atual ✅
- [x] CRUD completo de transações
- [x] Orçamentos mensais
- [x] Dashboard consolidado
- [x] Simulação de IA com regras de negócio

### Fase 2 🚧
- [ ] Substituir simulação por ML real (Regressão Linear, ARIMA)
- [ ] Jobs em background (Celery/APScheduler)
- [ ] Notificações por email/push
- [ ] Exportar relatórios (PDF/Excel)
- [ ] Categorias inteligentes (ML para classificação)

### Fase 3 🔮
- [ ] Multi-moeda
- [ ] Integração com bancos (Open Banking)
- [ ] Metas de economia
- [ ] Análise comparativa (usuário vs média)

## 🧪 Testando a API

### Exemplo com cURL

#### 1. Registrar usuário

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "email": "joao@example.com",
    "senha": "senha123"
  }'
```

#### 2. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@example.com",
    "senha": "senha123"
  }' \
  -c cookies.txt
```

#### 3. Criar transação

```bash
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN" \
  -d '{
    "id_categoria": "uuid-da-categoria",
    "descricao": "Almoço no restaurante",
    "valor": 45.50,
    "data_transacao": "2025-12-19",
    "tipo": "SAIDA"
  }'
```

#### 4. Dashboard

```bash
curl -X GET http://localhost:8000/dashboard/overview \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

## 📝 Convenções de Código

### Nomenclatura

- **Variáveis**: `snake_case`
- **Classes**: `PascalCase`
- **Constantes**: `UPPER_CASE`
- **Funções**: `snake_case`

### Comentários

- Docstrings em todas as funções públicas
- Type hints obrigatórios
- Comentários inline para lógica complexa

### Commits

```
feat: adiciona endpoint de categorias personalizadas
fix: corrige cálculo de percentual no orçamento
docs: atualiza README com exemplos de uso
refactor: melhora performance da query de transações
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'feat: adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.

## 👥 Equipe
Felipe Ferrete - Desenvolvedor BackEnd e Modelos de IA
Gustavo Bosak - Desenvolvedor FrontEnd

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no GitHub.

---

**Desenvolvido com ❤️ usando FastAPI**