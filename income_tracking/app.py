import os
from decimal import Decimal
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Income

def create_app():
    app = Flask(__name__)
    # Minimal config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")  # for flash messages
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    @app.route("/", methods=["GET"])
    def income_form():
        # Render the form page
        return render_template("income_form.html", today=date.today().isoformat())

    @app.route("/save-income", methods=["POST"])
    def save_income():
        # Read form fields
        amount_raw = request.form.get("amount", "").strip()
        date_str   = request.form.get("date", "").strip() or date.today().isoformat()
        source     = (request.form.get("source") or "").strip()

        # Validate & coerce
        try:
            amount = Decimal(amount_raw)
            if amount <= 0:
                raise ValueError("Amount must be > 0")
            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
            if not source:
                raise ValueError("Source is required")
        except Exception as e:
            flash(f"Invalid input: {e}", "error")
            return redirect(url_for("income_form"))

        # Save to DB
        inc = Income(amount=amount, date=dt, source=source)
        db.session.add(inc)
        db.session.commit()

        flash("Income saved ✅", "success")
        return redirect(url_for("income_form"))

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()  # creates the 'income' table if it doesn't exist
    app.run(debug=True)
