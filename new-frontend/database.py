# database.py
from flask_sqlalchemy import SQLAlchemy

# Single shared SQLAlchemy instance
db = SQLAlchemy()

def init_app(app):
    """Bind the SQLAlchemy instance to the Flask app and create tables."""
    db.init_app(app)
    with app.app_context():
        db.create_all()