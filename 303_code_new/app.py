# US1: Expense Tracking
# US2: Categorization
# US3: Income Tracking
# US4: Budgeting


from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from datetime import date, datetime
from decimal import Decimal
from database import db, init_db
from models import Category, Expense, Income, Budget, SavingsGoal
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
    add_income, monthly_total_income, monthly_net_flow,
    # US5 helpers
    create_savings_goal, goal_progress_for_month,
    add_recurring_item, update_recurring_item, delete_recurring_item, post_due_recurring, predicted_totals_for_month, _advance_date, _post_single, 
    get_active_goal

)
def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapped_view

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-only-secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    init_db(app)

    VALID_USERNAME = "admin"
    VALID_PASSWORD = "1234"  # login name and password

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("logged_in"):
            return redirect(url_for("view_report"))

        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = (request.form.get("password") or "").strip()

            if username == VALID_USERNAME and password == VALID_PASSWORD:
                session["logged_in"] = True
                session["username"] = username
                flash("Logged in successfully.", "success")
                return redirect(url_for("view_report"))
            else:
                flash("Invalid username or password.", "error")

        return render_template("login.html")

    @app.route("/goals", methods=["GET", "POST"])
    @login_required
    def goals():
        # choose which year/month to look at (default: current)
        today = date.today()
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))

        # Handle form submit: create/update savings goal
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            target_amount_str = request.form.get("target_amount") or "0"

            try:
                target_amount = Decimal(target_amount_str)
                create_savings_goal(name, target_amount)
                flash("Savings goal saved.", "success")
            except Exception as e:
                flash(f"Failed to save savings goal: {e}", "error")

            # redirect so refresh doesn't resubmit the form
            return redirect(url_for("goals", year=year, month=month))

        # For GET: compute progress for this month
        progress = goal_progress_for_month(year, month)

        return render_template(
            "goals.html",
            year=year,
            month=month,
            active_goal=progress["goal"],
            target=progress["target"],
            current_savings=progress["current_savings"],
            percent=progress["percent"],
            reached=progress["reached"],
        )

    
    @app.get("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    @app.route("/")
    def index():
        return redirect(url_for("view_report"))

    # =========================
    # US2: Categorization
    # =========================
    @app.route("/categories", methods=["GET", "POST"])
    @login_required
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
    @login_required
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
    @login_required
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
    @login_required
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
    @login_required
    def view_report():
        today = date.today()
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
    
        # Original query returns a list of Row objects
        rows_from_db = monthly_spend_by_category(year, month)
    
        # Convert to JSON-serializable format
        spend_data = [{"category": row.category, "spent": float(row.spent)} for row in rows_from_db]
    
        total_spend = monthly_total_spend(year, month)
        total_income = monthly_total_income(year, month)
        net = monthly_net_flow(year, month)
    
        # Get recent expenses for activity feed
        recent_expenses = Expense.query.filter(
            db.func.strftime('%Y', Expense.date) == str(year),
            db.func.strftime('%m', Expense.date) == str(month).zfill(2)
        ).order_by(Expense.date.desc()).limit(5).all()
    
        # Get monthly trend data (last 6 months)
        monthly_trends = []
        for i in range(5, -1, -1):
            # Calculate date for i months ago
            if month - i <= 0:
                trend_month = 12 + (month - i)
                trend_year = year - 1
            else:
                trend_month = month - i
                trend_year = year
        
            m_spend = monthly_total_spend(trend_year, trend_month)
            m_income = monthly_total_income(trend_year, trend_month)
            monthly_trends.append({
                "month": date(trend_year, trend_month, 1).strftime("%b %Y"),
                "spend": float(m_spend),
                "income": float(m_income)
            })
    
        # Get budget data for current month
        month_key = month_key_from_date(date(year, month, 1))
        budgets_list = Budget.query.filter_by(month_key=month_key).all()
        budget_data = []
    
        for budget in budgets_list:
            if budget.category_id:
                cat_name = budget.category.name
                # Get actual spending for this category
                cat_spend = sum([float(row["spent"]) for row in spend_data if row["category"] == cat_name], 0)
                budget_data.append({
                    "category": cat_name,
                    "budget": float(budget.amount),
                    "actual": cat_spend
                })
            else:
                # Overall budget
                budget_data.append({
                    "category": "Overall",
                    "budget": float(budget.amount),
                    "actual": float(total_spend)
                })
    
        return render_template(
            "report.html",
            year=year, 
            month=month,
            rows=spend_data,
            total_spend=total_spend,
            total_income=total_income,
            net=net,
            recent_expenses=recent_expenses,
            monthly_trends=monthly_trends,
            budget_data=budget_data
        )

    
    
    # =========================
    # US8: Recurring (subscriptions/bills & paychecks)
    # =========================
    @app.route("/recurring", methods=["GET", "POST"])
    @login_required
    def recurring():
        from models import RecurringItem
        if request.method == "POST":
            try:
                name = (request.form.get("name") or "").strip()
                kind = request.form.get("kind")             # "expense" | "income"
                amount = Decimal(request.form["amount"])
                start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
                freq = request.form.get("freq")
                every_n_days = int(request.form["every_n_days"]) if request.form.get("every_n_days") else None
                day_of_month = int(request.form["day_of_month"]) if request.form.get("day_of_month") else None
                end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date() if request.form.get("end_date") else None
                auto_post = bool(request.form.get("auto_post"))
                notes = (request.form.get("notes") or "").strip()

                # category/income source
                category_id = None
                income_source = None
                if kind == "expense":
                    cat_name = (request.form.get("category") or "General").strip()
                    category_id = get_or_create_category(cat_name).id
                else:
                    income_source = (request.form.get("income_source") or "Recurring").strip()

                add_recurring_item(
                    name=name, kind=kind, amount=amount,
                    category_id=category_id, income_source=income_source,
                    freq=freq, every_n_days=every_n_days, day_of_month=day_of_month,
                    start_date=start_date, next_run_date=start_date,
                    end_date=end_date, auto_post=auto_post, active=True, notes=notes
                )
                flash("Recurring item saved.", "success")
            except Exception as e:
                flash(f"Failed to save recurring item: {e}", "error")
            return redirect(url_for("recurring"))

        items = RecurringItem.query.order_by(RecurringItem.next_run_date.asc()).all()
        return render_template("recurring.html", items=items, categories=all_categories())

    @app.get("/recurring/<int:id>/toggle")
    @login_required
    def recurring_toggle(id):
        from models import RecurringItem
        it = RecurringItem.query.get_or_404(id)
        it.active = not it.active
        db.session.commit()
        flash("Recurring item toggled.", "success")
        return redirect(url_for("recurring"))

    @app.get("/recurring/<int:id>/run")
    @login_required
    def recurring_run_now(id):
        from models import RecurringItem
        it = RecurringItem.query.get_or_404(id)
        _post_single(it, when=it.next_run_date)
        it.next_run_date = _advance_date(it.next_run_date, it.freq, it.every_n_days, it.day_of_month)
        db.session.commit()
        flash("Recurring item posted.", "success")
        return redirect(url_for("recurring"))

    @app.get("/tasks/run-recurring")
    @login_required
    def run_recurring_task():
        count = post_due_recurring()
        flash(f"Posted {count} due recurring items.", "success")
        return redirect(url_for("recurring"))

    

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)


    
