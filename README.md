# Gestão de Processos Jurídicos

> Sistema web local para **advogados** gerenciarem clientes, processos, prazos e movimentações processuais.

O sistema utiliza a **API Pública do DataJud (CNJ)** para consultar movimentações processuais.

---

## 🚀 Comece aqui

Você está apenas **usando o sistema**?

👉 Vá para [**1. Usuário**](#1-usuário).

Você está **desenvolvendo, testando ou mantendo o projeto**?

👉 Vá para [**2. Desenvolvedor**](#2-desenvolvedor).

---

# 1. 👤 Usuário

Esta seção é para quem vai **usar o Gestão de Processos no dia a dia**.

## O que preciso instalar?

### Primeira instalação

Você só precisa do:

**GestaoProcessos-Setup.exe**

Você **não precisa instalar**:

- Python
- Flask
- Git
- PyInstaller
- Inno Setup
- Redis
- Docker
- nenhuma dependência de desenvolvimento

> O aplicativo distribuído já contém o Python e as dependências necessárias.

---

## 📥 Instalando pela primeira vez

### Passo 1 — Baixe o instalador

Baixe o arquivo **GestaoProcessos-Setup.exe** na versão desejada em **Releases** do GitHub.

### Passo 2 — Instale

Dê **duplo clique** no instalador e siga as etapas.

Ao finalizar, será criado um atalho:

**Área de Trabalho → Gestão de Processos**

### Passo 3 — Abra o sistema

Abra o atalho **Gestão de Processos**.

O sistema inicia um servidor local no próprio computador e abre a aplicação no navegador.

> O sistema foi pensado para funcionar localmente. Ele não precisa ser publicado na internet para ser utilizado no computador do escritório.

---

## 🆕 Primeiro acesso

Na primeira execução, o sistema apresenta a tela de **Configuração Inicial**.

Nela, crie:

- nome de usuário do administrador;
- senha;
- chave da API do DataJud, se quiser utilizar as consultas de movimentações.

Depois da configuração, faça login normalmente.

### E depois?

Nas próximas vezes, basta:

**Área de Trabalho → Gestão de Processos → Login**

Não é necessário abrir o Python ou o CMD.

---

## 💾 Onde ficam meus dados?

Os dados da aplicação são mantidos separadamente dos arquivos do programa, na pasta:

**%LOCALAPPDATA%\GestaoProcessos**

A ideia é manter nessa pasta:

- banco de dados SQLite;
- configurações;
- logs;
- backups.

Isso permite que o programa seja atualizado sem substituir os dados do usuário.

> **Importante:** antes de instalar uma atualização importante, é recomendado fazer um backup do banco.

---

## 🔄 Atualizando o sistema

Quando uma nova versão estiver disponível:

1. faça um backup;
2. feche o Gestão de Processos;
3. baixe o novo **GestaoProcessos-Setup.exe**;
4. execute o instalador;
5. abra o sistema novamente.

As migrações do banco são aplicadas automaticamente pela aplicação quando necessário.

---

## 🗄️ Backup

O sistema possui suporte a backup local do banco SQLite.

Para uso cotidiano, mantenha cópias de backup em um local diferente do computador sempre que possível.

O comando técnico de backup está documentado na seção de desenvolvedor.

---

## 🌐 DataJud

O Gestão de Processos pode consultar movimentações processuais através da API Pública do DataJud.

A consulta é feita **quando solicitada pelo usuário**. O sistema não depende de Celery, Redis ou outro serviço de tarefas em segundo plano.

A disponibilidade das informações depende da API do DataJud e da configuração do tribunal correspondente.

---

# 2. 🧑‍💻 Desenvolvedor

Esta seção é para quem vai **programar, testar, corrigir ou gerar novas versões** do projeto.

## 🧰 Tecnologias

| Parte | Tecnologia |
|---|---|
| Backend | Python + Flask |
| Banco | SQLite |
| ORM | Flask-SQLAlchemy |
| Migrações | Flask-Migrate + Alembic |
| Autenticação | Flask-Login |
| Formulários/CSRF | Flask-WTF |
| Templates | Jinja2 |
| Frontend | HTML + CSS |
| API externa | DataJud (CNJ) |
| Testes | unittest |
| Empacotamento | PyInstaller |
| Instalador Windows | Inno Setup 6 |

---

## 📁 Estrutura geral

Principais partes do projeto:

~~~text
gestao-processos/
│
├── app.py
├── requirements.txt
├── requirements-build.txt
├── GestaoProcessos.spec
│
├── config/
├── migrations/
├── processos/
│   ├── models.py
│   ├── routes/
│   ├── services/
│   ├── templates/
│   └── static/
│
├── scripts/
│   └── build_windows.bat
│
├── installer/
│   └── GestaoProcessos.iss
│
└── .github/
    └── workflows/
~~~

---

## 🔧 Preparando o ambiente de desenvolvimento

### 1. Clone o projeto

~~~bash
git clone https://github.com/IJCC06/gestao-processos.git
cd gestao-processos
~~~

Para trabalhar na branch de desenvolvimento:

~~~bash
git checkout desenvolvimento
~~~

### 2. Crie o ambiente virtual

No Windows:

~~~bat
python -m venv venv
~~~

### 3. Ative o ambiente virtual

~~~bat
venv\Scripts\activate
~~~

Quando aparecer **(venv)** no início da linha de comando, o ambiente está ativo.

### 4. Instale as dependências

~~~bat
pip install -r requirements.txt
~~~

---

## ⚙️ Configuração local

Crie um arquivo **.env** na raiz do projeto.

Exemplo:

~~~env
FLASK_SECRET_KEY=uma-chave-secreta-forte
FLASK_DEBUG=True
DATAJUD_API_KEY=sua-chave-do-datajud
~~~

> **Nunca envie o .env para o GitHub.**

---

## ▶️ Executando em desenvolvimento

Com o ambiente virtual ativado:

~~~bat
flask --app app run --debug
~~~

Depois abra no navegador:

~~~text
http://127.0.0.1:5000/
~~~

Para parar o servidor, use **Ctrl + C**.

---

## 🧪 Executando os testes

Com o ambiente virtual ativado:

~~~bat
python -m unittest processos.tests -v
~~~

Antes de enviar alterações, verifique se os testes continuam passando.

---

## 🗃️ Banco de dados e migrações

O projeto utiliza **Flask-Migrate + Alembic**.

### Criar uma migração

Depois de alterar os modelos:

~~~bat
flask --app app db migrate -m "descricao da alteracao"
~~~

### Aplicar migrações

~~~bat
flask --app app db upgrade
~~~

### Ver a versão atual

~~~bat
flask --app app db current
~~~

> Evite alterar o banco manualmente quando a alteração puder ser representada por uma migração.

---

## 💾 Backup para desenvolvimento

Para criar um backup do SQLite:

~~~bat
flask --app app backup-db
~~~

Por padrão, os backups são mantidos localmente.

Também existe o script:

~~~bat
scripts\backup_db.bat
~~~

---

## 🏗️ Gerando o aplicativo Windows

O desenvolvedor precisa ter:

- Python;
- ambiente virtual do projeto;
- Inno Setup 6.

O usuário final **não precisa dessas ferramentas**.

### Gerar o instalador

Na raiz do projeto:

~~~bat
scripts\build_windows.bat
~~~

O processo executa:

~~~text
Código Flask
    ↓
PyInstaller
    ↓
GestaoProcessos.exe
    ↓
Inno Setup 6
    ↓
GestaoProcessos-Setup.exe
~~~

O resultado fica em:

~~~text
installer_output\GestaoProcessos-Setup.exe
~~~

### Teste antes de publicar

Antes de distribuir uma nova versão:

1. instale o Setup.exe;
2. abra o aplicativo;
3. faça a configuração inicial;
4. crie alguns dados de teste;
5. feche e abra novamente;
6. confirme que os dados continuam;
7. teste login e logout;
8. teste DataJud;
9. teste backup;
10. teste migrações.

---

## 📦 Releases

O projeto possui workflow do GitHub Actions para gerar o instalador Windows quando uma tag de versão é publicada.

Exemplo:

~~~bash
git tag v1.0.0
git push origin v1.0.0
~~~

O workflow de release:

1. cria o ambiente de build;
2. instala as dependências;
3. gera o executável com PyInstaller;
4. gera o instalador com Inno Setup;
5. publica o GestaoProcessos-Setup.exe no Release.

> Antes de criar uma Release, teste localmente o instalador.

---

## 🔐 Segurança

O projeto trabalha com dados pessoais e deve ser tratado com cuidado.

- Não versionar .env.
- Não publicar a chave do DataJud.
- Usar uma FLASK_SECRET_KEY forte.
- Manter backups.
- Não compartilhar o banco SQLite publicamente.
- Manter as dependências atualizadas.
- Testar restauração de backups antes de depender deles.

---

# 3. 📌 Fluxo rápido

## Para o usuário

~~~text
Baixar Setup.exe
      ↓
Instalar
      ↓
Abrir atalho
      ↓
Configuração inicial
      ↓
Login
      ↓
Usar o sistema
~~~

## Para o desenvolvedor

~~~text
Git clone
    ↓
Criar venv
    ↓
Instalar requirements
    ↓
Configurar .env
    ↓
Executar Flask
    ↓
Alterar código
    ↓
Executar testes
    ↓
Gerar Setup.exe
    ↓
Testar
    ↓
Publicar Release
~~~

---

## 📝 Estado do projeto

O projeto está em desenvolvimento contínuo. Algumas etapas de empacotamento e distribuição podem exigir validação adicional antes de uma versão ser considerada pronta para uso final.
