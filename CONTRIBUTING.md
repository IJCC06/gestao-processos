# Contribuindo

Obrigado pelo interesse no Gestão de Processos.

## Fluxo de desenvolvimento

1. Crie uma branch para a alteração.
2. Faça a implementação de forma pequena e objetiva.
3. Atualize os testes quando a alteração afetar uma funcionalidade existente ou adicionar uma funcionalidade importante.
4. Atualize o README ou a documentação quando necessário.
5. Execute a suíte completa:

```bat
venv\Scripts\python.exe -m unittest discover -v
```

6. Antes de abrir um Pull Request, confirme que não há arquivos locais, credenciais, bancos ou logs no commit.

## Commits

Prefira mensagens de commit claras e específicas, por exemplo:

- `Adiciona validação de número CNJ`
- `Corrige consulta de movimentações DataJud`
- `Atualiza documentação de instalação`

## Pull Requests

Descreva:

- o que foi alterado;
- por que a alteração foi necessária;
- como foi testada;
- eventuais limitações ou impactos.

Alterações que envolvam banco de dados devem incluir a migração correspondente.

## Dados sensíveis

Nunca envie para o repositório:

- arquivos `.env`;
- chaves de API;
- bancos de dados reais;
- backups reais;
- logs que contenham dados pessoais;
- credenciais.

