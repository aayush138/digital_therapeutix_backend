from flask import Flask
from models import db, User
from seed.seed_data import create_dummy_data

def seed_database(app):
    with app.app_context():
        db.create_all()
        # Check if the User table is empty (or any other main table)
        if not User.query.first():
            create_dummy_data()
            db.session.commit()
            print("✅ Seed data loaded!")
        else:
            print("✅ Database already seeded, skipping seeding.")