
import pytest
from datetime import date
from decimal import Decimal

from flask import Flask
from database import db
from models import Category, Expense, Income, Budget, SavingsGoal, RecurringItem
from functions import (
    # from logic tests
    month_bounds,
    month_key_from_date,
    all_categories,
    get_or_create_category,
    add_expense,
    delete_expense,
    monthly_spend_by_category,
    monthly_total_spend,
    set_budget,
    add_income,
    monthly_total_income,
    monthly_net_flow,
    create_savings_goal,
    get_active_goal,
    goal_progress_for_month,
    _advance_date,
    add_recurring_item,
    update_recurring_item,
    delete_recurring_item,
    _post_single,
    post_due_recurring,
    predicted_totals_for_month,
)


# ==============================
# Fixtures
# ==============================

@pytest.fixture
def app_routes():
    """
    Use the real create_app() so we cover route code in app.py,
    and reset the database to keep tests isolated.
    """
    from app import create_app  # app.py
    app = create_app()
    app.config.update(TESTING=True)

    with app.app_context():
        db.drop_all()
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client_routes(app_routes):
    return app_routes.test_client()


@pytest.fixture
def app_db():
    """
    Minimal Flask app + in-memory DB (sqlite://) for unit tests on helpers.
    This bypasses create_app() so we can test pure DB/logic utilities in isolation.
    """
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()
    ctx.pop()


# ==============================
# Helper for route tests
# ==============================

def login_as_admin(client):
    """Helper: log in with the hard-coded credentials in app.py."""
    return client.post(
        "/login",
        data={"username": "admin", "password": "1234"},
        follow_redirects=True,
    )


# ==============================
# Route tests (from pytest_2.py-style)
# ==============================

def test_index_redirects_to_report(client_routes):
    resp = client_routes.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/report" in resp.headers.get("Location", "")


