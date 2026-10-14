"""
SGC - Sistema de Gestão Comercial (Flask + SQLAlchemy)

Rotas:
  /registro, /login, /logout        autenticação
  /                                 página inicial
  /clientes                         lista (aceita ?q=nome)
  /cliente/novo                     cadastro
  /cliente/editar/<id>              edição
  /cliente/excluir/<id>             exclusão (POST)
  /produtos                         lista (aceita ?q=nome)
  /produto/novo                     cadastro
  /produto/editar/<id>              edição
  /produto/excluir/<id>             exclusão (POST)
Só /registro e /login ficam abertas, o resto exige login.
"""

import os
import re
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Flask, abort, render_template, request, redirect, url_for, session, flash
from models import db, Usuario, Cliente, Produto

# configuração do app
app = Flask(__name__)

# chave usada pela sessão e pelo flash
# (em produção o ideal é usar a variável de ambiente SECRET_KEY)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-de-desenvolvimento-troque-em-producao')

# banco sqlite, o arquivo sgc.db fica na pasta instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sgc.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# liga o sqlalchemy no app
db.init_app(app)

# cria as tabelas se ainda não existirem
with app.app_context():
    db.create_all()


# controle de acesso
def login_required(f):
    """bloqueia quem não está logado: GET manda pro login, POST dá erro 403"""
    @wraps(f)
    def decorada(*args, **kwargs):
        """só roda a rota se tiver usuário na sessão"""
        if 'usuario_id' not in session:
            if request.method != 'GET':
                # tentou fazer uma ação sem estar logado
                abort(403)
            flash('Faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorada


# funções auxiliares
def email_valido(email):
    """confere o formato básico do e-mail (texto@dominio.ext)"""
    return re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email) is not None


def validar_registro(username, email, senha, confirmar_senha):
    """valida o cadastro de usuário, devolve a mensagem de erro ou None"""
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
    """pega os campos do form e tira a pontuação do cpf/cnpj e do telefone"""
    return {
        'nome': request.form.get('nome', '').strip(),
        'email': request.form.get('email', '').strip().lower(),
        'telefone': re.sub(r'[()\-\s]', '', request.form.get('telefone', '')),
        'cpf_cnpj': re.sub(r'[.\-/\s]', '', request.form.get('cpf_cnpj', '')),
    }


def validar_cliente(dados):
    """valida os dados do cliente, devolve a mensagem de erro ou None"""
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
    """vê se já existe outro cliente com o mesmo e-mail ou cpf/cnpj (na edição ignora o próprio)"""
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


def ler_form_produto():
    """pega os campos do form de produto (ainda como texto)"""
    return {
        'nome': request.form.get('nome', '').strip(),
        'preco': request.form.get('preco', '').strip(),
        'estoque': request.form.get('estoque', '').strip(),
        'categoria': request.form.get('categoria', '').strip(),
        'descricao': request.form.get('descricao', '').strip(),
    }


def validar_produto(dados):
    """valida o produto e converte preço e estoque, devolve (erro, valores)"""
    if not dados['nome']:
        return 'O nome do produto é obrigatório.', None

    if len(dados['nome']) > 100:
        return 'O nome deve ter no máximo 100 caracteres.', None

    if len(dados['categoria']) > 50:
        return 'A categoria deve ter no máximo 50 caracteres.', None

    # aceita vírgula ou ponto no preço
    try:
        preco = Decimal(dados['preco'].replace(',', '.'))
    except InvalidOperation:
        return 'Informe um preço válido (ex.: 19,90).', None

    if not preco.is_finite() or preco < 0:
        return 'O preço deve ser um número maior ou igual a zero.', None

    if preco > Decimal('99999999.99'):
        return 'O preço máximo permitido é 99.999.999,99.', None

    if preco != preco.quantize(Decimal('0.01')):
        return 'O preço deve ter no máximo 2 casas decimais.', None

    # estoque tem que ser inteiro e >= 0
    try:
        estoque = int(dados['estoque'])
    except ValueError:
        return 'O estoque deve ser um número inteiro.', None

    if estoque < 0:
        return 'O estoque deve ser maior ou igual a zero.', None

    if estoque > 2147483647:
        return 'O estoque informado é muito grande.', None

    return None, {'preco': preco.quantize(Decimal('0.01')), 'estoque': estoque}


