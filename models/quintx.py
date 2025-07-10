from . import db
from datetime import datetime
import uuid as uuid_lib

# ---------------------
# 1. Bacteria & Phages (UUID-based)
# ---------------------
class Bacteria(db.Model):
    __tablename__ = 'bacteria'

    bacteria_id = db.Column(db.String(150), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ncbi_id = db.Column(db.String(100))
    tax_id = db.Column(db.String(50))
    genbank_id = db.Column(db.String(100))
    description = db.Column(db.Text)

    phages = db.relationship('BacteriaPhages', back_populates='bacteria')
    interaction = db.relationship('BacteriaInteraction', uselist=False, back_populates='bacteria')


class Phages(db.Model):
    __tablename__ = 'phages'

    phage_id = db.Column(db.String(150), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ncbi_id = db.Column(db.String(100))
    tax_id = db.Column(db.String(50))
    genbank_id = db.Column(db.String(100))
    description = db.Column(db.Text)

    bacteria = db.relationship('BacteriaPhages', back_populates='phage')
    interaction = db.relationship('PhageInteraction', uselist=False, back_populates='phage')
    manufacturers = db.relationship('PhagesManufacturers', back_populates='phage')

# ---------------------
# 2. Relationships
# ---------------------
class BacteriaPhages(db.Model):
    __tablename__ = 'bacteria_phages'

    bacteria_id = db.Column(db.String(150), db.ForeignKey('bacteria.bacteria_id'), primary_key=True)
    phage_id = db.Column(db.String(150), db.ForeignKey('phages.phage_id'), primary_key=True)
    infection_type = db.Column(db.String(100))

    bacteria = db.relationship('Bacteria', back_populates='phages')
    phage = db.relationship('Phages', back_populates='bacteria')


class PhagesManufacturers(db.Model):
    __tablename__ = 'phages_manufacturers'

    phage_id = db.Column(db.String(150), db.ForeignKey('phages.phage_id'), primary_key=True)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturers.manufacturer_id'), primary_key=True)
    price = db.Column(db.Float)

    phage = db.relationship('Phages', back_populates='manufacturers')
    manufacturer = db.relationship('Manufacturers', back_populates='phages')

# ---------------------
# 3. Manufacturers
# ---------------------
class Manufacturers(db.Model):
    __tablename__ = 'manufacturers'

    manufacturer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))
    application = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(100))

    phages = db.relationship('PhagesManufacturers', back_populates='manufacturer')

# ---------------------
# 4. Interactions
# ---------------------
class BacteriaInteraction(db.Model):
    __tablename__ = 'bacteria_interactions'

    uuid = db.Column(db.String(150), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    bacteria_id = db.Column(db.String(150), db.ForeignKey('bacteria.bacteria_id'), unique=True, nullable=False)
    no_infection = db.Column(db.Text)
    weak_infection = db.Column(db.Text)
    strong_infection = db.Column(db.Text)
    tax_id = db.Column(db.String(100))

    bacteria = db.relationship('Bacteria', back_populates='interaction')


class PhageInteraction(db.Model):
    __tablename__ = 'phage_interactions'

    uuid = db.Column(db.String(150), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    phage_id = db.Column(db.String(150), db.ForeignKey('phages.phage_id'), unique=True, nullable=False)
    no_infection = db.Column(db.Text)
    weak_infection = db.Column(db.Text)
    strong_infection = db.Column(db.Text)
    tax_id = db.Column(db.String(100))

    phage = db.relationship('Phages', back_populates='interaction')

# ---------------------
# 5. Case Reports
# ---------------------
class CaseReport(db.Model):
    __tablename__ = 'case_reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    uploaded_file_name = db.Column(db.String(255))
    specimen_number = db.Column(db.String(50))
    genome_length = db.Column(db.String(50))
    name = db.Column(db.String(255))
    gc_content = db.Column(db.String(50))
    resistance = db.Column(db.String(50))
    severity = db.Column(db.String(50))
    background = db.Column(db.Text)

    most_effective_phage = db.Column(db.String(100))
    match_effectiveness = db.Column(db.Float)
    match_score = db.Column(db.Float)
    matches_100 = db.Column(db.Integer)
    matches_partial = db.Column(db.Integer)

    pdf_filename = db.Column(db.String(255))
    pdf_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='case_reports')
    phage_matches = db.relationship('PhageMatch', back_populates='case_report', cascade='all, delete-orphan')


class PhageMatch(db.Model):
    __tablename__ = 'phage_matches'

    id = db.Column(db.Integer, primary_key=True)
    case_report_id = db.Column(db.Integer, db.ForeignKey('case_reports.id'), nullable=False)

    phage_name = db.Column(db.String(100))
    effectiveness = db.Column(db.Float)
    host_range = db.Column(db.String(100))
    cost = db.Column(db.String(50))
    turnaround_time = db.Column(db.String(50))
    insurance_status = db.Column(db.String(50))
    match_type = db.Column(db.String(50))
    recommended = db.Column(db.Boolean, default=False)

    case_report = db.relationship('CaseReport', back_populates='phage_matches')
