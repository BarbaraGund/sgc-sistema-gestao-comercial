# app.py
# Aplicação Flask do SGC (Sistema de Gestão Comercial).
# Utiliza Flask-SQLAlchemy para persistência em um banco SQLite local.

import re
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Usuario, Cliente

# ---------------------------------------------------------------------------
# Configuração da aplicação
# ---------------------------------------------------------------------------
app = Flask(__name__)

# Chave usada para assinar a sessão e as mensagens flash
app.config['SECRET_KEY'] = 'troque-esta-chave-em-producao'

# Banco de dados SQLite (arquivo sgc.db, criado na pasta instance/)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sgc.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Conecta o SQLAlchemy à aplicação Flask
db.init_app(app)

# Cria as tabelas do banco de dados (caso ainda não existam)
with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
# Controle de acesso
# ---------------------------------------------------------------------------
def login_required(f):
    """
    Decorator que bloqueia o acesso de usuários não autenticados.
    Se não houver usuário na sessão, redireciona para a tela de login.
    """
    @wraps(f)
    def decorada(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorada


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def email_valido(email):
    """Retorna True se o e-mail tem o formato texto@dominio.extensao."""
    return re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email) is not None


def validar_registro(username, email, senha, confirmar_senha):
    """
    Valida os dados do cadastro de usuário.
    Retorna uma mensagem de erro (string) ou None se estiver tudo certo.
    """
    if not username or not email or not senha or not confirmar_senha:
        return 'Todos os campos são obrigatórios.'

    if len(username) < 3:
        return 'O nome de usuário deve ter pelo menos 3 caracteres.'

    if not email_valido(email):
        return 'Informe um e-mail válido.'

    if len(senha) < 6:
        return 'A senha deve ter pelo menos 6 caracteres.'

    if senha != confirmar_senha:
        return 'As senhas não conferem.'

    return None


def ler_form_cliente():
    """
    Lê os campos do formulário de cliente e já remove a formatação:
    o CPF/CNPJ e o telefone são guardados somente com números.
    """
    return {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'telefone': re.sub(r'[()\-\s]', '', request.form.get('telefone', '')),
        'cpf_cnpj': re.sub(r'[.\-/\s]', '', request.form.get('cpf_cnpj', '')),
    }


def validar_cliente(dados):
    """
    Valida os dados do cliente.
    Retorna uma mensagem de erro (string) ou None se estiver tudo certo.
    """
    if not dados['nome'] or not dados['email'] or not dados['cpf_cnpj']:
        return 'Nome, e-mail e CPF/CNPJ são obrigatórios.'

    if len(dados['nome']) > 100:
        return 'O nome deve ter no máximo 100 caracteres.'

    if len(dados['email']) > 100 or not email_valido(dados['email']):
        return 'Informe um e-mail válido.'

    documento = dados['cpf_cnpj']
    if not documento.isdigit() or len(documento) not in (11, 14):
        return 'Informe um CPF (11 números) ou um CNPJ (14 números) válido.'

    telefone = dados['telefone']
    if telefone and (not telefone.isdigit() or len(telefone) not in (10, 11)):
        return 'Telefone inválido. Informe o DDD e o número (10 ou 11 números).'

    return None


def verificar_duplicidade_cliente(dados, ignorar_id=None):
    """
    Verifica se já existe outro cliente com o mesmo e-mail ou CPF/CNPJ.
    Na edição, o próprio cliente é ignorado (ignorar_id).
    Retorna uma mensagem de erro (string) ou None.
    """
    por_email = Cliente.query.filter_by(email=dados['email'])
    por_documento = Cliente.query.filter_by(cpf_cnpj=dados['cpf_cnpj'])

    if ignorar_id is not None:
        por_email = por_email.filter(Cliente.id != ignorar_id)
        por_documento = por_documento.filter(Cliente.id != ignorar_id)

    if por_email.first():
        return 'Já existe um cliente cadastrado com este e-mail.'
    if por_documento.first():
        return 'Já existe um cliente cadastrado com este CPF/CNPJ.'

    return None


# ---------------------------------------------------------------------------
# Filtros de exibição (usados nos templates)
# ---------------------------------------------------------------------------
@app.template_filter('documento')
def formatar_documento(valor):
    """Formata CPF (000.000.000-00) ou CNPJ (00.000.000/0000-00)."""
    if valor and len(valor) == 11:
        return f'{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}'
    if valor and len(valor) == 14:
        return f'{valor[:2]}.{valor[2:5]}.{valor[5:8]}/{valor[8:12]}-{valor[12:]}'
    return valor or ''


@app.template_filter('telefone')
def formatar_telefone(valor):
    """Formata o telefone como (00) 00000-0000 ou (00) 0000-0000."""
    if not valor:
        return '-'
    if len(valor) == 11:
        return f'({valor[:2]}) {valor[2:7]}-{valor[7:]}'
    if len(valor) == 10:
        return f'({valor[:2]}) {valor[2:6]}-{valor[6:]}'
    return valor


