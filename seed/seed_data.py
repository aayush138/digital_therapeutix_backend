import csv
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash
import random

from models import (
    db, User, Bacteria, Phages, Manufacturers,
    BacteriaInteraction, PhageInteraction, BacteriaPhages, PhagesManufacturers,
    CaseReport, PhageMatch
)

# ---------- USER ----------
def create_dummy_user():
    if not User.query.filter_by(email='test@example.com').first():
        user = User(
            email='test@example.com',
            name='Test User',
            password_hash=generate_password_hash('password'),
            is_active=True
        )      
        db.session.add(user)
        db.session.commit()

# ---------- BACTERIA ----------
def load_bacteria_interactions(csv_path):
    print(f"🔄 Loading bacteria from {csv_path}")
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            uuid_ = row.get("uuid")
            if not uuid_:
                continue
            name = row.get("bacteria_name", "Unknown Bacteria")
            ncbi_id = row.get("ncbi_id", "").strip()
            tax_id = row.get("tax_id", "").replace("TAX:", "").strip()
            genbank_id = row.get("genbank_id", "").strip()

            # Insert into Bacteria
            if not Bacteria.query.filter_by(bacteria_id=uuid_).first():
                db.session.add(Bacteria(
                    bacteria_id=uuid_,
                    name=name,
                    ncbi_id=ncbi_id,
                    genbank_id=genbank_id,
                    tax_id=tax_id,
                    description=f"{name} strain"
                ))

            # Insert into BacteriaInteraction
            if not BacteriaInteraction.query.filter_by(bacteria_id=uuid_).first():
                db.session.add(BacteriaInteraction(
                    uuid=str(uuid.uuid4()),
                    bacteria_id=uuid_,
                    no_infection=row.get('no_infection', ''),
                    weak_infection=row.get('weak_infection', ''),
                    strong_infection=row.get('strong_infection', ''),
                    tax_id=tax_id
                ))
    print("✅ Bacteria loaded.")

# ---------- PHAGES ----------
def load_phage_interactions(csv_path):
    print(f"🔄 Loading phages from {csv_path}")
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            uuid_ = row.get("uuid")
            if not uuid_:
                continue
            name = row.get("phage_name", "Unknown Phage")
            ncbi_id = row.get("ncbi_id", "").strip()
            tax_id = row.get("tax_id", "").replace("TAX:", "").strip()
            genbank_id = row.get("genbank_id", "").strip()

            # Insert into Phages
            if not Phages.query.filter_by(phage_id=uuid_).first():
                db.session.add(Phages(
                    phage_id=uuid_,
                    name=name,
                    ncbi_id=ncbi_id,
                    genbank_id=genbank_id,
                    tax_id=tax_id,
                    description=f"{name} phage"
                ))

            # Insert into PhageInteraction
            if not PhageInteraction.query.filter_by(phage_id=uuid_).first():
                db.session.add(PhageInteraction(
                    uuid=str(uuid.uuid4()),
                    phage_id=uuid_,
                    no_infection=row.get('no_infection', ''),
                    weak_infection=row.get('weak_infection', ''),
                    strong_infection=row.get('strong_infection', ''),
                    tax_id=tax_id
                ))
    print("✅ Phages loaded.")

# ---------- LINKS ----------
def link_bacteria_phages():
    print("🔗 Linking Bacteria <-> Phages")
    for b in BacteriaInteraction.query.all():
        for t, raw in {
            "strong": b.strong_infection,
            "weak": b.weak_infection,
            "none": b.no_infection
        }.items():
            if raw:
                for phage_id in raw.split(','):
                    pid = phage_id.strip()
                    if pid:
                        if not BacteriaPhages.query.filter_by(bacteria_id=b.bacteria_id, phage_id=pid).first():
                            db.session.add(BacteriaPhages(
                                bacteria_id=b.bacteria_id,
                                phage_id=pid,
                                infection_type=t
                            ))
    for p in PhageInteraction.query.all():
        for t, raw in {
            "strong": p.strong_infection,
            "weak": p.weak_infection,
            "none": p.no_infection
        }.items():
            if raw:
                for bac_id in raw.split(','):
                    bid = bac_id.strip()
                    if bid:
                        if not BacteriaPhages.query.filter_by(bacteria_id=bid, phage_id=p.phage_id).first():
                            db.session.add(BacteriaPhages(
                                bacteria_id=bid,
                                phage_id=p.phage_id,
                                infection_type=t
                            ))
    print("✅ Links created.")

