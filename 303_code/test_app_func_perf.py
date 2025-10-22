
import math
import time
from decimal import Decimal
from datetime import date, timedelta

import pytest

from app import create_app
from database import db
from models import Category, Expense, Income
from functions import (
    monthly_spend_by_category,
    monthly_total_spend,
    monthly_total_income,
    monthly_net_flow,
)

@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.testing = True
    return app

@pytest.fixture(autouse=True)
def _db(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    with app.test_client() as c:
        yield c

def seed_basic_month(year=None, month=None):
    if year is None or month is None:
        today = date.today()
        year, month = today.year, today.month

    groceries = Category(name="Groceries")
    rent = Category(name="Rent")
    misc = Category(name="Misc")
    db.session.add_all([groceries, rent, misc])
    db.session.flush()

    day = date(year, month, 15)
    db.session.add_all([
        Expense(date=day, amount=Decimal("25.10"), description="apples", category=groceries),
        Expense(date=day, amount=Decimal("45.55"), description="veggies", category=groceries),
        Expense(date=day, amount=Decimal("1200.00"), description="monthly rent", category=rent),
        Expense(date=day, amount=Decimal("9.90"), description="pen", category=misc),
    ])

    db.session.add_all([
        Income(date=day, amount=Decimal("3000.00"), source="paycheck"),
        Income(date=day, amount=Decimal("200.00"), source="bonus"),
    ])

    db.session.commit()
    return year, month, {"Groceries": Decimal("70.65"), "Rent": Decimal("1200.00"), "Misc": Decimal("9.90")}

def seed_edge_dates(year=None, month=None):
    if year is None or month is None:
        today = date.today()
        year, month = today.year, today.month
    first = date(year, month, 1)
    prev_last = first - timedelta(days=1)
    next_first = (first + timedelta(days=32)).replace(day=1)

    cat = Category(name="EdgeCat")
    db.session.add(cat)
    db.session.flush()

    db.session.add(Expense(date=prev_last, amount=Decimal("11.00"), description="prev", category=cat))
    db.session.add(Expense(date=first, amount=Decimal("22.00"), description="firstday", category=cat))
    db.session.add(Expense(date=first + timedelta(days=10), amount=Decimal("33.00"), description="mid", category=cat))
    db.session.add(Expense(date=next_first, amount=Decimal("44.00"), description="next", category=cat))

    db.session.add(Income(date=prev_last, amount=Decimal("111.00"), source="prev income"))
    db.session.add(Income(date=first, amount=Decimal("222.00"), source="cur income 1"))
    db.session.add(Income(date=first + timedelta(days=10), amount=Decimal("333.00"), source="cur income 2"))
    db.session.add(Income(date=next_first, amount=Decimal("444.00"), source="next income"))

    db.session.commit()
    return year, month

def test_balance_math_correctness(_db):
    y, m, cat_totals = seed_basic_month()
    spend = Decimal(str(monthly_total_spend(y, m)))
    income = Decimal(str(monthly_total_income(y, m)))
    net = Decimal(str(monthly_net_flow(y, m)))
    assert net == income - spend
    by_cat = list(monthly_spend_by_category(y, m))
    summed = sum(Decimal(str(row[1])) for row in by_cat)
    assert summed == spend

def test_date_filtering_in_month_only(_db):
    y, m = seed_edge_dates()
    spend = Decimal(str(monthly_total_spend(y, m)))
    income = Decimal(str(monthly_total_income(y, m)))
    assert spend == Decimal("55.00")
    assert income == Decimal("555.00")

def test_persistence_update_delete_recompute(_db):
    y, m, _ = seed_basic_month()
    base_spend = Decimal(str(monthly_total_spend(y, m)))
    groceries = Category.query.filter_by(name="Groceries").first()
    db.session.add(Expense(date=date(y, m, 20), amount=Decimal("10.00"), description="milk", category=groceries))
    db.session.commit()
    after_add_spend = Decimal(str(monthly_total_spend(y, m)))
    assert after_add_spend == base_spend + Decimal("10.00")
    e = Expense.query.filter_by(description="milk").first()
    db.session.delete(e)
    db.session.commit()
    after_delete_spend = Decimal(str(monthly_total_spend(y, m)))
    assert after_delete_spend == base_spend



@pytest.mark.parametrize("path", ["/report", "/expenses", "/income", "/budgets", "/categories"])
def test_routes_ok_with_empty_db(client, path):
    t0 = time.perf_counter()
    resp = client.get(path)
    elapsed = time.perf_counter() - t0
    assert resp.status_code == 200
    assert elapsed < 0.80, f"{path} too slow on empty DB: {elapsed:.3f}s"

@pytest.mark.parametrize("path", ["/report", "/expenses", "/income", "/budgets", "/categories"])
def test_routes_ok_and_reasonably_fast_with_data(client, _db, path):
    y, m, _ = seed_basic_month()
    groceries = Category.query.filter_by(name="Groceries").first()
    long_text = "x" * 5000
    db.session.add(Expense(date=date(y, m, 22), amount=Decimal("1.00"), description=long_text, category=groceries))
    db.session.commit()
    t0 = time.perf_counter()
    resp = client.get(path)
    elapsed = time.perf_counter() - t0
    assert resp.status_code == 200
    assert elapsed < 1.00, f"{path} too slow with modest data: {elapsed:.3f}s"

def test_report_content_has_totals(client, _db):
    seed_basic_month()
    resp = client.get("/report")
    assert resp.status_code == 200
    assert (b"Total" in resp.data) or (b"total" in resp.data) or (b"Net" in resp.data) or (b"net" in resp.data)

def test_monthly_aggregations_complete_quickly(_db):
    y, m, _ = seed_basic_month()
    groceries = Category.query.filter_by(name="Groceries").first()
    for i in range(200):
        db.session.add(Expense(date=date(y, m, 10), amount=Decimal("1.00"), description=f"bulk{i}", category=groceries))
    for i in range(50):
        db.session.add(Income(date=date(y, m, 10), amount=Decimal("2.00"), source=f"in{i}"))
    db.session.commit()
    t0 = time.perf_counter()
    monthly_spend_by_category(y, m)
    monthly_total_spend(y, m)
    monthly_total_income(y, m)
    monthly_net_flow(y, m)
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.80, f"Monthly aggregations too slow: {elapsed:.3f}s"
