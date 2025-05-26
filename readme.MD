## Configuração do Ambiente de Desenvolvimento Local

1.  **Pré-requisitos:**

    - Python 3.12+
    - PostgreSQL instalado e rodando.
    - python-dotenv.
    - Alembic.

2.  **Clonar o Repositório:**

    ```bash
    git clone https://github.com/AbnerTavares14/Lu-Estilo-Teste-Tecnico.git
    cd <nome-do-repositorio>
    ```

3.  **Configurar Ambiente Virtual:**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    # .venv\Scripts\activate    # Windows
    ```

4.  **Instalar Dependências:**

    ```bash
    pip install -r requirements.txt
    ```

5.  **Configurar Variáveis de Ambiente:**

    - Copie o arquivo `.env.example` para `.env`.
    - Edite o arquivo `.env` com as suas configurações locais:

    - **Importante:** Substitua `USER`, `PASSWORD`, `HOST`, `PORT`, `DATABASE_NAME` pelas credenciais do seu banco de dados PostgreSQL local. Crie o banco de dados se ele não existir.

6.  **Executar Migrações do Banco de Dados:**

    ```bash
    alembic upgrade head
    ```

7.  **Rodar a Aplicação FastAPI Localmente:**
    ```bash
    uvicorn app.main:app --reload
    ```
    A API estará disponível em `http://127.0.0.1:8000`.

## Rodando com Docker (Localmente)

1.  **Pré-requisitos:**

    - Docker
    - Docker Compose

2.  **Configurar Variáveis de Ambiente para Docker:**

    - Copie o arquivo  `.env.example` para `.env`.
    - Edite o arquivo `.env` com as configurações para o ambiente Docker. Note que `DATABASE_URL` não é necessária aqui, pois é construída no `docker-compose.yaml` usando `DB_USER`, `DB_PASSWORD`, `DB_NAME`.

3.  **Construir e Iniciar os Contêineres:**
    Na raiz do projeto, execute:

    ```bash
    docker compose up --build
    ```

    Para rodar em background:

    ```bash
    docker compose up --build -d
    ```

    O script `entrypoint.sh` cuidará de rodar as migrações do Alembic antes de iniciar a aplicação.

4.  **Acessar a API:**

    - API: `http://localhost:8000`
    - Documentação Swagger: `http://localhost:8000/docs`
    - Documentação ReDoc: `http://localhost:8000/redoc`

5.  **Parar os Contêineres:**
    ```bash
    docker compose down
    ```
    Para remover os volumes (incluindo dados do banco):
    ```bash
    docker compose down -v
    ```

## Documentação da API (Endpoints)

A documentação da API é gerada automaticamente pelo FastAPI e está disponível em:

- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`

Os principais grupos de endpoints são:

- `/auth`: Autenticação e gerenciamento de tokens.
- `/clients`: Gerenciamento de clientes.
- `/products`: Gerenciamento de produtos.
- `/orders`: Gerenciamento de pedidos.

Consulte a documentação interativa para exemplos de requisições e respostas para cada endpoint.

## Migrações do Banco de Dados (Alembic)

As migrações do esquema do banco de dados são gerenciadas pelo Alembic.

- Para gerar uma nova revisão após alterações nos modelos SQLAlchemy:
  ```bash
  alembic revision -m "breve_descricao_da_mudanca" --autogenerate
  ```
- Para aplicar as migrações ao banco de dados:
  ```bash
  alembic upgrade head
  ```
- Para reverter a última migração:
  ```bash
  alembic downgrade -1
  ```

## Testes

O projeto utiliza Pytest para testes unitários e de integração.

- Para rodar todos os testes:
  ```bash
  pytest -v app/tests
  ```
- Para rodar apenas testes unitários:
  ```bash
  pytest -v app/tests/unit/
  ```
- Para rodar apenas testes de integração:
  ```bash
  pytest -v app/tests/integration/
  ```
- Para gerar um relatório de cobertura de testes:
  ```bash
  pytest --cov=app
  ```

## Deploy

A aplicação foi configurada para deploy utilizando Docker. Um exemplo de deploy foi realizado na plataforma **Render** : https://lu-estilo-teste-tecnico.onrender.com


## Funcionalidades Adicionais (Desafios)

### Integração com WhatsApp

- A API inclui uma funcionalidade para enviar notificações automáticas para clientes via WhatsApp em eventos como criação de pedidos ou atualização de status.
- **Implementação Atual:** Para este teste técnico, a integração foi realizada utilizando a **Sandbox do Twilio API for WhatsApp**. Isso permite o envio de mensagens para números de telefone previamente conectados à sandbox (geralmente o número do desenvolvedor para teste).
- **Variáveis de Ambiente Necessárias (para Twilio):**
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_WHATSAPP_FROM_NUMBER` (Número da sandbox do Twilio)
  - `TWILIO_WHATSAPP_TO_NUMBER` (Opcional, usado nos testes para definir um destinatário padrão que está conectado à sandbox)
- **Para Produção:** Seria necessário migrar da sandbox para a API oficial do WhatsApp Business (via Twilio ou diretamente com a Meta), o que envolve ter um número de telefone comercial verificado e aprovação de templates de mensagem para notificações iniciadas pela empresa. A estrutura de serviço (`WhatsappService`) está pronta para ser adaptada para um provedor de produção.

### Controle de Acesso Baseado em Roles

- A API implementa dois níveis de acesso: `admin` e `user` (usuário regular).
- **Usuário Regular (`user`):**
  - Pode se registrar e logar.
  - Pode gerenciar clientes (criar, listar, ver, atualizar), mas **não** deletar.
  - Pode apenas visualizar produtos.
  - Pode gerenciar pedidos (criar, listar, ver, atualizar status e itens), mas **não** deletar.
- **Administrador (`admin`):**
  - Possui permissões CRUD completas sobre todas as entidades: Clientes, Produtos e Pedidos.

## (Opcional) Próximos Passos / Melhorias Futuras

- Implementação de um pipeline de CI/CD completo (ex: GitHub Actions) para automatizar testes e deploy.
- Sistema de "propriedade" para Clientes e Pedidos, permitindo que usuários regulares gerenciem apenas seus próprios registros.
- Implementação de upload de arquivos para imagens de produtos, em vez de apenas URLs.
- Logging e monitoramento de erros mais detalhados e centralizados (além da configuração básica do Sentry).
- Testes de carga e performance.
- Validação de número de telefone mais robusta usando bibliotecas especializadas.

---
