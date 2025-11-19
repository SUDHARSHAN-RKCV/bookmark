# models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, String, UniqueConstraint, ForeignKey
import uuid

db = SQLAlchemy()

# ============================================================
# Team Table
# ============================================================
class Team(db.Model):
    __tablename__ = "teams"
    __table_args__ = {"schema": "housebox"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<Team {self.name}>"


# ============================================================
# UserTeam Mapping Table
# (id, user_id, email, team_name)
# ============================================================
class UserTeam(db.Model):
    __tablename__ = "user_teams"
    __table_args__ = (
        UniqueConstraint("user_id", "team_name", name="uq_user_team"),
        {"schema": "housebox"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("housebox.users.id"), nullable=False)
    email = Column(String(255), nullable=False)
    team_name = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<UserTeam user={self.user_id}, team={self.team_name}>"


# ============================================================
# User Table
# ============================================================
class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = {"schema": "housebox"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Relationship: A user has many user-team entries
    teams = db.relationship("UserTeam", backref="user", lazy="dynamic")

    # --------------------------
    # Constructor
    # --------------------------
    def __init__(self, email, role, password=None):
        self.email = email
        self.role = role
        if password:
            self.set_password(password)

    # --------------------------
    # Password Helpers
    # --------------------------
    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def get_id(self):
        return str(self.id)

    # --------------------------
    # Add team to user
    # --------------------------
    def add_team(self, team_name, commit=True):
        # Ensure the team exists in teams table
        team = Team.query.filter_by(name=team_name).first()
        if not team:
            team = Team(name=team_name)
            db.session.add(team)
            if commit:
                db.session.commit()

        # Check if already mapped
        existing = UserTeam.query.filter_by(
            user_id=self.id,
            team_name=team_name
        ).first()

        if not existing:
            db.session.add(
                UserTeam(
                    user_id=self.id,
                    email=self.email,
                    team_name=team_name
                )
            )

        if commit:
            db.session.commit()

    # --------------------------
    # Helper: return list of team names
    # --------------------------
    def get_team_names(self):
        return [t.team_name for t in self.teams.all()]

    # --------------------------
    # JSON Output
    # --------------------------
    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "role": self.role,
            "teams": self.get_team_names(),
        }
