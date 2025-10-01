from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Income(db.Model):
    __tablename__ = "income"
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    source = db.Column(db.String(120), nullable=False)
