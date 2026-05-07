"""
Production data pool containing realistic transaction scenarios
based on San Francisco Open Data schemas (Procurement & Purchasing).
Used to demonstrate "Real-World" data processing capability.
"""

SF_DEPARTMENTS = [
    "DPH: Public Health",
    "SFMTA: Municipal Transportation",
    "DPW: Public Works",
    "AIR: San Francisco Airport",
    "PUC: Public Utilities Commission",
    "REC: Recreation & Parks",
    "POL: Police Department",
    "FIR: Fire Department",
    "LIB: Public Library",
    "ADM: Administrative Services",
    "HSA: Human Services Agency",
    "CCT: Community College District",
]

SF_VENDORS = [
    # Technology & Services
    "IBM Corporation", "Microsoft Services", "Oracle America Inc",
    "Cisco Systems", "CDW Government LLC", "Accenture LLP",
    # Infrastructure & Construction
    "Granite Construction Co", "Webcor Construction LP", "Swinerton Builders",
    "AECOM Technical Services", "Bechtel Infrastructure",
    # Supplies & Maintenance
    "Grainger Industrial Supply", "Fastenal Company", "Home Depot USA Inc",
    "Graybar Electric Co", "United Rentals", "Sunbelt Rentals Inc",
    # Medical & Health
    "McKesson Medical-Surgical Inc", "Cardinal Health 200 LLC", "Medline Industries",
    "LabCorp of America", "Quest Diagnostics Inc",
    # Transit & Specialized
    "New Flyer of America", "Siemens Industry Inc", "Bombardier Transportation",
]

# High-fidelity real-world scenarios
SF_REAL_SCENARIOS = [
    # Normal/Routine
    {"vendor": "Grainger Industrial Supply", "desc": "Filter replacement for HVAC systems", "dept": "PUC: Public Utilities Commission", "ptype": "Invoice", "holder": "System", "min_amt": 450, "max_amt": 3500},
    {"vendor": "Oracle America Inc", "desc": "Database support renewal - Annual", "dept": "ADM: Administrative Services", "ptype": "Invoice", "holder": "System", "min_amt": 15000, "max_amt": 45000},
    {"vendor": "Granite Construction Co", "desc": "Emergency road surfacing - Sector 4", "dept": "DPW: Public Works", "ptype": "Invoice", "holder": "System", "min_amt": 2500, "max_amt": 8000},
    {"vendor": "McKesson Medical-Surgical Inc", "desc": "Medical supply restock - Ward C", "dept": "DPH: Public Health", "ptype": "Invoice", "holder": "System", "min_amt": 1200, "max_amt": 6000},
    {"vendor": "Siemens Industry Inc", "desc": "Signaling equipment maintenance", "dept": "SFMTA: Municipal Transportation", "ptype": "Invoice", "holder": "System", "min_amt": 3500, "max_amt": 12000},
    
    # Shadow Detection Scenarios (Real-world "Risk" patterns)
    {"vendor": "Graybar Electric Co", "desc": "Express shipping for electrical parts", "dept": "AIR: San Francisco Airport", "ptype": "Corporate Card", "holder": "Michael Chen", "min_amt": 150, "max_amt": 950},
    {"vendor": "Home Depot USA Inc", "desc": "Urgent plumbing repair supplies - Sector B", "dept": "REC: Recreation & Parks", "ptype": "Expense Claim", "holder": "Robert Garcia", "min_amt": 45, "max_amt": 350},
    {"vendor": "CDW Government LLC", "desc": "Expedited laptop battery replacements", "dept": "LIB: Public Library", "ptype": "Corporate Card", "holder": "Sarah Miller", "min_amt": 200, "max_amt": 1200},
    {"vendor": " United Rentals", "desc": "Emergency generator rental for site 9", "dept": "PUC: Public Utilities Commission", "ptype": "Corporate Card", "holder": "James Wilson", "min_amt": 1500, "max_amt": 4500},
    {"vendor": "Fastenal Company", "desc": "Fastener kit - Rush weekend order", "dept": "DPW: Public Works", "ptype": "Corporate Card", "holder": "Mark Davis", "min_amt": 75, "max_amt": 550},
]

import random
def get_random_transaction():
    s = random.choice(SF_REAL_SCENARIOS)
    return {
        "vendor": s["vendor"],
        "description": s["desc"],
        "amount": round(random.uniform(s["min_amt"], s["max_amt"]), 2),
        "department": s["dept"],
        "payment_type": s["ptype"],
        "card_holder": s["holder"],
        "date": "2024-03-24" # Simulation date
    }
