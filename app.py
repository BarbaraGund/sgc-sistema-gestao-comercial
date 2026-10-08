# Aplicação Flask do SGC (Sistema de Gestão Comercial).
# Utiliza Flask-SQLAlchemy para persistência em um banco SQLite local.

from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Usuario


app = Flask(__name__)


app.config['SECRET_KEY'] = 'troque-esta-chave-em-producao'


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sgc.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)


with app.app_context():
    db.create_all()


# Controle de acesso
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


# Funções auxiliares
def validar_registro(username, email, senha, confirmar_senha):
    """
    Valida os dados do cadastro de usuário.
    Retorna uma mensagem de erro (string) ou None se estiver tudo certo.
    """
    if not username or not email or not senha or not confirmar_senha:
        return 'Todos os campos são obrigatórios.'

    if len(username) < 3:
        return 'O nome de usuário deve ter pelo menos 3 caracteres.'

    if '@' not in email or '.' not in email.split('@')[-1]:
        return 'Informe um e-mail válido.'

    if len(senha) < 6:
        return 'A senha deve ter pelo menos 6 caracteres.'

    if senha != confirmar_senha:
        return 'As senhas não conferem.'

    return None


# Rotas de autenticação
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


@app.route('/')
@login_required
def index():
    """Exibe a página inicial do sistema (somente usuários autenticados)."""
    return render_template('index.html')


# Execução da aplicação
if __name__ == '__main__':
    app.run(debug=True)
