from flask import Flask, render_template, render_template_string, request, redirect, url_for, flash
from datetime import date, datetime
import sqlite3
from pathlib import Path

APP_DB = Path("finance.sqlite3")

app = Flask(__name__)
app.secret_key = "dev-key"  # for flash messages


# ---------------------- SQLite helpers ----------------------
def get_db():
    conn = sqlite3.connect(APP_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,        -- YYYY-MM-DD
            amount REAL NOT NULL,      -- positive
            category TEXT NOT NULL,
            description TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    # ensure starting_balance exists
    cur.execute("INSERT OR IGNORE INTO settings(key, value) VALUES('starting_balance', '0.0')")
    conn.commit()
    conn.close()

def get_starting_balance():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key='starting_balance'")
    row = cur.fetchone()
    conn.close()
    return round(float(row["value"]) if row and row["value"] else 0.0, 2)

def set_starting_balance(v: float):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE settings SET value=? WHERE key='starting_balance'", (str(round(v, 2)),))
    conn.commit()
    conn.close()

def insert_purchase(d):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO purchases(date, amount, category, description) VALUES(?,?,?,?)",
        (d["date"], d["amount"], d["category"], d["description"]),
    )
    conn.commit()
    conn.close()

def fetch_purchases():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, date, amount, category, description FROM purchases ORDER BY date DESC, id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def totals():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(amount), 0) AS spent FROM purchases")
    spent = float(cur.fetchone()["spent"] or 0.0)
    conn.close()
    total_spent = round(spent, 2)
    current_balance = round(get_starting_balance() - total_spent, 2)
    return total_spent, current_balance


# ---------------------- Template (unchanged UI) ----------------------
# TEMPLATE = 


# ---------------------- Routes ----------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Validate & save a purchase to SQLite
        try:
            raw_date = request.form.get("date") or date.today().isoformat()
            datetime.strptime(raw_date, "%Y-%m-%d")  # validate

            raw_amount = (request.form.get("amount") or "").strip()
            amount = float(raw_amount)
            if amount <= 0:
                raise ValueError("Amount must be positive.")

            category = (request.form.get("category") or "").strip()
            if not category:
                raise ValueError("Category is required.")

            description = (request.form.get("description") or "").strip()

            insert_purchase({
                "date": raw_date,
                "amount": amount,
                "category": category,
                "description": description
            })
            flash("Purchase saved.")
        except ValueError as e:
            flash(f"Error: {e}")
        except Exception:
            flash("Something went wrong while saving the purchase.")
        return redirect(url_for("index"))

    # GET render
    rows = fetch_purchases()
    total_spent, current_balance = totals()

    # convert sqlite rows to simple dot-access objects (optional)
    class Row:
        def __init__(self, r): self.__dict__.update(dict(r))

    return render_template(
        'Expense_Tracking.html',
        purchases=[Row(r) for r in rows],
        total_spent=total_spent,
        current_balance=current_balance,
        starting_balance=get_starting_balance(),
        today=date.today().isoformat(),
        db_path=str(APP_DB.resolve())
    )

@app.post("/set-balance")
def set_balance():
    try:
        sb = float(request.form.get("starting_balance", "0").strip())
        if sb < 0:
            raise ValueError("Starting balance cannot be negative.")
        set_starting_balance(sb)
        flash("Starting balance updated.")
    except ValueError as e:
        flash(f"Error: {e}")
    except Exception:
        flash("Unable to set starting balance.")
    return redirect(url_for("index"))

@app.get("/reset")
def reset():
    """Clear purchases and reset starting balance (persists in SQLite)."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM purchases")
        cur.execute("UPDATE settings SET value='0.0' WHERE key='starting_balance'")
        conn.commit()
        conn.close()
        flash("All data cleared.")
    except Exception:
        flash("Reset failed.")
    return redirect(url_for("index"))


# ---------------------- Bootstrap & run ----------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