def test_report_requires_login(client_routes):
    resp = client_routes.get("/report", follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers.get("Location", "")


def test_login_page_get(client_routes):
    resp = client_routes.get("/login")
    assert resp.status_code == 200


def test_invalid_login_stays_on_login_page(client_routes):
    resp = client_routes.post(
        "/login",
        data={"username": "wrong", "password": "bad"},
        follow_redirects=True,
    )
    assert resp.status_code == 200


def test_successful_login_and_access_report(client_routes, app_routes):
    resp = login_as_admin(client_routes)
    assert resp.status_code == 200

    resp2 = client_routes.get("/report")
    assert resp2.status_code == 200

    resp3 = client_routes.get("/login", follow_redirects=False)
    assert resp3.status_code in (301, 302)
    assert "/report" in resp3.headers.get("Location", "")


def test_logout_clears_session_and_protects_report_again(client_routes):
    login_as_admin(client_routes)

    resp = client_routes.get("/report")
    assert resp.status_code == 200

    resp2 = client_routes.get("/logout", follow_redirects=True)
    assert resp2.status_code == 200

    resp3 = client_routes.get("/report", follow_redirects=False)
    assert resp3.status_code in (301, 302)
    assert "/login" in resp3.headers.get("Location", "")


def test_category_create_and_list(client_routes, app_routes):
    login_as_admin(client_routes)

    resp = client_routes.post(
        "/categories",
        data={"name": "Food"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app_routes.app_context():
        cats = Category.query.all()
        assert len(cats) == 1
        assert cats[0].name == "Food"

    resp2 = client_routes.get("/categories")
    assert resp2.status_code == 200


def test_add_and_delete_expense_via_routes(client_routes, app_routes):
    login_as_admin(client_routes)

    with app_routes.app_context():
        get_or_create_category("Food")

    resp = client_routes.post(
        "/expenses",
        data={
            "date": "2025-01-10",
            "amount": "12.50",
            "category": "Food",
            "description": "Lunch",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app_routes.app_context():
        expenses = Expense.query.all()
        assert len(expenses) == 1
        exp_id = expenses[0].id

    resp2 = client_routes.get(f"/expenses/{exp_id}/delete", follow_redirects=True)
    assert resp2.status_code == 200

    with app_routes.app_context():
        assert Expense.query.count() == 0

    resp3 = client_routes.get("/expenses")
    assert resp3.status_code == 200


def test_expenses_requires_login(client_routes):
    resp = client_routes.get("/expenses", follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers.get("Location", "")


def test_add_income_via_route(client_routes, app_routes):
    login_as_admin(client_routes)

    resp = client_routes.post(
        "/income",
        data={
            "date": "2025-01-05",
            "amount": "200.00",
            "source": "Salary",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app_routes.app_context():
        incomes = Income.query.all()
        assert len(incomes) == 1
        assert float(incomes[0].amount) == pytest.approx(200.00)

    resp2 = client_routes.get("/income")
    assert resp2.status_code == 200


def test_budgets_create_category_and_overall(client_routes, app_routes):
    login_as_admin(client_routes)

    with app_routes.app_context():
        food = get_or_create_category("Food")
        food_id = food.id

    resp1 = client_routes.post(
        "/budgets",
        data={
            "month": "2025-01",
            "amount": "100.00",
            "category_id": str(food_id),
        },
        follow_redirects=True,
    )
    assert resp1.status_code == 200

    resp2 = client_routes.post(
        "/budgets",
        data={
            "month": "2025-01",
            "amount": "500.00",
            "category_id": "",
        },
        follow_redirects=True,
    )
    assert resp2.status_code == 200

    with app_routes.app_context():
        budgets = Budget.query.filter_by(month_key="2025-01").all()
        assert len(budgets) == 2

    resp3 = client_routes.get("/budgets")
    assert resp3.status_code == 200


def test_view_report_with_expenses_income_and_budgets(client_routes, app_routes):
    login_as_admin(client_routes)

    with app_routes.app_context():
        food = get_or_create_category("Food")
        add_expense(date(2025, 1, 10), Decimal("20.00"), food, "Groceries")
        add_income(amount=Decimal("200.00"), when=date(2025, 1, 5), source="Salary")

        key = month_key_from_date(date(2025, 1, 1))
        set_budget(key, Decimal("100.00"), food)
        set_budget(key, Decimal("300.00"), None)

    resp = client_routes.get("/report?year=2025&month=1")
    assert resp.status_code == 200


def test_recurring_create_toggle_run_and_task(client_routes, app_routes):
    login_as_admin(client_routes)

    resp = client_routes.get("/recurring")
    assert resp.status_code == 200

    resp2 = client_routes.post(
        "/recurring",
        data={
            "name": "Gym",
            "kind": "expense",
            "amount": "30.00",
            "start_date": "2025-01-01",
            "freq": "monthly",
            "every_n_days": "",
            "day_of_month": "",
            "end_date": "",
            "auto_post": "y",
            "notes": "Membership",
            "category": "Health",
        },
        follow_redirects=True,
    )
    assert resp2.status_code == 200

    with app_routes.app_context():
        items = RecurringItem.query.all()
        assert len(items) == 1
        item_id = items[0].id
        assert items[0].active is True

    resp3 = client_routes.get(f"/recurring/{item_id}/toggle", follow_redirects=True)
    assert resp3.status_code == 200

    with app_routes.app_context():
        refreshed = RecurringItem.query.get(item_id)
        assert refreshed.active is False

    resp4 = client_routes.get(f"/recurring/{item_id}/toggle", follow_redirects=True)
    assert resp4.status_code == 200

    resp5 = client_routes.get(f"/recurring/{item_id}/run", follow_redirects=True)
    assert resp5.status_code == 200

    with app_routes.app_context():
        refreshed = RecurringItem.query.get(item_id)
        assert refreshed.next_run_date > date(2025, 1, 1)
        assert Expense.query.count() == 1

    resp6 = client_routes.get("/tasks/run-recurring", follow_redirects=True)
    assert resp6.status_code == 200


# ==============================
# Logic/DB unit tests (from test.py-style)
# ==============================

def test_month_bounds_and_key():
    start, end = month_bounds(2025, 1)
    assert start == date(2025, 1, 1)
    assert end == date(2025, 1, 31)

    start_dec, end_dec = month_bounds(2025, 12)
    assert start_dec == date(2025, 12, 1)
    assert end_dec == date(2025, 12, 31)

    d = date(2025, 4, 9)
    assert month_key_from_date(d) == "2025-04"


def test_get_or_create_category_idempotent(app_db):
    cat1 = get_or_create_category("Food")
    cat2 = get_or_create_category("  Food  ")
    assert cat1.id == cat2.id

    cats = all_categories()
    assert len(cats) == 1
    assert cats[0].name == "Food"


def test_add_and_delete_expense_and_totals(app_db):
    food = get_or_create_category("Food")
    d1 = date(2025, 1, 10)
    d2 = date(2025, 1, 20)

    add_expense(d1, Decimal("10.50"), food, "Lunch")
    add_expense(d2, Decimal("5.25"), food, "Snack")

    total = monthly_total_spend(2025, 1)
    assert total == pytest.approx(15.75)

    rows = monthly_spend_by_category(2025, 1)
    assert len(rows) == 1
    row = rows[0]
    assert row.category == "Food"
    assert float(row.spent) == pytest.approx(15.75)

    all_expenses = Expense.query.all()
    assert len(all_expenses) == 2
    to_delete_id = all_expenses[0].id
    delete_expense(to_delete_id)

    remaining = Expense.query.all()
    assert len(remaining) == 1

    total_after = monthly_total_spend(2025, 1)
    assert total_after == pytest.approx(float(remaining[0].amount))


def test_delete_expense_nonexistent_is_safe(app_db):
    delete_expense(999)
    assert Expense.query.count() == 0


def test_income_and_net_flow(app_db):
    add_income(amount=Decimal("200.00"), when=date(2025, 1, 5), source="Salary")
    add_income(amount=Decimal("50.00"), when=date(2025, 1, 15), source="Bonus")

    food = get_or_create_category("Food")
    add_expense(date(2025, 1, 6), Decimal("30.00"), food, "Groceries")
    add_expense(date(2025, 1, 7), Decimal("20.00"), food, "Dinner")

    income_total = monthly_total_income(2025, 1)
    spend_total = monthly_total_spend(2025, 1)
    net = monthly_net_flow(2025, 1)

    assert income_total == pytest.approx(250.00)
    assert spend_total == pytest.approx(50.00)
    assert net == pytest.approx(200.00)


def test_monthly_totals_zero_when_no_records(app_db):
    assert monthly_total_spend(2025, 1) == 0.0
    assert monthly_total_income(2025, 1) == 0.0
    assert monthly_net_flow(2025, 1) == 0.0


def test_set_budget_create_and_update(app_db):
    food = get_or_create_category("Food")
    key = "2025-01"

    b1 = set_budget(key, Decimal("100.00"), food)
    assert b1.id is not None
    assert float(b1.amount) == pytest.approx(100.00)

    b2 = set_budget(key, Decimal("150.00"), food)
    assert b1.id == b2.id
    assert float(b2.amount) == pytest.approx(150.00)

    b_overall = set_budget(key, Decimal("500.00"), None)
    assert b_overall.id is not None
    assert float(b_overall.amount) == pytest.approx(500.00)

    budgets = Budget.query.filter_by(month_key=key).all()
    assert len(budgets) == 2


def test_goal_progress_no_goal_returns_defaults(app_db):
    food = get_or_create_category("Food")
    add_expense(date(2025, 1, 6), Decimal("30.00"), food, "Groceries")
    add_income(amount=Decimal("100.00"), when=date(2025, 1, 1), source="Salary")

    progress = goal_progress_for_month(2025, 1)
    assert progress["goal"] is None
    assert progress["current_savings"] == 0.0
    assert progress["target"] == 0.0
    assert progress["percent"] == 0.0
    assert progress["reached"] is False


def test_goal_progress_basic(app_db):
    food = get_or_create_category("Food")
    add_expense(date(2025, 1, 6), Decimal("30.00"), food, "Groceries")
    add_income(amount=Decimal("100.00"), when=date(2025, 1, 1), source="Salary")

    goal = create_savings_goal("Save 100", Decimal("100.00"))

    active = get_active_goal()
    assert active.id == goal.id

    progress = goal_progress_for_month(2025, 1)
    assert progress["goal"].id == goal.id
    assert progress["current_savings"] == pytest.approx(70.00)
    assert progress["target"] == pytest.approx(100.00)
    assert progress["percent"] == pytest.approx(70.0)
    assert progress["reached"] is False


def test_goal_progress_clamps_percent_and_reached(app_db):
    food = get_or_create_category("Food")
    add_expense(date(2025, 1, 6), Decimal("10.00"), food, "Groceries")
    add_income(amount=Decimal("200.00"), when=date(2025, 1, 1), source="Salary")

    create_savings_goal("Save 100", Decimal("100.00"))

    progress = goal_progress_for_month(2025, 1)
    assert progress["percent"] == pytest.approx(100.0)
    assert progress["reached"] is True

    add_expense(date(2025, 1, 7), Decimal("500.00"), food, "Huge expense")
    progress2 = goal_progress_for_month(2025, 1)
    assert progress2["percent"] >= 0.0


def test_advance_date_variants():
    d = date(2025, 1, 1)
    assert _advance_date(d, "weekly", None, None) == date(2025, 1, 8)
    assert _advance_date(d, "biweekly", None, None) == date(2025, 1, 15)
    assert _advance_date(d, "every_n_days", 3, None) == date(2025, 1, 4)

    d_end_jan = date(2025, 1, 31)
    next_month = _advance_date(d_end_jan, "monthly", None, None)
    assert next_month == date(2025, 2, 28)

    d_mid = date(2025, 1, 10)
    next_dom = _advance_date(d_mid, "monthly_dom", None, 15)
    assert next_dom == date(2025, 2, 15)

    d_31 = date(2025, 1, 31)
    feb_dom = _advance_date(d_31, "monthly_dom", None, 31)
    assert feb_dom == date(2025, 2, 28)


def test_add_update_delete_recurring_item(app_db):
    item = add_recurring_item(
        name="Rent",
        kind="expense",
        amount=Decimal("1000.00"),
        category_id=None,
        income_source=None,
        freq="monthly",
        every_n_days=None,
        day_of_month=None,
        start_date=date(2025, 1, 1),
        next_run_date=date(2025, 1, 1),
        end_date=None,
        auto_post=True,
        active=True,
        notes="Test rent",
    )
    assert item.id is not None

    updated = update_recurring_item(item.id, amount=Decimal("1200.00"), active=False)
    assert updated is not None
    assert float(updated.amount) == pytest.approx(1200.00)
    assert updated.active is False

    delete_recurring_item(item.id)
    assert RecurringItem.query.get(item.id) is None


def test_post_single_expense_creates_expense_with_general_category(app_db):
    item = add_recurring_item(
        name="Gym",
        kind="expense",
        amount=Decimal("30.00"),
        category_id=None,
        income_source=None,
        freq="monthly",
        every_n_days=None,
        day_of_month=None,
        start_date=date(2025, 1, 1),
        next_run_date=date(2025, 1, 1),
        end_date=None,
        auto_post=True,
        active=True,
        notes="",
    )

    assert Expense.query.count() == 0
    _post_single(item, when=date(2025, 1, 5))
    expenses = Expense.query.all()
    assert len(expenses) == 1
    e = expenses[0]
    assert float(e.amount) == pytest.approx(30.00)
    assert e.description.startswith("[Recurring] Gym")
    assert e.category.name == "General"


def test_post_single_income_creates_income(app_db):
    item = add_recurring_item(
        name="Salary",
        kind="income",
        amount=Decimal("1000.00"),
        category_id=None,
        income_source="Job",
        freq="monthly",
        every_n_days=None,
        day_of_month=None,
        start_date=date(2025, 1, 1),
        next_run_date=date(2025, 1, 1),
        end_date=None,
        auto_post=True,
        active=True,
        notes="",
    )

    assert Income.query.count() == 0
    _post_single(item, when=date(2025, 1, 31))
    incomes = Income.query.all()
    assert len(incomes) == 1
    inc = incomes[0]
    assert float(inc.amount) == pytest.approx(1000.00)
    assert inc.source == "Job"


def test_post_due_recurring_posts_only_due_auto_active_items(app_db):
    exp_item = add_recurring_item(
        name="Gym",
        kind="expense",
        amount=Decimal("20.00"),
        category_id=None,
        income_source=None,
        freq="monthly",
        every_n_days=None,
        day_of_month=None,
        start_date=date(2025, 1, 1),
        next_run_date=date(2025, 1, 1),
        end_date=None,
        auto_post=True,
        active=True,
        notes="",
    )

    add_recurring_item(
        name="Side job",
        kind="income",
        amount=Decimal("50.00"),
        category_id=None,
        income_source="SideJob",
        freq="monthly",
        every_n_days=None,
        day_of_month=None,
        start_date=date(2025, 1, 1),
        next_run_date=date(2025, 1, 1),
        end_date=None,
        auto_post=False,
        active=True,
        notes="",
    )

    posted = post_due_recurring(today=date(2025, 1, 1))
    assert posted == 1
    assert Expense.query.count() == 1
    assert Income.query.count() == 0

    refreshed = RecurringItem.query.get(exp_item.id)
    assert refreshed.next_run_date > date(2025, 1, 1)


def test_post_due_recurring_respects_end_date_and_deactivates(app_db):
    item = add_recurring_item(
        name="Old subscription",
        kind="expense",
        amount=Decimal("10.00"),
        category_id=None,
        income_source=None,
        freq="monthly",
        every_n_days=None,
        day_of_month=None,
        start_date=date(2024, 1, 1),
        next_run_date=date(2025, 1, 1),
        end_date=date(2024, 12, 31),
        auto_post=True,
        active=True,
        notes="",
    )

    posted = post_due_recurring(today=date(2025, 1, 1))
    assert posted == 0
    refreshed = RecurringItem.query.get(item.id)
    assert refreshed.active is False
    assert Expense.query.count() == 0


def test_predicted_totals_for_month_basic(app_db):
    add_recurring_item(
        name="Rent",
        kind="expense",
        amount=Decimal("100.00"),
        category_id=None,
        income_source=None,
        freq="monthly_dom",
        every_n_days=None,
        day_of_month=1,
        start_date=date(2025, 1, 1),
        next_run_date=date(2025, 1, 1),
        end_date=None,
        auto_post=True,
        active=True,
        notes="",
    )

    add_recurring_item(
        name="Gym",
        kind="expense",
        amount=Decimal("25.00"),
        category_id=None,
        income_source=None,
        freq="weekly",
        every_n_days=None,
        day_of_month=None,
        start_date=date(2025, 1, 7),
        next_run_date=date(2025, 1, 7),
        end_date=None,
        auto_post=True,
        active=True,
        notes="",
    )

    add_recurring_item(
        name="Salary",
        kind="income",
        amount=Decimal("1000.00"),
        category_id=None,
        income_source="Job",
        freq="monthly_dom",
        every_n_days=None,
        day_of_month=15,
        start_date=date(2025, 1, 15),
        next_run_date=date(2025, 1, 15),
        end_date=None,
        auto_post=True,
        active=True,
        notes="",
    )

    totals = predicted_totals_for_month(2025, 1)
    assert totals["predicted_expense"] == pytest.approx(200.00)
    assert totals["predicted_income"] == pytest.approx(1000.00)
