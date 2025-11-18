# seed.py
from models import db, User

def seed_users():
    user_data = [
        ("admin@example.com", "admin", ["l1_ops"], "password123"),
        ("manager@example.com", "manager", ["operations", "sales"], "secret456"),
        ("sales@example.com", "member", ["sales"], "salespass"),
    ]

    for email, role, teams, password in user_data:
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"[SEED] Adding user {email}")
            user = User(email=email, role=role, password=password)
            db.session.add(user)
            db.session.commit()

        for team in teams:
            user.add_team(team)
