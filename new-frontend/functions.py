from datetime import date
from calendar import monthrange
from sqlalchemy import func
from database import db
from models import Category, Expense, Budget

# ---- Category helpers ----
def all_categories():
    return Category.query.order_by(Category.name.asc()).all()

def get_or_create_category(name: str) -> Category:
    name = (name or "").strip()
    if not name:
        return None
    existing = Category.query.filter(func.lower(Category.name) == name.lower()).first()
    if existing:
        return existing
    c = Category(name=name)
    db.session.add(c)
    db.session.commit()
    return c

# ---- Expense helpers ----
def add_expense(amount, when: date, description: str = "", category_name: str | None = None):
    category = get_or_create_category(category_name) if category_name else None
    e = Expense(amount=amount, date=when, description=description, category=category)
    db.session.add(e)
    db.session.commit()
    return e

def delete_expense(expense_id: int) -> bool:
    e = Expense.query.get(expense_id)
    if not e:
        return False
    db.session.delete(e)
    db.session.commit()
    return True

# ---- Budget helpers ----
def set_budget(month_key: str, amount, category_name: str | None = None):
    category = get_or_create_category(category_name) if category_name else None
    q = Budget.query.filter_by(month_key=month_key, category=category)
    b = q.first()
    if b is None:
        b = Budget(month_key=month_key, amount=amount, category=category)
        db.session.add(b)
    else:
        b.amount = amount
    db.session.commit()
    return b

def month_key_from_date(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"

# ---- Reporting ----
def month_bounds(year: int, month: int) -> tuple[date, date]:
    days = monthrange(year, month)[1]
    start = date(year, month, 1)
    end = date(year, month, days)
    return start, end

def monthly_spend_by_category(year: int, month: int):
    start, end = month_bounds(year, month)
    rows = (
        db.session.query(
            Category.name.label("category"),
            func.coalesce(func.sum(Expense.amount), 0).label("spent"),
        )
        .outerjoin(Expense, Expense.category_id == Category.id)
        .filter((Expense.date >= start) & (Expense.date <= end))
        .group_by(Category.name)
        .order_by(Category.name.asc())
        .all()
    )
    # Include uncategorized
    uncategorized_spent = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter((Expense.category_id.is_(None)) & (Expense.date >= start) & (Expense.date <= end))
        .scalar()
    )
    results = [{"category": r.category, "spent": float(r.spent)} for r in rows]
    if uncategorized_spent:
        results.append({"category": "(Uncategorized)", "spent": float(uncategorized_spent)})
    return results

def monthly_total_spend(year: int, month: int) -> float:
    start, end = month_bounds(year, month)
    total = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        (Expense.date >= start) & (Expense.date <= end)
    ).scalar()
    return float(total or 0.0)