# ---------------------------------------------------------------------------
# Rotas de autenticação
# ---------------------------------------------------------------------------
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """
    GET  -> Exibe o formulário de registro.
    POST -> Valida os dados e cria o usuário com a senha em hash.
    """
    if 'usuario_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        erro = validar_registro(username, email, senha, confirmar_senha)

        # Verifica se já existe usuário com o mesmo username ou e-mail
        if not erro:
            existente = Usuario.query.filter(
                (Usuario.username == username) | (Usuario.email == email)
            ).first()
            if existente:
                erro = 'Já existe um usuário com este nome de usuário ou e-mail.'

        if erro:
            flash(erro, 'danger')
            return render_template('registro.html', username=username, email=email)

        usuario = Usuario(username=username, email=email)
        usuario.set_senha(senha)

        try:
            db.session.add(usuario)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Erro ao cadastrar o usuário. Tente novamente.', 'danger')
            return render_template('registro.html', username=username, email=email)

        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  -> Exibe o formulário de login.
    POST -> Confere usuário e senha (hash) e inicia a sessão.
    """
    if 'usuario_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        senha = request.form.get('senha', '')

        usuario = Usuario.query.filter_by(username=username).first()

        if usuario and usuario.verificar_senha(senha):
            session.clear()
            session['usuario_id'] = usuario.id
            session['username'] = usuario.username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))

        # Mesma mensagem para usuário inexistente e senha errada
        flash('Usuário ou senha inválidos.', 'danger')
        return render_template('login.html', username=username)

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    """Limpa a sessão e volta para a tela de login."""
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))


# ---------------------------------------------------------------------------
# Rotas do sistema (protegidas)
# ---------------------------------------------------------------------------
@app.route('/')
@login_required
def index():
    """Exibe a página inicial do sistema (somente usuários autenticados)."""
    return render_template('index.html')


# ---------------------------------------------------------------------------
# Rotas de clientes (protegidas)
# ---------------------------------------------------------------------------
@app.route('/clientes')
@login_required
def clientes():
    """Lista todos os clientes cadastrados em uma tabela."""
    lista = Cliente.query.order_by(Cliente.nome).all()
    return render_template('clientes.html', clientes=lista)


@app.route('/cliente/novo', methods=['GET', 'POST'])
@login_required
def cliente_novo():
    """
    GET  -> Exibe o formulário de cadastro.
    POST -> Valida os dados, verifica duplicidade e salva o novo cliente.
    """
    if request.method == 'POST':
        dados = ler_form_cliente()
        erro = validar_cliente(dados) or verificar_duplicidade_cliente(dados)

        if erro:
            flash(erro, 'danger')
            return render_template('cliente_form.html', form=dados, titulo='Novo cliente')

        cliente = Cliente(
            nome=dados['nome'],
            email=dados['email'],
            telefone=dados['telefone'] or None,
            cpf_cnpj=dados['cpf_cnpj'],
        )

        try:
            db.session.add(cliente)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Erro ao salvar o cliente. Tente novamente.', 'danger')
            return render_template('cliente_form.html', form=dados, titulo='Novo cliente')

        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('clientes'))

    return render_template('cliente_form.html', form={}, titulo='Novo cliente')


@app.route('/cliente/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def cliente_editar(id):
    """
    GET  -> Carrega o formulário preenchido com os dados do cliente.
    POST -> Valida os dados, verifica duplicidade (ignorando o próprio cliente) e atualiza.
    """
    cliente = db.get_or_404(Cliente, id)

    if request.method == 'POST':
        dados = ler_form_cliente()
        erro = validar_cliente(dados) or verificar_duplicidade_cliente(dados, ignorar_id=id)

        if erro:
            flash(erro, 'danger')
            return render_template('cliente_form.html', form=dados,
                                   titulo='Editar cliente', cliente_id=id)

        cliente.nome = dados['nome']
        cliente.email = dados['email']
        cliente.telefone = dados['telefone'] or None
        cliente.cpf_cnpj = dados['cpf_cnpj']

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Erro ao atualizar o cliente. Tente novamente.', 'danger')
            return render_template('cliente_form.html', form=dados,
                                   titulo='Editar cliente', cliente_id=id)

        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('clientes'))

    form = {
        'nome': cliente.nome,
        'email': cliente.email,
        'telefone': cliente.telefone,
        'cpf_cnpj': cliente.cpf_cnpj,
    }
    return render_template('cliente_form.html', form=form,
                           titulo='Editar cliente', cliente_id=id)


@app.route('/cliente/excluir/<int:id>', methods=['POST'])
@login_required
def cliente_excluir(id):
    """Exclui o cliente (somente via POST; a confirmação é feita na tela)."""
    cliente = db.get_or_404(Cliente, id)

    try:
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente excluído com sucesso!', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao excluir o cliente. Tente novamente.', 'danger')

    return redirect(url_for('clientes'))


# ---------------------------------------------------------------------------
# Execução da aplicação
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
