
# US1: Expense Tracking
# US2: Categorization
# US3: Income Tracking
# US4: Budgeting


from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date, datetime
from decimal import Decimal
from database import db, init_db
from models import Category, Expense, Income, Budget
from functions import (
    # US2 helpers
    all_categories, get_or_create_category,
    # US1 helpers
    add_expense, delete_expense,
    # US4 helpers
    set_budget, month_key_from_date,
    # Report helpers (US1/2 aggregates)
    monthly_spend_by_category, monthly_total_spend,
    # US3 helpers + net
    add_income, monthly_total_income, monthly_net_flow
)

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-only-secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    init_db(app)

    @app.route("/")
    def index():
        return redirect(url_for("view_report"))

    # =========================
    # US2: Categorization
    # =========================
    @app.route("/categories", methods=["GET", "POST"])
    def categories():
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            if not name:
                flash("Category name cannot be empty.", "error")
            else:
                get_or_create_category(name)
                flash("Category added (or already exists).", "success")
            return redirect(url_for("categories"))
        return render_template(
            "categories.html",
            items=Category.query.order_by(Category.name).all()
        )

    # =========================
    # US1: Expense Tracking
    # =========================
    @app.route("/expenses", methods=["GET", "POST"])
    def expenses():
        if request.method == "POST":
            try:
                when = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
                amount = Decimal(request.form["amount"])
                category_name = request.form["category"].strip()
                desc = (request.form.get("description") or "").strip()
                cat = get_or_create_category(category_name)
                add_expense(when, amount, cat, desc)
                flash("Expense added.", "success")
            except Exception as e:
                flash(f"Failed to add expense: {e}", "error")
            return redirect(url_for("expenses"))

        items = Expense.query.order_by(Expense.date.desc(), Expense.id.desc()).all()
        return render_template("expenses.html", items=items, categories=all_categories())

    @app.get("/expenses/<int:id>/delete")
    def delete_expense_route(id):
        delete_expense(id)
        flash("Expense deleted.", "success")
        return redirect(url_for("expenses"))

    # =========================
    # US3: Income Tracking
    # =========================
    @app.route("/income", methods=["GET", "POST"])
    def income():
        if request.method == "POST":
            try:
                when = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
                amount = Decimal(request.form["amount"])
                source = (request.form.get("source") or "Other").strip()
                add_income(amount=amount, when=when, source=source)
                flash("Income added.", "success")
            except Exception as e:
                flash(f"Failed to add income: {e}", "error")
            return redirect(url_for("income"))

        items = Income.query.order_by(Income.date.desc(), Income.id.desc()).all()
        return render_template("income.html", items=items)

    # =========================
    # US4: Budgeting
    # =========================
    @app.route("/budgets", methods=["GET", "POST"])
    def budgets():
        if request.method == "POST":
            try:
                # HTML month input like "2025-10"
                month_str = request.form["month"]
                y, m = map(int, month_str.split("-"))
                key = month_key_from_date(date(y, m, 1))
                amount = Decimal(request.form["amount"])
                category_id = request.form.get("category_id") or None
                cat = Category.query.get(int(category_id)) if category_id else None
                set_budget(key, amount, cat)
                flash("Budget saved.", "success")
            except Exception as e:
                flash(f"Failed to save budget: {e}", "error")
            return redirect(url_for("budgets"))

        items = Budget.query.order_by(Budget.month_key.desc()).all()
        return render_template("budgets.html", items=items, categories=all_categories())

    # =========================
    # Report (US1–US4 summary)
    # =========================
    @app.route("/report", methods=["GET"])
    def view_report():
        today = date.today()
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
        rows = monthly_spend_by_category(year, month)      # US1/US2
        total_spend = monthly_total_spend(year, month)     # US1
        total_income = monthly_total_income(year, month)   # US3
        net = monthly_net_flow(year, month)                # US3–US1
        return render_template(
            "report.html",
            year=year, month=month,
            rows=rows,
            total_spend=total_spend,
            total_income=total_income,
            net=net
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
