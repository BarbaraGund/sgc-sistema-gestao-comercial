# SGC - Sistema de Gestão Comercial

Sistema web de gestão comercial desenvolvido em **Flask** e **SQLAlchemy** como projeto acadêmico.
Permite cadastrar usuários, fazer login e gerenciar **clientes** e **produtos** (cadastrar, listar,
buscar, editar e excluir), com interface responsiva em Bootstrap 5.

## Informações do projeto

| | |
|---|---|
| **Aluna** | Bárbara Gund Machado |
| **Turma** | N19 |
| **Início do desenvolvimento** | 08/10/2026 |
| **Tipo** | Projeto acadêmico |

## Funcionalidades

- **Autenticação**: registro de usuários com senha armazenada em hash, login, logout e sessões.
- **Controle de acesso**: todas as páginas do sistema exigem login; ações sem login retornam erro 403.
- **Clientes**: CRUD completo com validação de e-mail, telefone, CPF/CNPJ e bloqueio de duplicidade
  (e-mail e CPF/CNPJ).
- **Produtos**: CRUD completo com validação de preço e estoque (maiores ou iguais a zero).
- **Busca**: filtro por nome nas listagens de clientes e de produtos.
- **Feedback**: mensagens (`flash`) em todas as operações de sucesso e de erro.
- **Páginas de erro** personalizadas (403, 404 e 500).
- **Interface responsiva** com barra de navegação que exibe o nome do usuário logado.

## Tecnologias utilizadas

- Python 3
- Flask 3.0.3
- Flask-SQLAlchemy 3.1.1
- SQLAlchemy 2.0.31
- SQLite (banco de dados local)
- Bootstrap 5.3.3 (via CDN)
- Jinja2 (templates)

## Estrutura do projeto

```
sgc/
├── app.py                  # Rotas, validações e regras da aplicação
├── models.py               # Modelos (tabelas): Usuario, Cliente e Produto
├── requirements.txt        # Dependências do projeto
├── README.md
├── .gitignore
└── templates/
    ├── base.html           # Layout base (Bootstrap, navbar e mensagens flash)
    ├── index.html          # Painel inicial
    ├── login.html
    ├── registro.html
    ├── clientes.html       # Listagem de clientes
    ├── cliente_form.html   # Formulário de cadastro/edição de cliente
    ├── produtos.html       # Listagem de produtos
    ├── produto_form.html   # Formulário de cadastro/edição de produto
    └── erro.html           # Páginas de erro (403, 404 e 500)
```

## Como instalar e executar

### 1. Obter o projeto

```bash
git clone https://github.com/BarbaraGund/sgc-sistema-gestao-comercial.git
cd sgc-sistema-gestao-comercial
```

### 2. Criar e ativar o ambiente virtual

No Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

No Linux/Mac:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Executar a aplicação

```bash
python app.py
```

### 5. Acessar no navegador

```
http://127.0.0.1:5000/
```

O banco de dados SQLite (`sgc.db`) é criado automaticamente na primeira execução, dentro da pasta
`instance/`. No primeiro acesso, clique em **Registrar** para criar um usuário e depois faça login.

### Variável de ambiente (opcional)

A chave que assina a sessão pode ser definida em `SECRET_KEY`. Se não for definida, o projeto usa
uma chave de desenvolvimento, adequada apenas para uso local.

## Rotas disponíveis

Todas as rotas, exceto `/registro` e `/login`, exigem usuário autenticado.

| Método | Rota | Descrição |
|---|---|---|
| GET/POST | `/registro` | Cadastro de usuário (senha com hash) |
| GET/POST | `/login` | Login |
| POST | `/logout` | Logout (limpa a sessão) |
| GET | `/` | Painel com totais de clientes e produtos |
| GET | `/clientes` | Lista de clientes (filtro opcional `?q=nome`) |
| GET/POST | `/cliente/novo` | Cadastro de cliente |
| GET/POST | `/cliente/editar/<id>` | Edição de cliente |
| POST | `/cliente/excluir/<id>` | Exclusão de cliente |
| GET | `/produtos` | Lista de produtos (filtro opcional `?q=nome`) |
| GET/POST | `/produto/novo` | Cadastro de produto |
| GET/POST | `/produto/editar/<id>` | Edição de produto |
| POST | `/produto/excluir/<id>` | Exclusão de produto |

A exclusão só aceita `POST`: o navegador pede confirmação antes de enviar.

## Modelos de dados

**Usuario**: `id`, `username` (único), `email` (único), `senha_hash`

**Cliente**: `id`, `nome`, `email` (único), `telefone` (opcional), `cpf_cnpj` (único),
`data_cadastro`

**Produto**: `id`, `nome`, `preco`, `estoque`, `categoria` (opcional), `descricao` (opcional)

## Regras de validação

- **Usuário**: nome com pelo menos 3 caracteres, e-mail válido, senha com pelo menos 6 caracteres
  e confirmação de senha igual; nome de usuário e e-mail não podem se repetir.
- **Cliente**: nome, e-mail e CPF/CNPJ são obrigatórios; o documento aceita pontos, traços e barra
  na digitação, mas é salvo só com números (11 dígitos para CPF ou 14 para CNPJ); o telefone, se
  informado, deve ter DDD + número (10 ou 11 dígitos); e-mail e CPF/CNPJ não podem se repetir.
- **Produto**: nome obrigatório; preço numérico, maior ou igual a zero e com no máximo 2 casas
  decimais (aceita vírgula ou ponto); estoque inteiro maior ou igual a zero.

## Observações

- O CPF/CNPJ é validado pela quantidade de dígitos, sem conferir os dígitos verificadores.
- Os formulários não possuem proteção CSRF e as listagens não têm paginação; são pontos de melhoria
  para uma versão futura.
- O arquivo `*.db`, a pasta `instance/` e o ambiente virtual `venv/` não são versionados
  (ver `.gitignore`).
