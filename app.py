from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func, UniqueConstraint
from calendar import monthrange 

# --- Configuration and Setup ---
app = Flask(__name__)
# The database file will be created in an 'instance' folder automatically.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'secure_key_for_flash_messages' 
db = SQLAlchemy(app)

# --- Database Models ---

class Limit(db.Model):
    """Stores the single planned total spending limit for a month."""
    id = db.Column(db.Integer, primary_key=True)
    month_year = db.Column(db.String(7), unique=True, nullable=False) # e.g., '2025-09'
    total_limit = db.Column(db.Float, nullable=False)

class Budget(db.Model):
    """Stores the planned monthly budget per category."""
    id = db.Column(db.Integer, primary_key=True)
    month_year = db.Column(db.String(7), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    planned_amount = db.Column(db.Float, nullable=False)

    # Composite key to ensure you only budget once per category per month
    __table_args__ = (
        db.UniqueConstraint('month_year', 'category', name='_month_category_uc'),
    )

class Expense(db.Model):
    """Stores actual logged expenses."""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.String(200), nullable=True)

# Create tables (will run on first launch if the DB file is missing)
with app.app_context():
    db.create_all()

# --- Utility Function: Get All Unique Categories ---

def get_all_categories():
    """Fetches all unique category names ever used across Budgets and Expenses."""
    budget_categories = db.session.query(Budget.category).distinct()
    expense_categories = db.session.query(Expense.category).distinct()
    
    all_categories = set()
    all_categories.update([c[0] for c in budget_categories])
    all_categories.update([c[0] for c in expense_categories])
    
    # Always include some common starters for convenience
    starters = ['Rent', 'Groceries', 'Utilities', 'Fun', 'Transportation', 'Income']
    all_categories.update(starters)
    
    return sorted(list(all_categories))


# --- Utility Function for Report Calculation ---

def calculate_monthly_report(month_year):
    """Calculates all limit and category data for the report view."""
    
    # 1. Define month boundaries
    try:
        start_date = datetime.strptime(month_year, '%Y-%m').date()
        days_in_month = monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(start_date.year, start_date.month, days_in_month).date()
    except ValueError:
        return 0.0, 0.0, {}, []

    # 2. Fetch Global Limit
    monthly_limit_obj = Limit.query.filter_by(month_year=month_year).first()
    planned_limit = monthly_limit_obj.total_limit if monthly_limit_obj else 0.0

    # 3. Calculate Total Actual Spent (for overall limit check)
    total_actual_spent = db.session.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.date >= start_date,
        Expense.date <= end_date
    ).scalar() or 0.0

    # 4. Fetch Category Budgets and Expenses (for breakdown)
    planned_budgets = Budget.query.filter_by(month_year=month_year).all()
    actual_expenses = Expense.query.filter(
        Expense.date >= start_date,
        Expense.date <= end_date
    ).all()
    
    report_data = {}
    all_categories = set()

    # Initialize report_data with planned amounts
    for budget in planned_budgets:
        report_data[budget.category] = {
            'planned': budget.planned_amount,
            'actual': 0.0,
            'variance': budget.planned_amount
        }
        all_categories.add(budget.category)

    # Tally up actual expenses and update variance
    for expense in actual_expenses:
        category = expense.category
        if category not in report_data:
            # Expense in an unplanned category
            report_data[category] = {'planned': 0.0, 'actual': 0.0, 'variance': 0.0}
            
        report_data[category]['actual'] += expense.amount
    
    # Final variance calculation and category listing
    for category, data in report_data.items():
        data['variance'] = data['planned'] - data['actual']
        all_categories.add(category) # Add categories logged but not planned
    
    return planned_limit, total_actual_spent, report_data, sorted(list(all_categories))


# --- Flask Routes ---

@app.route('/')
def index():
    return redirect(url_for('view_report')) 

@app.route('/limit/set', methods=['GET', 'POST'])
def set_limit():
    """Route for setting the single total monthly limit."""
    if request.method == 'POST':
        month_year = request.form.get('month_year')
        limit_amount_str = request.form.get('limit_amount')
        
        try:
            amount = float(limit_amount_str)
            if amount < 0:
                flash('Limit must be a positive number.', 'error')
                return redirect(url_for('set_limit'))

            # Use update or insert pattern
            existing_limit = Limit.query.filter_by(month_year=month_year).first()
            if existing_limit:
                existing_limit.total_limit = amount
            else:
                new_limit = Limit(month_year=month_year, total_limit=amount)
                db.session.add(new_limit)
            
            db.session.commit()
            flash(f'Total spending limit for {month_year} set to ${amount:.2f}!', 'success')
            return redirect(url_for('view_report', month_year=month_year))

        except ValueError:
            flash('Invalid amount entered.', 'error')
            
    current_month = datetime.now().strftime('%Y-%m')
    return render_template('set_limit.html', current_month=current_month)