# ---------- MANUFACTURER ----------
def seed_real_manufacturers():
    print("🔄 Seeding manufacturers...")

    manufacturers_data = [
        {
            "name": "PhageBiotics Research Foundation",
            "type": "Nonprofit",
            "application": "Vet, Clinical",
            "address": "4510 Green Cove Ct NW, Olympia, WA 98502",
            "phone_number": "+1-123-456-789",
            "email": "info@email.com"
        },
        {
            "name": "Phages for Global Health",
            "type": "Nonprofit",
            "application": "Ag, Vet, Clinical",
            "address": "Oakland, CA (exact address not public)",
            "phone_number": "+1-123-456-789",
            "email": "contact@email.com"
        },
        {
            "name": "IPATH (UC San Diego)",
            "type": "Academic",
            "application": "Clinical",
            "address": "9500 Gilman Dr, MC 0866, La Jolla, CA 92093",
            "phone_number": "+1-123-456-789",
            "email": "ipath@email.com"
        },
        {
            "name": "Purdue University (USDA Project)",
            "type": "Academic",
            "application": "Ag, Vet",
            "address": "610 Purdue Mall, West Lafayette, IN 47907",
            "phone_number": "+1-123-456-789",
            "email": "info@email.com"
        },
        {
            "name": "Sentinel Environmental Group",
            "type": "Public/Research",
            "application": "Ag",
            "address": "Based via USDA; likely associated with Purdue/UC system",
            "phone_number": "+1-123-456-789",
            "email": "sentinel@email.com"
        },
        {
            "name": "Creative BioLabs (PhagenBIO)",
            "type": "Private/Contract R&D",
            "application": "Vet",
            "address": "7616 Standish Place, Suite 200, Rockville, MD 20855",
            "phone_number": "+1-123-456-789",
            "email": "phagenbio@email.com"
        },
        {
            "name": "Intralytix, Inc.",
            "type": "Private",
            "application": "Ag, Vet, Clinical",
            "address": "8681 Robert Fulton Dr, Columbia, MD 21046",
            "phone_number": "+1-123-456-789",
            "email": "info@email.com"
        },
        {
            "name": "TAILΦR Labs (Baylor College of Medicine)",
            "type": "Academic",
            "application": "Clinical",
            "address": "One Baylor Plaza, Houston, TX 77030",
            "phone_number": "+1-123-456-789",
            "email": "tailor@email.com"
        },
        {
            "name": "Phagovet / PHAGEVET-P (EU Project)",
            "type": "Public/Intl R&D",
            "application": "Ag, Vet",
            "address": "EU-based; not U.S., but useful models/applications",
            "phone_number": "+1-123-456-789",
            "email": "phagovet@email.com"
        }
    ]

    for m in manufacturers_data:
        if not Manufacturers.query.filter_by(name=m["name"]).first():
            db.session.add(Manufacturers(**m))

    db.session.commit()
    print("✅ Manufacturers seeded.")

# ---------- PHAGE MANUFACTURERS LINK ----------
def link_manufacturers_to_phages():
    print("🔗 Linking manufacturers to phages randomly...")
    all_phages = Phages.query.all()
    all_manufs = Manufacturers.query.all()

    for phage in all_phages:
        selected_manufs = random.sample(all_manufs, k=min(2, len(all_manufs)))
        for m in selected_manufs:
            if not PhagesManufacturers.query.filter_by(phage_id=phage.phage_id, manufacturer_id=m.manufacturer_id).first():
                db.session.add(PhagesManufacturers(
                    phage_id=phage.phage_id,
                    manufacturer_id=m.manufacturer_id,
                    price=round(random.uniform(49.99, 199.99), 2)
                ))

    db.session.commit()
    print("✅ Manufacturers linked to phages.")


# ---------- MAIN ENTRY ----------
def create_dummy_data():
    print("🚀 Starting DB seeding...")
    create_dummy_user()
    load_bacteria_interactions("seed/bacteria_interactions.csv")
    load_phage_interactions("seed/phage_interactions.csv")
    link_bacteria_phages()
    seed_real_manufacturers()
    link_manufacturers_to_phages()
    db.session.commit()
    print("✅ All data seeded successfully.")
