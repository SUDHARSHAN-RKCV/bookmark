# um.py
from flask import request, render_template, flash, redirect, url_for
from flask_login import login_user as flask_login_user, logout_user as flask_logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from errors import InvalidCredentialsError
from models import User

# ✅ Users keyed by EMAIL instead of username
USERS = {
    "admin@example.com": {
        "email": "admin@example.com",
        "role": "admin",
        "team": "l1_ops",   # 👈 new field
        "password": generate_password_hash("password123")
    },
    "manager@example.com": {
        "email": "manager@example.com",
        "role": "manager",
        "team": "operations",   # 👈 new field
        "password": generate_password_hash("secret456")
    },
    "sales@example.com": {
        "email": "sales@example.com",
        "role": "member",
        "team": "sales",
        "password": generate_password_hash("salespass")
    },
}

def login_user(email, password):
    """Authenticate user; return user dict if valid, raise InvalidCredentialsError if not."""
    user = USERS.get(email)
    if user and check_password_hash(user["password"], password):
        return user
    raise InvalidCredentialsError(f"Invalid login attempt for '{email}'")

def handle_login():
    """Handle /login route (GET & POST)."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        print(f"[DEBUG] POST /login email={email}")

        user_data = USERS.get(email)
        if not user_data:
            print("[DEBUG] No user found")
        else:
            print("[DEBUG] Found user:", user_data)

        if not user_data or not check_password_hash(user_data["password"], password):
            print("[DEBUG] Password check failed")
            flash("Invalid email or password", "danger")
            return render_template('login.html')

        print("[DEBUG] Password check passed")

        # ✅ Correct argument order (email, role, team)
        user_obj = User(email, user_data["role"], user_data.get("team"))

        flask_login_user(user_obj)
        print(f"[DEBUG] Login successful for user: {email}, team: {user_data.get('team')}")

        flash(f"Welcome back, {email}!", "success")

        # ✅ Redirect logic
        if user_data.get("team"):
            return redirect(url_for('team_page', team_name=user_data["team"]))
        else:
            return redirect(url_for('home'))

    print("[DEBUG] GET /login")
    return render_template('login.html')

def logout_current_user():
    """Log out current user."""
    flask_logout_user()
    return redirect(url_for('login'))