@app.route('/budget/category', methods=['GET', 'POST'])
def set_category_budget():
    """Route for setting the category-by-category budgets."""
    current_month = datetime.now().strftime('%Y-%m')
    
    # Get all potential categories for the form
    all_categories = get_all_categories()

    if request.method == 'POST':
        month_year = request.form.get('month_year')
        
        # Delete existing budgets for the month to allow for updates/overwrites
        Budget.query.filter_by(month_year=month_year).delete()
        
        saved_count = 0
        
        # Iterate through ALL submitted form items
        for key, value in request.form.items():
            # Skip control fields (like month_year) and empty values
            if key in ['month_year', 'new_category_name'] or not value.strip():
                continue

            category_name = key.strip()
            amount_str = value.strip()
            
            try:
                amount = float(amount_str)
                if amount < 0:
                    flash(f'Amount for {category_name} must be a positive number.', 'error')
                    continue
                
                new_budget = Budget(
                    month_year=month_year, 
                    category=category_name, 
                    planned_amount=amount
                )
                db.session.add(new_budget)
                saved_count += 1
            
            except ValueError:
                flash(f'Invalid amount entered for {category_name}. Use numbers only.', 'error')
                    
        db.session.commit()
        flash(f'Category budget for {month_year} set/updated with {saved_count} categories!', 'success')
        return redirect(url_for('view_report', month_year=month_year))

    # Retrieve existing budget data for pre-filling the form (for GET request)
    existing_budgets = {b.category: b.planned_amount for b in Budget.query.filter_by(month_year=current_month).all()}

    return render_template(
        'set_category_budget.html', 
        current_month=current_month,
        all_categories=all_categories,
        existing_budgets=existing_budgets
    )


@app.route('/expense/log', methods=['GET', 'POST'])
def log_expense():
    """Route for logging actual expenses."""
    
    # Get all categories to populate the dropdown/datalist
    all_categories = get_all_categories()
    
    if request.method == 'POST':
        try:
            date_str = request.form.get('date')
            category = request.form.get('category').strip()
            amount = float(request.form.get('amount'))
            notes = request.form.get('notes')

            if amount <= 0 or not category:
                 flash('Amount must be positive and Category cannot be empty.', 'error')
                 return redirect(url_for('log_expense')) 

            new_expense = Expense(
                date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                category=category,
                amount=amount,
                notes=notes
            )
            db.session.add(new_expense)
            db.session.commit()
            
            flash(f'Expense of ${amount:.2f} for {category} logged successfully!', 'success')
            return redirect(url_for('view_report', month_year=date_str[:7]))
        except Exception as e:
            db.session.rollback() 
            flash(f'An unexpected error occurred: {e}', 'error')
            
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template(
        'log_expense.html', 
        current_date=current_date, 
        categories=all_categories
    )


@app.route('/report')
@app.route('/report/<string:month_year>')
def view_report(month_year=None):
    """The unified report view showing global limit and category breakdown."""
    if month_year is None:
        month_year = datetime.now().strftime('%Y-%m')
    
    planned_limit, total_actual_spent, report_data, categories = calculate_monthly_report(month_year)
    
    remaining_balance = planned_limit - total_actual_spent
    
    # Calculate overall category planned/actual for the table summary
    total_planned_category = sum(data['planned'] for data in report_data.values())
    total_actual_category = sum(data['actual'] for data in report_data.values())
    total_variance_category = total_planned_category - total_actual_category


    return render_template(
        'view_report.html',
        month_year=month_year,
        planned_limit=planned_limit,
        total_actual_spent=total_actual_spent,
        remaining_balance=remaining_balance,
        report_data=report_data,
        categories=categories,
        total_planned_category=total_planned_category,
        total_actual_category=total_actual_category,
        total_variance_category=total_variance_category
    )

# --- Reset Feature ---
@app.route('/reset_data', methods=['POST'])
def reset_data():
    """Drops all tables and recreates them, effectively wiping all data."""
    try:
        db.drop_all()
        db.create_all()
        flash('All spending limits, category budgets, and expenses have been **cleared**! Start fresh.', 'success')
    except Exception as e:
        flash(f'Error resetting data: {e}', 'error')
    
    return redirect(url_for('view_report'))

if __name__ == '__main__':
    app.run(debug=True)
