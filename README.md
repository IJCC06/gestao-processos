# Gestão de Processos

> Aplicação desktop local para advogados gerenciarem clientes, processos, prazos e movimentações processuais em um único sistema.

**Primeira versão de lançamento: v1.0.0**  
**Desenvolvedor:** Gabriel Menegon Cassano

O Gestão de Processos foi desenvolvido para uso local em computadores Windows. A aplicação utiliza a **API Pública do DataJud (CNJ)** para consultar movimentações processuais quando solicitado pelo usuário.

---

## Visão geral

O sistema reúne recursos para:

- cadastro e gerenciamento de clientes;
- cadastro e gerenciamento de processos;
- controle de prazos;
- dashboard com informações relevantes;
- notificações de prazos;
- consulta e atualização de movimentações pelo DataJud;
- histórico de auditoria;
- gerenciamento de usuários e permissões administrativas;
- backup local do banco de dados.

A aplicação funciona localmente no computador do escritório e **não exige Docker, Redis, Celery ou outro serviço de tarefas em segundo plano**.

---

## Download e instalação

A versão distribuída para usuários finais é o instalador:

`GestaoProcessos-Setup.exe`

Os instaladores oficiais ficam na seção **Releases** do repositório.

### Requisitos do usuário final

O usuário final não precisa instalar:

- Python;
- Flask;
- Git;
- PyInstaller;
- Inno Setup;
- Redis;
- Docker.

O instalador já contém os componentes necessários para executar a aplicação.

### Primeira instalação

1. Baixe o `GestaoProcessos-Setup.exe` da Release desejada.
2. Execute o instalador.
3. Finalize a instalação.
4. Abra o atalho **Gestão de Processos** criado na Área de Trabalho.
5. Na primeira execução, conclua a **Configuração Inicial**.

Na configuração inicial, informe:

- nome de usuário do administrador;
- senha;
- chave da API Pública do DataJud.

Depois disso, faça login normalmente.

### Atualização

Para atualizar uma instalação existente:

1. faça um backup do banco;
2. feche o sistema;
3. baixe o instalador da nova versão;
4. execute o instalador;
5. abra o sistema novamente.

As migrações do banco são aplicadas automaticamente durante a inicialização do aplicativo.

---

## Dados e arquivos locais

O aplicativo instalado mantém os dados fora da pasta de instalação, em:

`%LOCALAPPDATA%\GestaoProcessos`

Entre os arquivos e diretórios mantidos nesse local estão:

| Local | Finalidade |
|---|---|
| `flask.db` | Banco de dados SQLite |
| `.env` | Configurações locais e chave do DataJud |
| `logs\app.log` | Logs da aplicação |
| `logs\launcher.log` | Erros do inicializador |
| `backups\` | Backups locais do banco |

Manter o banco separado da pasta de instalação permite atualizar o programa sem substituir os dados do usuário.

> **Importante:** o banco contém dados potencialmente sensíveis. Não compartilhe `flask.db`, arquivos de backup ou a chave do DataJud publicamente.

---

## Backup

Administradores podem criar backups em:

**Administração → Fazer backup → Criar backup**

Por padrão, o sistema mantém os backups dos últimos 30 dias.

Para maior segurança, mantenha pelo menos uma cópia de backup em outro local, separado do computador que executa o sistema.

Antes de uma atualização importante, recomenda-se criar um backup.

---

## DataJud

O sistema utiliza a **API Pública do DataJud do Conselho Nacional de Justiça (CNJ)** para consultar movimentações processuais.

A consulta é feita quando solicitada pelo usuário. O sistema não mantém um worker ou agendador de consultas em segundo plano.

A disponibilidade das movimentações depende:

- da disponibilidade da API do DataJud;
- do tribunal consultado;
- da chave de API configurada;
- da conectividade de internet.

Erros temporários, como indisponibilidade ou limitação da API, podem impedir uma consulta sem significar perda dos dados já armazenados no sistema.

A chave da API não é registrada nos logs.

---

## Segurança e privacidade

O sistema foi projetado para uso local, mas pode armazenar dados pessoais e informações relacionadas a processos.

Boas práticas:

- use uma senha forte para os usuários;
- não compartilhe sua chave do DataJud;
- não envie `.env` para o GitHub;
- não publique o banco SQLite ou backups;
- mantenha backups atualizados;
- mantenha o Windows e as dependências atualizados;
- use o sistema somente em computadores confiáveis.

O Gestão de Processos é uma ferramenta de gerenciamento. A conferência das informações processuais e o cumprimento dos prazos continuam sendo responsabilidade do profissional que utiliza o sistema.

---

# Desenvolvimento

## Tecnologias

| Área | Tecnologia |
|---|---|
| Backend | Python + Flask |
| Banco de dados | SQLite |
| ORM | Flask-SQLAlchemy |
| Migrações | Flask-Migrate + Alembic |
| Autenticação | Flask-Login |
| Formulários e CSRF | Flask-WTF |
| Templates | Jinja2 |
| Frontend | HTML + CSS |
| API externa | DataJud (CNJ) |
| Testes | unittest |
| Empacotamento | PyInstaller |
| Instalador | Inno Setup 6 |

## Estrutura

```text
gestao-processos/
├── app.py
├── requirements.txt
├── requirements-build.txt
├── GestaoProcessos.spec
├── config/
├── migrations/
├── processos/
│   ├── models.py
│   ├── routes/
│   ├── services/
│   ├── templates/
│   └── static/
├── scripts/
│   ├── build_windows.bat
│   ├── backup_db.bat
│   └── configurar_backup_automatico.bat
├── installer/
│   └── GestaoProcessos.iss
└── .github/
    └── workflows/
