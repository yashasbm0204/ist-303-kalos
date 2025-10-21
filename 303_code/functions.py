
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func
from database import db
from models import Category, Expense, Budget, Income


def month_bounds(year: int, month: int):
    start = date(year, month, 1)
    if month == 12:
        nxt = date(year + 1, 1, 1)
    else:
        nxt = date(year, month + 1, 1)
    end = nxt - timedelta(days=1)
    return start, end

def month_key_from_date(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"

def all_categories():
    return Category.query.order_by(Category.name).all()

# =========================
# US2: Categorization
# =========================
def get_or_create_category(name: str) -> Category:
    name = (name or "").strip()
    cat = Category.query.filter_by(name=name).first()
    if not cat:
        cat = Category(name=name)
        db.session.add(cat)
        db.session.commit()
    return cat

# =========================
# US1: Expense Tracking
# =========================
def add_expense(when: date, amount: Decimal, category: Category, description: str = "") -> Expense:
    e = Expense(date=when, amount=amount, category=category, description=description)
    db.session.add(e)
    db.session.commit()
    return e

def delete_expense(expense_id: int):
    e = Expense.query.get(expense_id)
    if e:
        db.session.delete(e)
        db.session.commit()

def monthly_spend_by_category(year: int, month: int):
    start, end = month_bounds(year, month)
    rows = (
        db.session.query(
            Category.name.label("category"),
            func.coalesce(func.sum(Expense.amount), 0).label("spent")
        )
        .join(Expense, Expense.category_id == Category.id)
        .filter((Expense.date >= start) & (Expense.date <= end))
        .group_by(Category.name)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )
    return rows

def monthly_total_spend(year: int, month: int) -> float:
    start, end = month_bounds(year, month)
    total = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        (Expense.date >= start) & (Expense.date <= end)
    ).scalar()
    return float(total or 0.0)

# =========================
# US4: Budgeting
# =========================
def set_budget(month_key: str, amount: Decimal, category: Category | None):
    b = Budget.query.filter_by(month_key=month_key, category=category).first()
    if not b:
        b = Budget(month_key=month_key, amount=amount, category=category)
        db.session.add(b)
    else:
        b.amount = amount
    db.session.commit()
    return b

# =========================
# US3: Income Tracking
# =========================
def add_income(amount: Decimal, when: date, source: str = "Other"):
    i = Income(amount=amount, date=when, source=source.strip() or "Other")
    db.session.add(i)
    db.session.commit()
    return i

def monthly_total_income(year: int, month: int) -> float:
    start, end = month_bounds(year, month)
    total = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        (Income.date >= start) & (Income.date <= end)
    ).scalar()
    return float(total or 0.0)

# Net flow ties US3 (income) with US1 (spend)
def monthly_net_flow(year: int, month: int) -> float:
    return monthly_total_income(year, month) - monthly_total_spend(year, month)
