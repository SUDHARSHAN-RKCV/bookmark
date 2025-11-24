# um.py
from flask import request, render_template, flash, redirect, url_for
from flask_login import login_user as flask_login_user, logout_user as flask_logout_user
from werkzeug.security import check_password_hash
from models import User
from errors import InvalidCredentialsError


def handle_login():
    """Handle /login route (GET & POST)."""

    # First load page
    if request.method == 'GET':
        return render_template('login.html')

    # POST login attempt
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    print(f"[DEBUG] POST /login email={email}")

    # Fetch user from DB
    user = User.query.filter_by(email=email).first()

    if not user:
        flash("Invalid email or password", "danger")
        print("[DEBUG] No such user in DB")
        return render_template("login.html")

    # Check password
    if not check_password_hash(user.password_hash, password):
        flash("Invalid email or password", "danger")
        print("[DEBUG] Password mismatch")
        return render_template("login.html")

    print("[DEBUG] Login successful for:", user.email)

    # Login with Flask-Login
    flask_login_user(user)

    flash(f"Welcome back, {user.email}!", "success")

    # Redirect to team page if exists
    team_names = user.get_team_names()
    if team_names:
        return redirect(url_for('home', team_name=team_names[0]))

    return render_template('home.html')
    #return redirect(url_for('home'))


def logout_current_user():
    flask_logout_user()
    return redirect(url_for('home'))
