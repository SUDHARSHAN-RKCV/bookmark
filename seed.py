# seed.py
from models import db, User, Team,ALL_TEAMS
from flask import Flask
from sqlalchemy import text
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] =  os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:passq123@localhost/postgres"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# =====================================
# MASTER TEAM LIST
# =====================================



def seed_users():
    with app.app_context():

        print("[SCHEMA-HEAL] Creating missing schema...")
        # SQLAlchemy 2.x compatible schema creation
        with db.engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS housebox"))
            conn.commit()

        print("[SCHEMA-HEAL] Creating missing tables...")
        db.create_all()

        # Users to seed ("email", "role", [teams], "password")
        user_data = [
            ("admin@example.com", "admin", [ "l1_ops","soc","roc","scipher","scipher_vx","scipher_fx","scipher_rx","scipher_soc","scipher_di"], "password123"),
            ("manager@example.com", "manager", [ "l1_ops","roc","soc","scipher","scipher_vx","scipher_fx","scipher_rx","scipher_soc","scipher_di"], "password123"),
            ("sre@example.com", "sre", [ "l1_ops","roc","scipher","soc","scipher_vx","scipher_fx","scipher_rx","scipher_soc","scipher_di"], "password123"),
            ("l1ops@example.com", "l1_ops", ["l1_ops","roc","scipher"], "password123"),
            ("roc@example.com", "roc", ["roc","scipher"], "password123"),
        ]

        for email, role, base_teams, password in user_data:

            # Check if user exists
            user = User.query.filter_by(email=email).first()
            if not user:
                print(f"[SEED] Creating user: {email}")
                user = User(email=email, role=role)
                user.set_password(password)
                db.session.add(user)
                db.session.flush()   # ensures user.id is available

            # --- ROLE BASED TEAM LOGIC ---
            if role == "admin":
                assigned_teams = ALL_TEAMS[:]     # admin gets all teams
            elif role == "manager":
                assigned_teams = [t for t in ALL_TEAMS if t != "admin"]
            else:
                assigned_teams = base_teams        # only the specific teams

            # Assign teams
            for t in assigned_teams:
                user.add_team(t, commit=False)

        db.session.commit()
        print("[SEED] Users + teams seeded successfully!")


if __name__ == "__main__":
    seed_users()
