import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from config import seed_database

from models import db, CaseReport, PhageMatch, Bacteria, Phages, Manufacturers, BacteriaPhages, PhagesManufacturers
from matcher.matcher import Matcher

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)


with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        fasta = request.files["fasta_file"]
        filename = secure_filename(fasta.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        fasta.save(filepath)

        try:
            threshold = float(request.form.get("threshold", 96.2))
        except ValueError:
            threshold = 96.2

        matcher = Matcher(ref_db='data/bacteria_blst/blst', high_prob_threshold=threshold)
        exact, matches = matcher.match(filepath)
        if not matches:
            return render_template(
                "result.html",
                report=None,
                no_match=True,
                uploaded_filename=filename
    )

        top_matches = matches[:4] if matches else []
        main_match = top_matches[0] if top_matches else (None, None)
        additional_matches = top_matches[1:]

        match_id, prob = main_match

        # ✅ Get matched bacteria info
        bacteria = Bacteria.query.filter_by(bacteria_id=match_id).first()
        bacteria_info = {
            "name": bacteria.name if bacteria else "N/A",
            "ncbi_id": bacteria.ncbi_id or "N/A",
            "tax_id": bacteria.tax_id or "N/A"
        }

        # ✅ Main match phages
        phage_links = BacteriaPhages.query.filter_by(bacteria_id=match_id).all()
        phage_info_list = []
        phage_match_objs = []

        for link in phage_links:
            phage = Phages.query.filter_by(phage_id=link.phage_id).first()
            if not phage:
                continue

            manufacturer_data = (
                db.session.query(Manufacturers.name, PhagesManufacturers.price)
                .join(PhagesManufacturers, Manufacturers.manufacturer_id == PhagesManufacturers.manufacturer_id)
                .filter(PhagesManufacturers.phage_id == phage.phage_id)
                .all()
            )

            phage_info_list.append({
                "name": phage.name,
                "ncbi": phage.ncbi_id or "N/A",
                "manufacturers": [
                    {"name": name, "price": f"${price:.2f}"} for name, price in manufacturer_data
                ] if manufacturer_data else [{"name": "None", "price": "N/A"}]
            })

            phage_match_objs.append(PhageMatch(
                phage_name=phage.name,
                effectiveness=prob,
                host_range='Unknown',
                cost='N/A',
                turnaround_time='Unknown',
                insurance_status='Unknown',
                match_type='100%' if exact else 'Partial',
                recommended=exact
            ))

        # ✅ Save CaseReport
        case = CaseReport(
            user_id=1,
            uploaded_file_name=filename,
            specimen_number="N/A",
            genome_length="N/A",
            name=bacteria.name if bacteria else "Unknown",
            gc_content="N/A",
            resistance="Unknown",
            severity="Unknown",
            background="Auto-generated",
            most_effective_phage=phage_info_list[0]["name"] if phage_info_list else "None",
            match_effectiveness=prob,
            match_score=prob,
            matches_100=1 if exact else 0,
            matches_partial=0 if exact else 1,
            pdf_filename=f"{filename}.pdf",
            pdf_path=f"/static/reports/{filename}.pdf",
            created_at=datetime.utcnow()
        )
        db.session.add(case)
        db.session.flush()

        for ph in phage_match_objs:
            ph.case_report_id = case.id
            db.session.add(ph)

        db.session.commit()

        # ➕ Additional Matches
        additional_outputs = []
        for add_match_id, add_prob in additional_matches:
            add_bacteria = Bacteria.query.filter_by(bacteria_id=add_match_id).first()
            if not add_bacteria:
                continue

            add_bacteria_info = {
                "name": add_bacteria.name,
                "ncbi_id": add_bacteria.ncbi_id or "N/A",
                "tax_id": add_bacteria.tax_id or "N/A"
            }

            add_phage_links = BacteriaPhages.query.filter_by(bacteria_id=add_match_id).all()
            add_phage_info_list = []

            for link in add_phage_links:
                phage = Phages.query.filter_by(phage_id=link.phage_id).first()
                if not phage:
                    continue

                manufacturer_data = (
                    db.session.query(Manufacturers.name, PhagesManufacturers.price)
                    .join(PhagesManufacturers, Manufacturers.manufacturer_id == PhagesManufacturers.manufacturer_id)
                    .filter(PhagesManufacturers.phage_id == phage.phage_id)
                    .all()
                )

                add_phage_info_list.append({
                    "name": phage.name,
                    "ncbi": phage.ncbi_id or "N/A",
                    "manufacturers": [
                        {"name": name, "price": f"${price:.2f}"} for name, price in manufacturer_data
                    ] if manufacturer_data else [{"name": "None", "price": "N/A"}]
                })

            additional_outputs.append({
                "match_id": add_match_id,
                "prob": add_prob,
                "bacteria_info": add_bacteria_info,
                "phage_info_list": add_phage_info_list
            })

        return render_template(
            "result.html",
            report=case,
            bacteria_info=bacteria_info,
            phage_info_list=phage_info_list,
            additional_outputs=additional_outputs
        )

    return render_template("home.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0")
