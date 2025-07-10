from flask import Flask
from models import db
from seed.seed_data import create_dummy_data, load_bacteria_interactions, load_phage_interactions

def seed_database(app):
    with app.app_context():
        db.drop_all()
        db.create_all()

        create_dummy_data()

        db.session.commit()
        print("✅ Seed data loaded!")