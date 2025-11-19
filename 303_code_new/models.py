
from database import db
from datetime import date

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

# US5: Savings Goal
class SavingsGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    target_amount = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.Date, nullable=False, default=date.today)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


# US8: Recurring Items
class RecurringItem(db.Model):
    __tablename__ = "recurring_items"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(120), nullable=False)
    # "expense" or "income"
    kind = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)

    # For expenses we link a Category; for income we store a free-text source
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    category = db.relationship("Category")
    income_source = db.Column(db.String(120), nullable=True)

    # Frequency
    freq = db.Column(db.String(20), nullable=False, default="monthly")
    every_n_days = db.Column(db.Integer, nullable=True)   # when freq="every_n_days"
    day_of_month = db.Column(db.Integer, nullable=True)   # when freq="monthly_dom" (1..28)

    start_date = db.Column(db.Date, nullable=False)
    next_run_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)

    auto_post = db.Column(db.Boolean, nullable=False, default=True)
    active = db.Column(db.Boolean, nullable=False, default=True)

    notes = db.Column(db.String(280), nullable=True)
