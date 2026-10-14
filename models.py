# models.py
# Define os modelos (tabelas) do SGC usando SQLAlchemy.

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Instância do SQLAlchemy que será inicializada no app.py
db = SQLAlchemy()


class Usuario(db.Model):
    """Representa a tabela 'usuario' no banco de dados."""

    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)

    def set_senha(self, senha):
        """Gera o hash da senha. A senha pura nunca é guardada."""
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        """Compara a senha digitada com o hash salvo no banco."""
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f'<Usuario {self.id} - {self.username}>'


class Cliente(db.Model):
    """Representa a tabela 'cliente' no banco de dados."""

    __tablename__ = 'cliente'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    # Somente números (DDD + número). Campo opcional.
    telefone = db.Column(db.String(11), nullable=True)
    # CPF (11 dígitos) ou CNPJ (14 dígitos), salvo somente com números
    cpf_cnpj = db.Column(db.String(14), nullable=False, unique=True)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<Cliente {self.id} - {self.nome}>'

