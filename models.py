# Define os modelos do SGC usando SQLAlchemy.

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

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
