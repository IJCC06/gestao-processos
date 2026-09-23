# Sistema de Gestão de Processos Jurídicos

Sistema web para advogados gerenciarem clientes e acompanharem processos judiciais, com foco nas áreas **trabalhista**, **cível** e **previdenciária**. O sistema integra a API pública do DataJud (CNJ) para monitorar automaticamente movimentações processuais, eliminando a necessidade de consulta manual repetida.

## Stack

- **Backend**: Python + Django
- **Banco de dados**: SQLite (produção inicial), com possibilidade de migração para PostgreSQL
- **Frontend**: HTML/CSS servido pelo próprio Django (templates), com Bootstrap para agilizar o layout
- **Integração externa**: API Pública do DataJud (CNJ)

---

## Funcionalidades

### Núcleo (MVP)

- **Cadastro de clientes** — nome, CPF/CNPJ, contato, endereço e observações
- **Cadastro de processos** — vinculado a um cliente, contendo:
  - Número único (CNJ)
  - Área do direito (trabalhista, cível ou previdenciário)
  - Tribunal/vara ou órgão
  - Fase atual e status (ativo, arquivado, suspenso)
- **Monitoramento automático via DataJud** — consulta periódica ao histórico de movimentações de cada processo cadastrado
- **Alertas de movimentação nova** — o sistema sinaliza no painel quando algo mudou desde a última verificação
- **Painel de busca e filtro** — localizar processos por cliente, número ou área do direito
- **Linha do tempo do processo** — histórico de movimentações exibido de forma cronológica

### Extensões futuras (fora do MVP)

- Controle de prazos processuais com alertas antecipados
- Agenda de audiências
- Controle financeiro (honorários combinados x recebidos)
- Suporte a múltiplos advogados/usuários no mesmo escritório
- Anexação de documentos (procurações, petições, contratos)

---

## Lógica dos fluxos

### Fluxo principal de uso

1. O advogado acessa o sistema (login)
2. Visualiza o painel com todos os clientes e processos cadastrados
3. Cadastra um novo processo, vinculando-o a um cliente e informando o número CNJ
4. O sistema passa a monitorar esse processo automaticamente
5. Quando uma movimentação nova é detectada, um alerta aparece no painel

### Lógica da verificação automática (DataJud)

1. Uma rotina periódica (job agendado) percorre todos os processos ativos cadastrados no sistema
2. Para cada processo, o sistema consulta a API pública do DataJud usando o número CNJ
3. A resposta traz a lista de movimentações daquele processo
4. O sistema compara a movimentação mais recente retornada com a última movimentação já registrada no banco local
5. Se houver diferença, uma nova entrada é criada na linha do tempo do processo e o status do processo passa a exibir "alerta pendente" até que o advogado visualize
6. Processos arquivados ou encerrados são excluídos da rotina de verificação, para economizar chamadas à API

### Limitações conhecidas

- O DataJud não indexa nome de partes nem número de OAB — a busca de processos precisa ser feita pelo número CNJ, já conhecido e cadastrado manualmente
- A API não fornece prazos processuais, apenas movimentações — o controle de prazos continua dependendo de registro manual pelo advogado
- Dados de processos em segredo de justiça não são retornados pela API pública

---

## Métodos de proteção e segurança

Como o sistema armazena dados pessoais de clientes (nome, CPF, contato), ele deve seguir boas práticas de segurança e os princípios da LGPD (Lei Geral de Proteção de Dados).

### Autenticação e acesso

- Login obrigatório para acessar qualquer parte do sistema (sem exceções)
- Senhas armazenadas com hash (mecanismo padrão do Django — nunca em texto puro)
- Sessão com expiração automática por inatividade
- Isolamento de dados por usuário, caso o sistema venha a suportar mais de um advogado no futuro

### Proteção de dados

- Nenhuma credencial (chave de API, senha de banco de dados) fica escrita diretamente no código — tudo fica em variáveis de ambiente, fora do controle de versão
- Proteção contra CSRF em todos os formulários (recurso nativo do Django)
- Proteção contra SQL Injection via uso do ORM do Django (nenhuma query SQL manual concatenada)
- Backups periódicos do banco de dados, já que ele contém informações sensíveis de clientes

### Boas práticas gerais

- Em produção, o sistema deve rodar exclusivamente sob HTTPS
- Princípio do mínimo privilégio: cada usuário só acessa os dados que precisa
- Logs de acesso e alteração, para rastrear quem viu ou modificou um processo (auditoria básica)

---

## Estrutura de dados (visão geral)

- **Cliente** — dados cadastrais da pessoa/empresa atendida
- **Processo** — vinculado a um Cliente; guarda número CNJ, área, tribunal, fase e status
- **Movimentação** — vinculada a um Processo; guarda data, descrição e origem (DataJud)
