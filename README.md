# Personal Finance Management Application

## Team Overview
**Team Members:** Allegra Fass, Yashas Basavaraju Mahesh, Nan Zhao, Adiya King

**Meeting Times**: Saturdays at 3:00pm, Wednesdays at 7:30pm

- [Project Planning and Meeting Notes](https://docs.google.com/document/d/1-j5lCEhB_hAZ8EomZhM-1UHy13lIxFS9l7CUk6FFzxw/edit?usp=sharing)

- [Burndown Chart](https://docs.google.com/spreadsheets/d/1SL-3rzaHygYvE1-G1IVE-6LVpXJd9Rws743BKv5CgmM/edit?usp=sharing)

---

## Application Concept
We are developing a **personal finance management application** that allows users to track their expenses and income, set budgets, and monitor savings goals. The application will provide a clear overview of money-in/money-out and offer visualizations to help users make better financial decisions.

---

## Relevant Stakeholders
- **End users**: individuals who want to log their purchases, income, budgets, and savings targets.  
- **Project developers (our team)**: responsible for designing, coding, and testing the application.  

---

## User Stories

### User Story 1: Expense Tracking
Responsible: **Nan**
- **As a user**, I want to input my purchases and categorize them,  
  so that I can see the total of what I’m spending my money on.  
- **Estimate:** 3–4 hours  
  *(design and implement input form and data storage)*  

### User Story 2: Categorization
Responsible: **Allegra**
- **As a user**, I want to categorize my purchases, so that I can see the total of what I’m spending my money on. 
- **Estimate:** 3–4 hours  
  *(design and implement category options, functionality, and basic reporting dashboard)*  

### User Story 3: Income Tracking
Responsible: **Adiya**
- **As a user**, I want to input my income,  
  so that I can calculate the total money-in/money-out for a given time period.  
- **Estimate:** 2–3 hours  
  *(simple form + calculation logic)*  

### User Story 4: Budgeting
Responsible: **Yashas**
- **As a user**, I want to create a budget,  
  so that I can track my expenses against my planned predictions.  
- **Estimate:** 4–5 hours  
  *(budget creation interface, logic to compare actual vs. planned spending, and reporting)*  

### User Story 5: Savings Goal
Responsible: **Adiya**
- **As a user**, I want to set a savings target for a product or goal,  
  so that I can track my progress toward achieving it.  
- **Estimate:** 3–4 hours  
  *(goal input form, progress bar visualization, and basic notification/alert feature)*  

### User Story 6: Data Visualization
Responsible: **Yashas**
- **As a user**, I want to view charts and summaries of my spending habits, so that I can better understand and adjust my financial behavior.  
- **Estimate:** 4–5 hours  
  *(implement graphs, summary statistics, and filtering options)*  

### User Story 7: App Interface
Responsible: **Allegra**
- **As a user**, I want the app to be engaging and visually appealing. 
- **Estimate:** 1-2 hours  
  *(UI/UX, HTML)*  

### User Story 8: Track Recurring Charges and Subscriptions
Responsible: **Nan**
- **As a user**, I want to input my subscriptions, bills, and income as predicted recurring charges, like RocketMoney. 
- **Estimate:** 4-5 hours  
  *(design and implement interface for inputting recurring charges/deposits and integrate with budget functionality)*

---

## Requirements

- Python 3.10+
- pip / venv
- Packages: `Flask`, `Flask-SQLAlchemy`, `pytest`, `pytest-cov`

Install:

```bash
pip install Flask Flask-SQLAlchemy pytest pytest-cov
```

> Tip: Use a virtual environment (`python -m venv .venv && source .venv/bin/activate`) to keep dependencies isolated.

---

## Quick Start (Run the App)

### Run directly with Python
```bash
python app.py
```
The app starts on `http://127.0.0.1:5000/` with a local SQLite database (e.g., `site.db`).


### Login
Open `http://127.0.0.1:5000/login` and sign in:

- **Username:** `admin`
- **Password:** `1234`

---

## Project Structure

- **`app.py`** – Flask app factory and routes for `/categories`, `/expenses`, `/income`, `/budgets`, `/report`, `/recurring`, plus login/logout and `login_required` protection.
- **`database.py`** – SQLAlchemy database setup.
- **`models.py`** – ORM models: `Category`, `Expense`, `Income`, `Budget`, `SavingsGoal`, `RecurringItem`.
- **`functions.py`** – Business logic: add/delete items, monthly totals, budgets, savings goal progress, and recurring scheduling/posting.
- **`code_test.py`** – Pytest suite that exercises both helper functions and Flask routes (you can add more tests here).

---

## How to Test

Run test file:
```bash
pytest code_test.py -q
```

---

## Test Coverage (pytest-cov)

Show coverage for the main modules **and** list uncovered lines:
```bash
pytest code_test.py   --cov=.  --cov-report=term-missing
```

Generate a clickable HTML coverage report:
```bash
pytest code_test.py --cov=. --cov-report=html
open htmlcov/index.html   # Windows: start htmlcov/index.html
```

## The Three most important things we learned about Software development
- Environment isolation critical for dependency management

- Regular git operations prevent repository state conflicts

- API contract validation ensures frontend-backend compatibility

- Cross-platform testing identifies environment-specific issues early

