from models import db, Bacteria, Phages, BacteriaInteraction, PhageInteraction, BacteriaPhages

def get_phages_from_bacteria(bacteria_id):
    """
    Given a bacteria UUID, return all phages that strongly infect it.

    Returns:
        list[dict]: [{phage_id, phage_name, ncbi_id, tax_id}, ...]
    """
    interaction = BacteriaInteraction.query.filter_by(bacteria_id=bacteria_id).first()
    if not interaction or not interaction.strong_infection:
        return []

    phage_ids = [p.strip() for p in interaction.strong_infection.split(',') if p.strip()]
    phages = Phages.query.filter(Phages.phage_id.in_(phage_ids)).all()

    return [
        {
            "phage_id": phage.phage_id,
            "phage_name": phage.name,
            "ncbi_id": phage.ncbi_id,
            "tax_id": phage.tax_id
        }
        for phage in phages
    ]

def get_bacteria_info(bacteria_id):
    """
    Get metadata for a given bacteria UUID.

    Returns:
        dict: {bacteria_name, ncbi_id, tax_id}
    """
    bacteria = Bacteria.query.filter_by(bacteria_id=bacteria_id).first()
    if not bacteria:
        return {"bacteria_name": "N/A", "ncbi_id": "N/A", "tax_id": "N/A"}

    return {
        "bacteria_name": bacteria.name or "N/A",
        "ncbi_id": bacteria.ncbi_id or "N/A",
        "tax_id": bacteria.tax_id or "N/A"
    }

def get_bacteria_from_phage(phage_id):
    """
    Return the first bacteria UUID linked to the given phage.

    Returns:
        str or None
    """
    link = BacteriaPhages.query.filter_by(phage_id=phage_id).first()
    return link.bacteria_id if link else None
