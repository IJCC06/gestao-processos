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

A versão distribuída para usuários finais será um aplicativo Windows empacotado. **Sua mãe não precisa instalar Python, criar ambiente virtual ou usar o CMD.**

### Para o usuário final

1. Baixe o instalador `GestaoProcessos-Setup.exe` na versão mais recente da área **Releases**.
2. Execute o instalador.
3. Siga as etapas do instalador.
4. Ao terminar, o atalho **Gestão de Processos** será criado na Área de Trabalho.
5. Na primeira abertura, o sistema mostrará a tela de configuração inicial para criar o primeiro administrador e, opcionalmente, informar a chave do DataJud.

Depois da instalação, o uso diário é apenas:

    Área de Trabalho -> Gestão de Processos

O aplicativo contém o runtime Python e as dependências necessários. Não é necessário instalar Python separadamente.

### Dados do usuário

Os dados da aplicação ficam fora da pasta do executável, em uma pasta local do usuário:

    %LOCALAPPDATA%\GestaoProcessos

Isso inclui:

- banco SQLite;
- configuração local;
- logs;
- backups.

Assim, uma atualização do programa não precisa apagar os dados existentes.

### Desenvolvimento e geração do instalador

Apenas quem desenvolve o projeto precisa de Python.

Para gerar o instalador Windows em uma máquina de desenvolvimento:

1. Tenha Python 3 instalado.
2. Tenha o Inno Setup 6 instalado.
3. Crie o ambiente virtual:

       python -m venv venv

4. Execute:

       scripts\build_windows.bat

O processo instala as ferramentas de build, gera o executável com PyInstaller e cria:

       installer_output\GestaoProcessos-Setup.exe

O instalador é criado com o Inno Setup e já inclui o runtime Python e as dependências dentro do aplicativo.

### Atualizações

Antes de atualizar uma instalação existente, faça um backup do banco.

A nova versão deve preservar os dados armazenados em:

    %LOCALAPPDATA%\GestaoProcessos

As migrações do Flask-Migrate são aplicadas automaticamente quando o aplicativo é iniciado.

### Instalação manual para desenvolvimento

Para desenvolvimento ou manutenção, continua disponível a instalação tradicional:

    python -m venv .venv

No Windows:

    .venv\Scripts\activate

    pip install -r requirements.txt

Configure o arquivo `.env` e execute:

    flask --app app run --debug

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