```

---

## Configurando o ambiente de desenvolvimento

### 1. Clonar o repositório

```bash
git clone https://github.com/IJCC06/gestao-processos.git
cd gestao-processos
git checkout desenvolvimento
```

### 2. Criar o ambiente virtual

No Windows:

```bat
python -m venv venv
```

### 3. Ativar o ambiente virtual

```bat
venv\Scripts\activate
```

### 4. Instalar as dependências

```bat
pip install -r requirements.txt
```

### 5. Configurar o ambiente

Crie um arquivo `.env` na raiz do projeto. Um modelo está disponível em [`.env.example`](.env.example).

Exemplo:

```env
FLASK_SECRET_KEY=uma-chave-secreta-forte
FLASK_DEBUG=True
DATAJUD_API_KEY=sua-chave-do-datajud
```

> Nunca versione o arquivo `.env`.

---

## Executando em desenvolvimento

Com o ambiente virtual ativado:

```bat
flask --app app run --debug
```

Abra:

```text
http://127.0.0.1:5000/
```

---

## Testes

A suíte de testes utiliza o `unittest`, sem depender do pytest.

Execute:

```bat
python -m unittest discover -v
```

Na preparação da versão **v1.0.0**, a suíte foi executada com:

```text
Ran 81 tests in 4.504s

OK
```

Antes de publicar uma nova versão, execute novamente a suíte completa.

---

## Banco de dados e migrações

O projeto utiliza Flask-Migrate e Alembic.

Criar uma migração:

```bat
flask --app app db migrate -m "descricao da alteracao"
```

Aplicar migrações:

```bat
flask --app app db upgrade
```

Ver a versão atual:

```bat
flask --app app db current
```

Evite alterar o banco manualmente quando a alteração puder ser representada por uma migração.

---

## Backup em desenvolvimento

Para criar um backup pelo CLI:

```bat
flask --app app backup-db
```

Também está disponível:

```bat
scripts\backup_db.bat
```

O script `scripts\configurar_backup_automatico.bat` pode ser usado para configurar uma tarefa agendada do Windows em ambientes de desenvolvimento ou administração local.

---

## Gerando o instalador Windows

O ambiente de build precisa de:

- Python;
- ambiente virtual do projeto;
- Inno Setup 6.

O usuário final não precisa dessas ferramentas.

Na raiz do projeto:

```bat
scripts\build_windows.bat
```

O processo executa:

```text
Código Flask
    ↓
PyInstaller
    ↓
GestaoProcessos.exe
    ↓
Inno Setup 6
    ↓
GestaoProcessos-Setup.exe
```

O instalador é gerado em:

```text
installer_output\GestaoProcessos-Setup.exe
```

Os diretórios de build e o instalador gerado não devem ser versionados.

---

## Checklist de publicação

Antes de publicar uma nova Release:

- [ ] executar a suíte completa de testes;
- [ ] gerar o instalador localmente;
- [ ] instalar o `GestaoProcessos-Setup.exe` em um ambiente limpo;
- [ ] testar a configuração inicial;
- [ ] testar login e logout;
- [ ] criar cliente;
- [ ] criar processo;
- [ ] criar prazo;
- [ ] verificar notificações;
- [ ] executar uma atualização pelo DataJud;
- [ ] confirmar persistência dos dados após fechar e reabrir o aplicativo;
- [ ] testar backup;
- [ ] confirmar que não há `.env`, banco, logs ou outros dados pessoais no repositório;
- [ ] conferir a versão do instalador;
- [ ] criar a tag da versão;
- [ ] publicar a Release.

---

## Releases

O projeto possui GitHub Actions para gerar automaticamente o instalador Windows quando uma tag no formato `v*` é publicada.

Para a primeira versão:

```bash
git tag v1.0.0
git push origin v1.0.0
```

O workflow:

1. baixa o código;
2. configura Python;
3. instala o Inno Setup;
4. cria o ambiente de build;
5. gera o executável com PyInstaller;
6. gera o instalador;
7. anexa o `GestaoProcessos-Setup.exe` à Release.

Antes de publicar a tag, faça a validação local descrita no checklist acima.

---

## Contribuição

Alterações devem ser feitas de forma organizada e acompanhadas dos testes necessários.

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para o fluxo recomendado de desenvolvimento.

Para informações sobre comunicação de vulnerabilidades, consulte [SECURITY.md](SECURITY.md).

---

## Autor

**Gabriel Menegon Cassano**

Desenvolvedor do Gestão de Processos.

---

## Licença

A licença do projeto ainda deve ser definida pelo mantenedor antes de uma distribuição pública do código.

---

## Estado da versão

**v1.0.0 — lançamento inicial**

A versão de lançamento foi validada com a suíte automatizada e com a geração do instalador Windows. A integração com o DataJud depende da disponibilidade da API externa e da chave de API configurada pelo usuário.