# filtros usados nos templates
@app.template_filter('documento')
def formatar_documento(valor):
    """coloca a pontuação do cpf ou do cnpj"""
    if valor and len(valor) == 11:
        return f'{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}'
    if valor and len(valor) == 14:
        return f'{valor[:2]}.{valor[2:5]}.{valor[5:8]}/{valor[8:12]}-{valor[12:]}'
    return valor or ''


@app.template_filter('moeda')
def formatar_moeda(valor):
    """mostra o valor no formato R$ 1.234,56"""
    texto = f'{valor:,.2f}'
    return 'R$ ' + texto.replace(',', 'X').replace('.', ',').replace('X', '.')


@app.template_filter('telefone')
def formatar_telefone(valor):
    """coloca o telefone no formato (00) 00000-0000"""
    if not valor:
        return '-'
    if len(valor) == 11:
        return f'({valor[:2]}) {valor[2:7]}-{valor[7:]}'
    if len(valor) == 10:
        return f'({valor[:2]}) {valor[2:6]}-{valor[6:]}'
    return valor


# login, registro e logout
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """GET mostra o form, POST cria o usuário (senha com hash)"""
    if 'usuario_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        erro = validar_registro(username, email, senha, confirmar_senha)

        # não deixa repetir username nem e-mail
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
        # salva só o hash
        usuario.set_senha(senha)

        try:
            db.session.add(usuario)
            db.session.commit()
        except Exception:
            # deu erro no banco, desfaz
            db.session.rollback()
            flash('Erro ao cadastrar o usuário. Tente novamente.', 'danger')
            return render_template('registro.html', username=username, email=email)

        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """GET mostra o form, POST confere a senha e cria a sessão"""
    if 'usuario_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        senha = request.form.get('senha', '')

        usuario = Usuario.query.filter_by(username=username).first()

        if usuario and usuario.verificar_senha(senha):
            # limpa qualquer sessão antiga antes de logar
            session.clear()
            session['usuario_id'] = usuario.id
            session['username'] = usuario.username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))

        # mesma mensagem nos dois casos, pra não mostrar se o usuário existe
        flash('Usuário ou senha inválidos.', 'danger')
        return render_template('login.html', username=username)

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    """limpa a sessão e volta para o login"""
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))


# página inicial
@app.route('/')
@login_required
def index():
    """página inicial, mostra o total de clientes e de produtos"""
    return render_template('index.html',
                           total_clientes=Cliente.query.count(),
                           total_produtos=Produto.query.count())


# clientes
@app.route('/clientes')
@login_required
def clientes():
    """lista os clientes, com busca opcional pelo nome (?q=)"""
    # texto digitado na busca
    busca = request.args.get('q', '').strip()

    consulta = Cliente.query
    if busca:
        consulta = consulta.filter(Cliente.nome.icontains(busca, autoescape=True))

    lista = consulta.order_by(Cliente.nome).all()
    return render_template('clientes.html', clientes=lista, busca=busca)


@app.route('/cliente/novo', methods=['GET', 'POST'])
@login_required
def cliente_novo():
    """GET mostra o form, POST valida e salva o cliente"""
    if request.method == 'POST':
        # pega o que foi digitado no form
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
            # deu erro no banco, desfaz
            db.session.rollback()
            flash('Erro ao salvar o cliente. Tente novamente.', 'danger')
            return render_template('cliente_form.html', form=dados, titulo='Novo cliente')

        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('clientes'))

    return render_template('cliente_form.html', form={}, titulo='Novo cliente')


