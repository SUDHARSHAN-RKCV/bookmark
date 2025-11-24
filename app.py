from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_login import LoginManager, login_required, current_user
import os
from sqlalchemy import text, inspect  

from helpers import load_excel, prepare_links
from errors import register_error_handlers
from security import register_security_features
from um import handle_login, logout_current_user
from models import db, User, Team, UserTeam



# -----------------------------
# APP SETUP
# -----------------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-in-production")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:passq123@localhost/postgres"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# -----------------------------
# SELF-HEALING DB SCHEMA
# -----------------------------
with app.app_context():

    db.session.execute(text("CREATE SCHEMA IF NOT EXISTS housebox"))
    db.session.commit()

    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names(schema="housebox"))

    expected_tables = {"users", "teams", "user_teams"}

    if not expected_tables.issubset(existing_tables):
        print("[SCHEMA-HEAL] Creating missing tables...")
        db.create_all()

    # Seed initial data
    from seed import seed_users
    seed_users()


# -----------------------------
# LOGIN MANAGER
# -----------------------------
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


# -----------------------------
# ROUTES
# -----------------------------

@app.route("/")
def home():
    try:
        filepath = "data/team_links.xlsx"

        scipher_links = prepare_links(load_excel(filepath, sheets=["scipher"]))
        roc_links = prepare_links(load_excel(filepath, sheets=["roc"]))

        return render_template("index.html", scipher_links=scipher_links, roc_links=roc_links)

    except Exception as e:
        app.logger.error(f"Home Page Error: {e}")
        return "Server Error", 500


@app.route('/admin_panel')
@login_required

def admin_panel():
    """ Admin Dashboard: View all users and teams """
    users = User.query.all()
    teams = Team.query.all()
    return render_template('admin_panel.html', users=users, teams=teams)
@app.route('/create_user', methods=['GET', 'POST'])
@login_required

def create_user():
    # Handle form submit and save user
    pass


@app.route("/edit_user/<int:user_id>", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        user.email = request.form.get("email")
        user.role = request.form.get("role")
        db.session.commit()

        flash("User details updated successfully!", "success")
        return redirect(url_for("admin_panel"))  # 👈 FIX: Must return

    # GET request → show form
    return render_template("edit_user.html", user=user)  # 👈 FIX: Must return


@app.route('/disable_user/<int:user_id>')
@login_required

def disable_user(user_id):
    user = User.query.get(user_id)
    user.is_active = False
    db.session.commit()
    return redirect(url_for('admin_panel'))


@app.route('/enable_user/<int:user_id>')
@login_required

def enable_user(user_id):
    user = User.query.get(user_id)
    user.is_active = True
    db.session.commit()
    return redirect(url_for('admin_panel'))


@app.route('/delete_user/<int:user_id>')
@login_required

def delete_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/team/<team_name>')
@login_required
def team_page(team_name):

    user_teams = [t.lower() for t in current_user.get_team_names()]
    team_name = team_name.lower()

    if team_name not in user_teams:
        return render_template('errors/403.html'), 403

    try:
        data = load_excel("data/team_links.xlsx", sheets=[team_name])
        links = prepare_links(data)
    except Exception:
        links = []

    return render_template("team.html", team=team_name.capitalize(), links=links)


@app.route('/my-team')
@login_required
def my_team():

    teams = current_user.get_team_names()

    if not teams:
        flash("No teams assigned to your account.", "warning")
        return redirect(url_for('home'))

    if len(teams) == 1:
        return redirect(url_for('team_page', team_name=teams[0]))

    return render_template('select_team.html', teams=teams)


@app.route('/login', methods=['GET', 'POST'])
def login():
    return handle_login()


@app.route('/logout')
def logout():
    logout_current_user()
    return redirect(url_for('home'))


# -----------------------------
# ERROR HANDLING & SECURITY
# -----------------------------
register_error_handlers(app)
register_security_features(app)


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
