# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# --- Association table for many-to-many User ↔ Team ---
user_teams = db.Table(
    "user_teams",
    db.Column("user_email", db.String(255), db.ForeignKey("housebox.users.email"), primary_key=True),
    db.Column("team_id", db.Integer, db.ForeignKey("housebox.teams.id"), primary_key=True),
    schema="housebox"
)

class Team(db.Model):
    __tablename__ = "teams"
    __table_args__ = {"schema": "housebox"}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<Team {self.name}>"

class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = {"schema": "housebox"}

    email = db.Column(db.String(255), primary_key=True)
    role = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    teams = db.relationship(
        "Team",
        secondary="housebox.user_teams",
        backref=db.backref("members", lazy="dynamic"),
        lazy="dynamic"
    )

    def __init__(self, email, role, password=None):
        self.email = email
        self.role = role
        if password:
            self.password_hash = generate_password_hash(password)

    @property
    def id(self):
        return self.email

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_team(self, team_name):
        team = Team.query.filter_by(name=team_name).first()
        if not team:
            team = Team(name=team_name)
            db.session.add(team)
        if team not in self.teams:
            self.teams.append(team)
        db.session.commit()

    def get_team_names(self):
        return [t.name for t in self.teams]

    def to_dict(self):
        return {"email": self.email, "role": self.role, "teams": self.get_team_names()}