@app.route('/cliente/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def cliente_editar(id):
    """GET carrega o form com os dados, POST valida e atualiza o cliente"""
    cliente = db.get_or_404(Cliente, id)

    if request.method == 'POST':
        # pega o que foi digitado no form
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
            # deu erro no banco, desfaz
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
    """exclui o cliente (só por POST, a confirmação é feita na tela)"""
    cliente = db.get_or_404(Cliente, id)

    try:
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente excluído com sucesso!', 'success')
    except Exception:
        # deu erro no banco, desfaz
        db.session.rollback()
        flash('Erro ao excluir o cliente. Tente novamente.', 'danger')

    return redirect(url_for('clientes'))


# produtos
@app.route('/produtos')
@login_required
def produtos():
    """lista os produtos, com busca opcional pelo nome (?q=)"""
    # texto digitado na busca
    busca = request.args.get('q', '').strip()

    consulta = Produto.query
    if busca:
        consulta = consulta.filter(Produto.nome.icontains(busca, autoescape=True))

    lista = consulta.order_by(Produto.nome).all()
    return render_template('produtos.html', produtos=lista, busca=busca)


@app.route('/produto/novo', methods=['GET', 'POST'])
@login_required
def produto_novo():
    """GET mostra o form, POST valida e salva o produto"""
    if request.method == 'POST':
        # pega o que foi digitado no form
        dados = ler_form_produto()
        erro, valores = validar_produto(dados)

        if erro:
            flash(erro, 'danger')
            return render_template('produto_form.html', form=dados, titulo='Novo produto')

        produto = Produto(
            nome=dados['nome'],
            preco=valores['preco'],
            estoque=valores['estoque'],
            categoria=dados['categoria'] or None,
            descricao=dados['descricao'] or None,
        )

        try:
            db.session.add(produto)
            db.session.commit()
        except Exception:
            # deu erro no banco, desfaz
            db.session.rollback()
            flash('Erro ao salvar o produto. Tente novamente.', 'danger')
            return render_template('produto_form.html', form=dados, titulo='Novo produto')

        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('produtos'))

    return render_template('produto_form.html', form={}, titulo='Novo produto')


@app.route('/produto/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def produto_editar(id):
    """GET carrega o form com os dados, POST valida e atualiza o produto"""
    produto = db.get_or_404(Produto, id)

    if request.method == 'POST':
        # pega o que foi digitado no form
        dados = ler_form_produto()
        erro, valores = validar_produto(dados)

        if erro:
            flash(erro, 'danger')
            return render_template('produto_form.html', form=dados,
                                   titulo='Editar produto', produto_id=id)

        produto.nome = dados['nome']
        produto.preco = valores['preco']
        produto.estoque = valores['estoque']
        produto.categoria = dados['categoria'] or None
        produto.descricao = dados['descricao'] or None

        try:
            db.session.commit()
        except Exception:
            # deu erro no banco, desfaz
            db.session.rollback()
            flash('Erro ao atualizar o produto. Tente novamente.', 'danger')
            return render_template('produto_form.html', form=dados,
                                   titulo='Editar produto', produto_id=id)

        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('produtos'))

    form = {
        'nome': produto.nome,
        'preco': f'{produto.preco:.2f}'.replace('.', ','),
        'estoque': produto.estoque,
        'categoria': produto.categoria,
        'descricao': produto.descricao,
    }
    return render_template('produto_form.html', form=form,
                           titulo='Editar produto', produto_id=id)


@app.route('/produto/excluir/<int:id>', methods=['POST'])
@login_required
def produto_excluir(id):
    """exclui o produto (só por POST, a confirmação é feita na tela)"""
    produto = db.get_or_404(Produto, id)

    try:
        db.session.delete(produto)
        db.session.commit()
        flash('Produto excluído com sucesso!', 'success')
    except Exception:
        # deu erro no banco, desfaz
        db.session.rollback()
        flash('Erro ao excluir o produto. Tente novamente.', 'danger')

    return redirect(url_for('produtos'))


# páginas de erro
@app.errorhandler(404)
def pagina_nao_encontrada(erro):
    """página de erro 404"""
    return render_template(
        'erro.html', codigo=404, titulo='Página não encontrada',
        mensagem='O endereço acessado não existe ou o registro foi removido.'
    ), 404


@app.errorhandler(403)
def acesso_negado(erro):
    """página de erro 403"""
    return render_template(
        'erro.html', codigo=403, titulo='Acesso negado',
        mensagem='Você não tem permissão para realizar esta ação. '
                 'Faça login e tente novamente.'
    ), 403


@app.errorhandler(500)
def erro_interno(erro):
    """página de erro 500, desfaz o que ficou pendente no banco"""
    # deu erro no banco, desfaz
    db.session.rollback()
    return render_template(
        'erro.html', codigo=500, titulo='Erro interno',
        mensagem='Ocorreu um problema inesperado. Tente novamente em instantes.'
    ), 500


# rodar o app
if __name__ == '__main__':
    app.run(debug=True)
