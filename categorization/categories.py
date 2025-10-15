from app import db, Budget, Expense, app
from sqlalchemy import text
from sqlalchemy.orm import relationship

# define Category class
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

# list of all categories
def all_categories():
    return Category.query.order_by(Category.name.asc()).all()

# create/post a new category
def get_or_create_category(name):

    key = name.strip().lower()
    # check to make sure it's not a blank string
    if not key:
        return None

    c = Category.query.filter_by(name=key).first()

    # check to make sure the category doesn't already exist
    if c:
        return c

    # if it doesn't already exist, create the category
    c = Category(name=key)
    db.session.add(c)
    db.session.commit()
    return c

# categories tab in app to view all categories
@app.route("/categories", methods=["GET", "POST"])
def categories_admin():
    if request.method == "POST":
        name = request.form.get("name", "")
        c = get_or_create_category(name)
        return redirect(url_for("categories_admin"))
    cats = all_categories()
    return render_template_string(
        """
        <h1>Categories</h1>
        <form method="post">
          <input name="name" placeholder="New category">
          <button type="submit">Add</button>
        </form>
        <ul>
          {% for c in cats %}
            <li>{{ c.name }}</li>
          {% endfor %}
        </ul>
        """,
        cats=cats,
    )