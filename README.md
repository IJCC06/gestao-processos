# Sistema de Gestão de Processos Jurídicos

Sistema web para advogados gerenciarem clientes, processos judiciais, prazos e movimentações processuais. A aplicação utiliza a API pública do DataJud (CNJ) para consultar movimentações de processos.

## Stack

- Backend: Python + Flask
- ORM e banco: Flask-SQLAlchemy + SQLite por padrão
- Autenticação: Flask-Login
- Formulários e CSRF: Flask-WTF
- Frontend: Jinja2 Templates + HTML/CSS
- Integração externa: API Pública do DataJud (CNJ)

## Funcionalidades implementadas

- Autenticação de usuários
- Dashboard
- Cadastro de clientes
- Cadastro de processos
- Cadastro de prazos
- Área de notificações
- Consulta manual de movimentações pelo DataJud
- Prevenção de duplicação de movimentações
- Proteção CSRF nos formulários
- Configuração por variáveis de ambiente
- Testes automatizados dos principais fluxos

## Atualização das movimentações

A atualização é feita manualmente dentro do sistema, pela área de notificações. Não há dependência de Celery, Redis ou outro serviço de tarefas em segundo plano.

A rotina seleciona processos não arquivados, consulta o DataJud, valida as movimentações recebidas e grava somente novidades.

Também é possível executar a rotina pela CLI do Flask:

    flask verificar-movimentacoes

## Configuração

Crie um ambiente virtual:

    python -m venv .venv

No Windows:

    .venv\Scripts\activate

Instale as dependências:

    pip install -r requirements.txt

Copie .env.example para .env e configure as variáveis necessárias, incluindo:

    FLASK_SECRET_KEY=sua-chave-secreta
    DATAJUD_API_KEY=sua-chave-do-datajud

O banco padrão é SQLite e será criado como flask.db.

## Execução

    flask --app app run --debug

A aplicação também pode ser executada com:

    python app.py

As tabelas são criadas automaticamente na inicialização da aplicação.

## Testes

    python -m unittest discover processos -p "test*.py" -v

Os testes utilizam SQLite em memória para não alterar o banco local de desenvolvimento.

## Estrutura

    .
    ├── app.py
    ├── config/
    │   └── settings.py
    ├── processos/
    │   ├── models.py
    │   ├── extensions.py
    │   ├── routes/
    │   ├── services/
    │   ├── static/
    │   └── tests.py
    ├── .env.example
    ├── .gitignore
    └── requirements.txt

## Segurança

O sistema lida com dados pessoais e deve ser configurado com atenção antes de qualquer uso em produção.

- Segredos devem ficar em variáveis de ambiente.
- .env não deve ser versionado.
- CSRF está habilitado por meio do Flask-WTF.
- Senhas são armazenadas usando hash.
- HTTPS deve ser utilizado em produção.
- A chave secreta padrão deve ser substituída por uma chave forte.
- Backups, auditoria e política de retenção devem ser definidos antes da implantação em produção.

## DataJud

A disponibilidade e o conteúdo das movimentações dependem da API pública do DataJud e da configuração correta do tribunal.

A chave da API deve ser configurada em DATAJUD_API_KEY e não deve ser publicada no repositório.
