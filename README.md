# Sistema de Gestão de Processos Jurídicos

Sistema web para advogados gerenciarem clientes e acompanharem processos judiciais, com foco nas áreas trabalhista, cível e previdenciária. O sistema integra a API pública do DataJud (CNJ) para monitorar movimentações processuais.

## Stack

- Backend: Python + Django
- Banco atual: SQLite
- Frontend: Django Templates (interface própria em desenvolvimento)
- Integração externa: API Pública do DataJud (CNJ)

## Estado atual

### Implementado

- Modelos de clientes, processos e movimentações
- Relacionamento Cliente → Processo → Movimentação
- Administração pelo Django Admin
- Integração com o DataJud
- Comando para verificar movimentações
- Prevenção de duplicação de movimentações
- Credenciais configuradas por variáveis de ambiente
- Configurações básicas de segurança

### Em desenvolvimento

- Login e autenticação da interface
- Dashboard
- Cadastro e edição pela interface própria
- Busca e filtros
- Linha do tempo
- Visualização e baixa de alertas
- Agendamento periódico da verificação
- Testes automatizados

### Futuro

- Controle de prazos
- Agenda de audiências
- Controle financeiro
- Múltiplos advogados/usuários
- Anexação de documentos
- Auditoria de acessos e alterações

## Verificação de movimentações

A rotina atual:

1. Seleciona processos não arquivados.
2. Ignora processos sem tribunal_alias.
3. Consulta o DataJud pelo número CNJ.
4. Converte e valida as datas recebidas.
5. Verifica se cada movimentação já existe usando processo, data, descrição e origem.
6. Insere somente movimentações novas.
7. Marca alerta_pendente quando há novidade.

Execução manual:

    python manage.py verificar_movimentacoes

O agendamento automático será implementado posteriormente.

## Segurança

O sistema lida com dados pessoais e, por isso, a segurança faz parte do desenvolvimento.

- DJANGO_SECRET_KEY é obrigatória e não fica no código.
- DATAJUD_API_KEY é obtida por variável de ambiente.
- .env não deve ser versionado.
- .env.example não contém credenciais.
- CSRF permanece habilitado pelo middleware do Django.
- Senhas serão tratadas pelo sistema de autenticação do Django.
- O ORM é usado para evitar SQL manual inseguro.
- Cookies seguros podem ser ativados para produção.
- HTTPS deve ser utilizado em produção.
- Backups, logs/auditoria e política de retenção ainda precisam ser implementados.

## Estrutura de dados

    Cliente
      |
      +-- Processo
            |
            +-- Movimentacao

### Cliente

Dados cadastrais da pessoa ou empresa atendida.

### Processo

Processo judicial vinculado a um cliente, contendo número CNJ, área, tribunal, fase e status.

### Movimentacao

Evento processual associado a um processo, contendo data, descrição e origem.

## Limitações conhecidas

- A consulta depende do número CNJ e do alias correto do tribunal.
- A disponibilidade de dados depende da API pública do DataJud.
- O sistema ainda não controla prazos processuais.
- A interface própria ainda está em desenvolvimento.
- A verificação ainda precisa ser ligada a um agendador para execução automática.

## Desenvolvimento

Crie um ambiente virtual:

    python -m venv .venv

Instale as dependências:

    pip install -r requirements.txt

Copie .env.example para .env e preencha pelo menos DJANGO_SECRET_KEY e DATAJUD_API_KEY.

Depois:

    python manage.py migrate
    python manage.py runserver

Para criar um usuário administrativo:

    python manage.py createsuperuser
