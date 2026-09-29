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

## Instalação no Windows

A instalação foi preparada para que um usuário sem conhecimento de programação possa configurar o sistema com um único instalador.

### Requisitos

- Windows 10 ou Windows 11
- Python 3 instalado no computador
- Acesso à internet durante a instalação, para baixar as dependências
- Chave da API pública do DataJud, caso o monitoramento de processos seja utilizado

### Instalação

1. Baixe o código da versão mais recente pela área **Releases** do GitHub.
2. Extraia o arquivo ZIP em uma pasta do computador.
3. Entre na pasta extraída.
4. Dê dois cliques em:

       scripts\instalar_sistema.bat

5. O instalador irá:
   - criar o ambiente virtual Python;
   - instalar as dependências;
   - criar automaticamente uma chave secreta para a instalação;
   - solicitar a chave do DataJud;
   - preparar o banco SQLite com as migrações;
   - solicitar os dados do primeiro administrador;
   - criar o atalho **Gestão de Processos** na Área de Trabalho.

A senha do administrador deve ter pelo menos 8 caracteres.

A chave do DataJud pode ser deixada em branco durante a instalação e configurada posteriormente no arquivo `.env`.

### Uso diário

Depois da instalação, não é necessário abrir o CMD.

Basta dar dois cliques no atalho **Gestão de Processos** criado na Área de Trabalho. O sistema inicia o servidor local e abre o navegador automaticamente.

### Configuração do DataJud

A chave da API fica somente no arquivo local `.env` e não deve ser enviada ao GitHub.

Se for necessário configurá-la depois da instalação, abra o arquivo:

       .env

e preencha:

       DATAJUD_API_KEY=sua-chave-do-datajud

### Atualização de uma instalação existente

Para atualizar uma instalação já existente:

1. Faça uma cópia/backup do banco `flask.db`.
2. Baixe a nova versão.
3. Substitua os arquivos do sistema, preservando o arquivo `.env` e o banco local.
4. Execute novamente `scripts\\instalar_sistema.bat`.

O instalador é preparado para reaproveitar o ambiente virtual, a configuração existente e o banco. As novas migrações serão aplicadas automaticamente.

### Instalação manual

Para desenvolvimento ou manutenção, também é possível configurar o projeto manualmente:

    python -m venv .venv

No Windows:

    .venv\Scripts\activate

Instale as dependências:

    pip install -r requirements.txt

Copie `.env.example` para `.env` e configure:

    FLASK_SECRET_KEY=sua-chave-secreta
    DATAJUD_API_KEY=sua-chave-do-datajud

Depois aplique as migrações:

    flask --app app db upgrade

O banco padrão é SQLite.

## Execução

    flask --app app run --debug

A aplicação também pode ser executada com:

    python app.py

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
