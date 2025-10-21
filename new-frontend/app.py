from datetime import date, datetime
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_app as init_db
from models import Category, Expense, Budget, Income
from functions import (
    all_categories,
    add_expense,
    delete_expense,
    set_budget,
    month_key_from_date,
    monthly_spend_by_category,
    monthly_total_spend,
)

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # set up database / create tables
    init_db(app)

    @app.route("/")
    def index():
        return redirect(url_for("view_report"))

    # ---- Expenses ----
    @app.route("/expenses", methods=["GET", "POST"])
    def expenses():
        if request.method == "POST":
            try:
                amount = Decimal(request.form.get("amount", "0").strip())
                when = datetime.strptime(request.form.get("date"), "%Y-%m-%d").date() if request.form.get("date") else date.today()
                description = request.form.get("description", "").strip()
                category_name = request.form.get("category", "").strip() or None
                add_expense(amount=amount, when=when, description=description, category_name=category_name)
                flash("Expense added.", "success")
            except Exception as e:
                flash(f"Could not add expense: {e}", "error")
            return redirect(url_for("expenses"))

        items = Expense.query.order_by(Expense.date.desc(), Expense.id.desc()).all()
        cats = all_categories()
        return render_template("expenses.html", items=items, categories=cats)

    @app.post("/expenses/<int:expense_id>/delete")
    def expenses_delete(expense_id: int):
        if delete_expense(expense_id):
            flash("Expense deleted.", "success")
        else:
            flash("Expense not found.", "error")
        return redirect(url_for("expenses"))

    # ---- Categories ----
    @app.route("/categories", methods=["GET", "POST"])
    def categories():
        from functions import get_or_create_category  # local import to avoid cycles
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            if not name:
                flash("Category name is required.", "error")
            else:
                get_or_create_category(name)
                flash("Category saved.", "success")
            return redirect(url_for("categories"))
        return render_template("categories.html", categories=all_categories())

    # ---- Budgets ----
    @app.route("/budgets", methods=["GET", "POST"])
    def budgets():
        today = date.today()
        default_key = month_key_from_date(today)
        if request.method == "POST":
            try:
                month_key = (request.form.get("month_key") or default_key).strip()
                amount = Decimal(request.form.get("amount", "0").strip())
                category_name = (request.form.get("category") or "").strip() or None
                set_budget(month_key, amount, category_name)
                flash("Budget saved.", "success")
            except Exception as e:
                flash(f"Could not save budget: {e}", "error")
            return redirect(url_for("budgets"))

        budgets = Budget.query.order_by(Budget.month_key.desc()).all()
        return render_template("budgets.html", budgets=budgets, categories=all_categories(), default_key=default_key)

    # ---- Report ----
    @app.route("/report", methods=["GET", "POST"])
    def view_report():
        today = date.today()
        year = int(request.values.get("year", today.year))
        month = int(request.values.get("month", today.month))
        rows = monthly_spend_by_category(year, month)
        total = monthly_total_spend(year, month)
        return render_template("report.html", year=year, month=month, rows=rows, total=total)

    return app

# For local dev: `python -m consolidated_app.app`
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)