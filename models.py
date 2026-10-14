# modelos (tabelas) do sistema

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# o init_app é feito no app.py
db = SQLAlchemy()


class Usuario(db.Model):
    """tabela de usuários"""

    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)

    def set_senha(self, senha):
        """guarda só o hash da senha, nunca a senha em texto"""
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        """compara a senha digitada com o hash salvo"""
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        """texto que aparece quando o objeto é impresso"""
        return f'<Usuario {self.id} - {self.username}>'


class Cliente(db.Model):
    """tabela de clientes"""

    __tablename__ = 'cliente'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    # só números (ddd + número), não é obrigatório
    telefone = db.Column(db.String(11), nullable=True)
    # cpf (11) ou cnpj (14), guardado só com números
    cpf_cnpj = db.Column(db.String(14), nullable=False, unique=True)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        """texto que aparece quando o objeto é impresso"""
        return f'<Cliente {self.id} - {self.nome}>'


class Produto(db.Model):
    """tabela de produtos"""

    __tablename__ = 'produto'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    estoque = db.Column(db.Integer, nullable=False, default=0)
    categoria = db.Column(db.String(50), nullable=True)
    descricao = db.Column(db.Text, nullable=True)

    def __repr__(self):
        """texto que aparece quando o objeto é impresso"""
        return f'<Produto {self.id} - {self.nome}>'
