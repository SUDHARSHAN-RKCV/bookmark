from flask import Flask, render_template, redirect, url_for, flash
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

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:passq123@localhost/postgres"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy
db.init_app(app)

# -----------------------------
# SELF-HEALING DB SCHEMA
# -----------------------------
with app.app_context():
    # Ensure schema exists
    db.session.execute(text("CREATE SCHEMA IF NOT EXISTS housebox"))
    db.session.commit()

    # Check and create missing tables
    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names(schema="housebox"))
    expected = {"users", "teams", "user_teams"}

    if not expected.issubset(existing_tables):
        print(f"[SCHEMA-HEAL] Creating missing tables in schema 'housebox'...")
        db.create_all()

    # ✅ Seed default users and teams once
    from seed import seed_users 
    seed_users()  # Safe to call; it only adds missing users

# -----------------------------
# LOGIN MANAGER
# -----------------------------
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    if not user_id:
        return None
    return db.session.get(User, user_id)

# -----------------------------
# ROUTES
# -----------------------------
def exc():
        #@app.route('/')
        #@login_required
        def homes():
            filepath = 'data/team_links.xlsx'

            # If user has multiple teams, just show their first one for now
            user_teams = current_user.get_team_names()
            current_team = user_teams[0] if user_teams else None

            sheets_to_load = ["scipher"]
            if current_team:
                sheets_to_load.insert(0, current_team)

            print(f"[DEBUG] Home: loading sheets {sheets_to_load} for {current_user.email}")
            all_links = load_excel(filepath, sheets=sheets_to_load)
            links = prepare_links(all_links)
            return render_template('index.html', links=links, team=current_team)

@app.route("/")
def home():
    try:
        filepath = "data/team_links.xlsx"

        # FIX: Correct sheet names
        scipher_raw = load_excel(filepath, sheets=["scipher"])
        scipher_links = prepare_links(scipher_raw)

        roc_raw = load_excel(filepath, sheets=["roc"])
        roc_links = prepare_links(roc_raw)

        return render_template(
            "index.html",
            scipher_links=scipher_links,
            roc_links=roc_links
        )

    except Exception as e:
        app.logger.error(f"Home Page Error: {e}")
        return "Internal Server Error", 500


@app.route('/team/<team_name>')
@login_required
def team_page(team_name):
    filepath = "data/team_links.xlsx"
    team_name = team_name.lower()

    # List of teams the logged-in user is part of
    user_teams = [t.lower() for t in current_user.get_team_names()]

    # User is trying to access a team they don't belong to
    if team_name not in user_teams:
        return "Unauthorized or unknown team", 403

    # Try loading this team's sheet
    try:
        data = load_excel(filepath, sheets=[team_name])
        links = prepare_links(data)
    except Exception:
        links = []

    return render_template(
        "team.html",
        team=team_name.capitalize(),
        links=links
    )



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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
