from . import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100))
    password_hash = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=False)

    case_reports = db.relationship('CaseReport', back_populates='user', cascade='all, delete-orphan')

