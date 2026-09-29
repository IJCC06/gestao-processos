# Sistema de Gestão de Processos Jurídicos

Sistema web para advogados gerenciarem clientes, processos judiciais, prazos e movimentações processuais. A aplicação utiliza a API pública do DataJud (CNJ) para consultar movimentações de processos.

## Stack

- Backend: Python + Flask
- ORM e banco: Flask-SQLAlchemy + SQLite por padrão
- Migrações: Flask-Migrate + Alembic
- Autenticação: Flask-Login
- Formulários e CSRF: Flask-WTF
- Frontend: Jinja2 Templates + HTML/CSS
- Integração externa: API Pública do DataJud (CNJ)

## Funcionalidades implementadas

- Autenticação de usuários
- Dashboard
- Cadastro de clientes com normalização e validação de CPF/CNPJ
- Cadastro de processos com validação de dados
- Página de detalhes do processo com resumo, prazos pendentes, movimentações e alertas
- Busca de processos por número CNJ, cliente ou tribunal
- Validação do número CNJ conforme o formato padronizado e dígitos verificadores
- Validação de área e status do processo
- Validação de valores da causa e honorários, aceitando apenas valores válidos e não negativos
- Edição de processos com preservação dos dados digitados quando houver erro
- Exclusão de processos com remoção em cascata de prazos e movimentações vinculados

- Filtros de processos por área e status
- Cadastro de prazos
- Área de notificações com resumo de prazos e movimentações pendentes
- Consulta manual de movimentações pelo DataJud, inclusive por processo
- Prevenção de duplicação de movimentações
- Proteção CSRF nos formulários
- Configuração por variáveis de ambiente
- Testes automatizados dos principais fluxos

## Atualização das movimentações

A atualização é feita manualmente dentro do sistema. Na área de notificações é possível atualizar os processos não arquivados em uma única operação, e na página de detalhes é possível atualizar somente um processo específico. Não há dependência de Celery, Redis ou outro serviço de tarefas em segundo plano.

A rotina valida as movimentações recebidas e grava somente novidades. Erros de configuração ou de comunicação com o DataJud são informados na interface, sem interromper a atualização dos demais processos em uma atualização geral.

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

As tabelas não são mais criadas automaticamente. O banco é controlado por migrações do Flask-Migrate/Alembic.

## Migrações do banco

Depois de instalar as dependências, use:

    flask --app app db upgrade

Para um banco SQLite existente que já contém o schema atual, marque a migração inicial como aplicada sem recriar as tabelas:

    flask --app app db stamp 0001_baseline

A partir daí, alterações futuras nos modelos devem ser feitas por novas migrações. Para gerar uma migração após alterar os modelos:

    flask --app app db migrate -m "descrever alteracao"

Revise a migração gerada antes de aplicá-la e depois execute:

    flask --app app db upgrade

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

## Backup do banco SQLite

O sistema possui backup manual e pode ser configurado para executar backups automaticamente no Windows. O backup usa a API nativa do SQLite, gerando uma cópia consistente mesmo enquanto a aplicação está em execução.

### Backup manual

Na pasta do projeto:

    scripts\backup_db.bat

Ou diretamente pela CLI:

    flask --app app backup-db

Por padrão, os backups são salvos em:

    backups\

e os arquivos seguem o formato:

    flask_AAAAMMDD_HHMMSS.db

O sistema mantém os últimos 30 dias de backups por padrão. Para alterar a retenção:

    flask --app app backup-db --retention-days 60

Também é possível definir outra pasta por meio de `BACKUP_DIR`.

### Backup automático no Windows

Execute uma vez:

    scripts\configurar_backup_automatico.bat

Isso cria uma tarefa do Agendador de Tarefas do Windows chamada `GestaoProcessos - Backup diario`, configurada para executar o backup todos os dias às 02:00.

Para remover a tarefa:

    schtasks /Delete /TN "GestaoProcessos - Backup diario" /F

O backup automático depende do computador estar ligado no horário programado. Se ele estiver desligado, a tarefa não executará retroativamente. Para maior segurança operacional, mantenha também cópias dos backups em outro local físico.

### Verificação do backup

Cada backup é validado com `PRAGMA integrity_check` antes de ser considerado concluído. Mesmo assim, um backup só deve ser considerado confiável depois de um teste real de restauração.

## Segurança

O sistema lida com dados pessoais e deve ser configurado com atenção antes de qualquer uso em produção.

- Segredos devem ficar em variáveis de ambiente.
- .env não deve ser versionado.
- CSRF está habilitado por meio do Flask-WTF.
- Senhas são armazenadas usando hash.
- HTTPS deve ser utilizado em produção.
- A chave secreta padrão deve ser substituída por uma chave forte.
- Backups locais são gerados pelo comando `backup-db` e podem ser agendados no Windows.
- O procedimento de restauração deve ser testado periodicamente antes do uso real.

## DataJud

A disponibilidade e o conteúdo das movimentações dependem da API pública do DataJud e da configuração correta do tribunal.

A chave da API deve ser configurada em DATAJUD_API_KEY e não deve ser publicada no repositório.
