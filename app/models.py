# models.py
from datetime import date
from decimal import Decimal
from .database import db

class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    expenses = db.relationship("Expense", back_populates="category", cascade="all, delete-orphan")
    budgets = db.relationship("Budget", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Category {self.name!r}>"

class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    category = db.relationship("Category", back_populates="expenses")

    def __repr__(self) -> str:
        return f"<Expense {self.date} ${self.amount} {self.description!r}>"

class Budget(db.Model):
    __tablename__ = "budgets"
    id = db.Column(db.Integer, primary_key=True)
    # month key stored as YYYY-MM (e.g., '2025-10')
    month_key = db.Column(db.String(7), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    category = db.relationship("Category", back_populates="budgets")

    __table_args__ = (
        db.UniqueConstraint("month_key", "category_id", name="uq_budget_month_category"),
    )

class Income(db.Model):
    __tablename__ = "income"
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    source = db.Column(db.String(120), nullable=False)
