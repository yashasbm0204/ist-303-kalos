
from database import db

# US2: Categorization
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    expenses = db.relationship("Expense", back_populates="category")
    budgets = db.relationship("Budget", back_populates="category")

# US1: Expense Tracking
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    category = db.relationship("Category", back_populates="expenses")

# US3: Income Tracking
class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    source = db.Column(db.String(128), default="Other")

# US4: Budgeting
class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # e.g., "2025-10"
    month_key = db.Column(db.String(7), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)

    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    category = db.relationship("Category", back_populates="budgets")

    __table_args__ = (
        db.UniqueConstraint("month_key", "category_id", name="uq_budget_month_category"),
    )
