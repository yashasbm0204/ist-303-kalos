
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        from models import Category, Expense, Income, Budget  # noqa
        db.create_all()
