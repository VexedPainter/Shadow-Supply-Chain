"""
Generate comprehensive realistic datasets for the Shadow Supply Chain system.
Produces 50+ transactions, 20+ vendors, 20+ POs, 15+ inventory items, and maintenance logs.
Simulates real ERP/financial data extraction.
"""
import csv, os, random
from datetime import datetime, timedelta

os.makedirs("data", exist_ok=True)

# ─── VENDORS (20+) ────────────────────────────────────────────
vendors = [
    {"id": "V001", "name": "Industrial Parts Express", "category": "MRO Supplies", "risk_level": "Low", "approved": True, "avg_order": 1200},
    {"id": "V002", "name": "Fastener World", "category": "Fasteners", "risk_level": "Low", "approved": True, "avg_order": 350},
    {"id": "V003", "name": "Emergency Hardware Supply", "category": "General Hardware", "risk_level": "High", "approved": False, "avg_order": 900},
    {"id": "V004", "name": "Global Logistics Corp", "category": "Logistics", "risk_level": "Low", "approved": True, "avg_order": 2500},
    {"id": "V005", "name": "Precision Tools Inc", "category": "Tooling", "risk_level": "Medium", "approved": True, "avg_order": 750},
    {"id": "V006", "name": "QuickFix Parts Shop", "category": "General Hardware", "risk_level": "High", "approved": False, "avg_order": 200},
    {"id": "V007", "name": "TechnoElec Solutions", "category": "Electronics", "risk_level": "Medium", "approved": True, "avg_order": 1800},
    {"id": "V008", "name": "SafetyFirst Equipment", "category": "Safety", "risk_level": "Low", "approved": True, "avg_order": 600},
    {"id": "V009", "name": "HydroFlow Systems", "category": "Hydraulics", "risk_level": "Low", "approved": True, "avg_order": 2200},
    {"id": "V010", "name": "WeldPro Supplies", "category": "Welding", "risk_level": "Low", "approved": True, "avg_order": 480},
    {"id": "V011", "name": "AirTech HVAC", "category": "HVAC", "risk_level": "Medium", "approved": True, "avg_order": 1400},
    {"id": "V012", "name": "Bob's Hardware Store", "category": "General Hardware", "risk_level": "High", "approved": False, "avg_order": 120},
    {"id": "V013", "name": "Pacific Bearing Co", "category": "Bearings", "risk_level": "Low", "approved": True, "avg_order": 900},
    {"id": "V014", "name": "National Electric Supply", "category": "Electronics", "risk_level": "Low", "approved": True, "avg_order": 1600},
    {"id": "V015", "name": "Midnight Auto Parts", "category": "General Hardware", "risk_level": "High", "approved": False, "avg_order": 300},
    {"id": "V016", "name": "ChemGuard Industrial", "category": "Chemicals", "risk_level": "Medium", "approved": True, "avg_order": 550},
    {"id": "V017", "name": "SteelCraft Manufacturing", "category": "Raw Materials", "risk_level": "Low", "approved": True, "avg_order": 3500},
    {"id": "V018", "name": "Joe's Corner Shop", "category": "General Hardware", "risk_level": "High", "approved": False, "avg_order": 80},
    {"id": "V019", "name": "PumpMaster International", "category": "Pumps", "risk_level": "Low", "approved": True, "avg_order": 4200},
    {"id": "V020", "name": "GasketPro Ltd", "category": "Seals & Gaskets", "risk_level": "Medium", "approved": True, "avg_order": 350},
    {"id": "V021", "name": "Random Online Seller", "category": "Unknown", "risk_level": "High", "approved": False, "avg_order": 150},
]
with open("data/vendors.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "name", "category", "risk_level", "approved", "avg_order"])
    w.writeheader(); w.writerows(vendors)

# ─── INVENTORY (15+) ──────────────────────────────────────────
inventory_items = [
    {"id": "INV001", "name": "Hydro-Pump XL", "sku": "HP-XL-001", "quantity": 15, "unit_price": 1200.00, "category": "Pumps", "reorder_level": 5, "location": "Warehouse A"},
    {"id": "INV002", "name": "Steel Bolt M10x40", "sku": "SB-M10-40", "quantity": 2500, "unit_price": 0.45, "category": "Fasteners", "reorder_level": 500, "location": "Warehouse B"},
    {"id": "INV003", "name": "Control Board Rev3", "sku": "CB-R3-001", "quantity": 8, "unit_price": 450.00, "category": "Electronics", "reorder_level": 3, "location": "Warehouse A"},
    {"id": "INV004", "name": "HVAC Filter 20x25", "sku": "HF-2025", "quantity": 45, "unit_price": 32.00, "category": "HVAC", "reorder_level": 20, "location": "Warehouse C"},
    {"id": "INV005", "name": "Bearing 6205-2RS", "sku": "BR-6205", "quantity": 120, "unit_price": 12.50, "category": "Bearings", "reorder_level": 30, "location": "Warehouse B"},
    {"id": "INV006", "name": "Safety Goggles Pro", "sku": "SG-PRO", "quantity": 200, "unit_price": 18.00, "category": "Safety", "reorder_level": 50, "location": "Warehouse C"},
    {"id": "INV007", "name": "Hydraulic Hose 1/2in", "sku": "HH-050", "quantity": 30, "unit_price": 45.00, "category": "Hydraulics", "reorder_level": 10, "location": "Warehouse A"},
    {"id": "INV008", "name": "Welding Rod E6013", "sku": "WR-6013", "quantity": 500, "unit_price": 3.20, "category": "Welding", "reorder_level": 100, "location": "Warehouse B"},
    {"id": "INV009", "name": "PLC Module S7-1200", "sku": "PLC-S7", "quantity": 4, "unit_price": 850.00, "category": "Electronics", "reorder_level": 2, "location": "Warehouse A"},
    {"id": "INV010", "name": "Conveyor Belt 6ft", "sku": "CB-6FT", "quantity": 10, "unit_price": 280.00, "category": "Conveyors", "reorder_level": 3, "location": "Warehouse A"},
    {"id": "INV011", "name": "Gasket Set Industrial", "sku": "GS-IND", "quantity": 85, "unit_price": 22.00, "category": "Seals & Gaskets", "reorder_level": 25, "location": "Warehouse B"},
    {"id": "INV012", "name": "Motor 2HP 3-Phase", "sku": "MT-2HP", "quantity": 6, "unit_price": 680.00, "category": "Motors", "reorder_level": 2, "location": "Warehouse A"},
    {"id": "INV013", "name": "Pressure Gauge 0-100PSI", "sku": "PG-100", "quantity": 35, "unit_price": 28.00, "category": "Instrumentation", "reorder_level": 10, "location": "Warehouse C"},
    {"id": "INV014", "name": "Lubricant ISO 68", "sku": "LB-68", "quantity": 60, "unit_price": 15.00, "category": "Chemicals", "reorder_level": 20, "location": "Warehouse B"},
    {"id": "INV015", "name": "Steel Plate 4x8 Sheet", "sku": "SP-4X8", "quantity": 25, "unit_price": 180.00, "category": "Raw Materials", "reorder_level": 8, "location": "Warehouse D"},
    {"id": "INV016", "name": "V-Belt A68", "sku": "VB-A68", "quantity": 40, "unit_price": 14.00, "category": "Power Transmission", "reorder_level": 15, "location": "Warehouse B"},
]
with open("data/inventory.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "name", "sku", "quantity", "unit_price", "category", "reorder_level", "location"])
    w.writeheader(); w.writerows(inventory_items)

# ─── PROCUREMENT RECORDS (20+) ────────────────────────────────
procurement = [
    {"id": "PO-001", "vendor_id": "V001", "vendor_name": "Industrial Parts Express", "item": "Hydro-Pump XL x2", "amount": 2400.00, "quantity": 2, "date": "2024-03-01", "status": "Delivered", "department": "Maintenance"},
    {"id": "PO-002", "vendor_id": "V002", "vendor_name": "Fastener World", "item": "Steel Bolt M10x40 (Box/500)", "amount": 225.00, "quantity": 500, "date": "2024-03-03", "status": "Delivered", "department": "Production"},
    {"id": "PO-003", "vendor_id": "V007", "vendor_name": "TechnoElec Solutions", "item": "Control Board Rev3 x3", "amount": 1350.00, "quantity": 3, "date": "2024-03-05", "status": "Delivered", "department": "Engineering"},
    {"id": "PO-004", "vendor_id": "V004", "vendor_name": "Global Logistics Corp", "item": "Freight Shipment Q1", "amount": 4200.00, "quantity": 1, "date": "2024-03-06", "status": "Delivered", "department": "Logistics"},
    {"id": "PO-005", "vendor_id": "V005", "vendor_name": "Precision Tools Inc", "item": "Torque Wrench Set", "amount": 680.00, "quantity": 2, "date": "2024-03-08", "status": "Delivered", "department": "Maintenance"},
    {"id": "PO-006", "vendor_id": "V008", "vendor_name": "SafetyFirst Equipment", "item": "Safety Goggles Pro (Box/50)", "amount": 900.00, "quantity": 50, "date": "2024-03-10", "status": "Delivered", "department": "HSE"},
    {"id": "PO-007", "vendor_id": "V013", "vendor_name": "Pacific Bearing Co", "item": "Bearing 6205-2RS (Pack/20)", "amount": 250.00, "quantity": 20, "date": "2024-03-11", "status": "Delivered", "department": "Maintenance"},
    {"id": "PO-008", "vendor_id": "V009", "vendor_name": "HydroFlow Systems", "item": "Hydraulic Hose Assembly", "amount": 2100.00, "quantity": 5, "date": "2024-03-12", "status": "Delivered", "department": "Maintenance"},
    {"id": "PO-009", "vendor_id": "V010", "vendor_name": "WeldPro Supplies", "item": "Welding Rod E6013 (50kg)", "amount": 480.00, "quantity": 50, "date": "2024-03-14", "status": "Delivered", "department": "Fabrication"},
    {"id": "PO-010", "vendor_id": "V011", "vendor_name": "AirTech HVAC", "item": "HVAC Filter Set (20x25)", "amount": 640.00, "quantity": 20, "date": "2024-03-15", "status": "Delivered", "department": "Facilities"},
    {"id": "PO-011", "vendor_id": "V014", "vendor_name": "National Electric Supply", "item": "PLC Module S7-1200 x2", "amount": 1700.00, "quantity": 2, "date": "2024-03-17", "status": "Delivered", "department": "Engineering"},
    {"id": "PO-012", "vendor_id": "V016", "vendor_name": "ChemGuard Industrial", "item": "Industrial Degreaser 20L", "amount": 320.00, "quantity": 4, "date": "2024-03-18", "status": "Delivered", "department": "Maintenance"},
    {"id": "PO-013", "vendor_id": "V017", "vendor_name": "SteelCraft Manufacturing", "item": "Steel Plate 4x8 (10 sheets)", "amount": 1800.00, "quantity": 10, "date": "2024-03-19", "status": "Delivered", "department": "Fabrication"},
    {"id": "PO-014", "vendor_id": "V019", "vendor_name": "PumpMaster International", "item": "Centrifugal Pump CP-200", "amount": 4200.00, "quantity": 1, "date": "2024-03-20", "status": "In Transit", "department": "Maintenance"},
    {"id": "PO-015", "vendor_id": "V020", "vendor_name": "GasketPro Ltd", "item": "Gasket Set Industrial (Box)", "amount": 440.00, "quantity": 20, "date": "2024-03-21", "status": "In Transit", "department": "Maintenance"},
    {"id": "PO-016", "vendor_id": "V002", "vendor_name": "Fastener World", "item": "Hex Nut M10 (Box/1000)", "amount": 180.00, "quantity": 1000, "date": "2024-03-22", "status": "Pending", "department": "Production"},
    {"id": "PO-017", "vendor_id": "V005", "vendor_name": "Precision Tools Inc", "item": "Digital Caliper Set", "amount": 520.00, "quantity": 4, "date": "2024-03-23", "status": "Pending", "department": "QC"},
    {"id": "PO-018", "vendor_id": "V008", "vendor_name": "SafetyFirst Equipment", "item": "Hard Hat Type II (25pc)", "amount": 625.00, "quantity": 25, "date": "2024-03-24", "status": "Pending", "department": "HSE"},
]
with open("data/procurement_records.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "vendor_id", "vendor_name", "item", "amount", "quantity", "date", "status", "department"])
    w.writeheader(); w.writerows(procurement)

# ─── FINANCIAL TRANSACTIONS (50+) ─────────────────────────────
transactions = [
    # ✅ MATCHED transactions (have corresponding POs)
    {"id": "TXN-1001", "date": "2024-03-02", "vendor": "Industrial Parts Express", "amount": 2400.00, "description": "Hydro-Pump XL x2 per PO-001", "payment_type": "Invoice", "card_holder": "System", "department": "Maintenance"},
    {"id": "TXN-1002", "date": "2024-03-04", "vendor": "Fastener World", "amount": 225.00, "description": "Steel bolts M10 box 500pc", "payment_type": "Invoice", "card_holder": "System", "department": "Production"},
    {"id": "TXN-1003", "date": "2024-03-06", "vendor": "TechnoElec Solutions", "amount": 1350.00, "description": "Control boards Rev3 x3", "payment_type": "Invoice", "card_holder": "System", "department": "Engineering"},
    {"id": "TXN-1004", "date": "2024-03-07", "vendor": "Global Logistics Corp", "amount": 4200.00, "description": "Q1 freight charges", "payment_type": "Invoice", "card_holder": "System", "department": "Logistics"},
    {"id": "TXN-1005", "date": "2024-03-09", "vendor": "Precision Tools Inc", "amount": 680.00, "description": "Torque wrench set x2", "payment_type": "Invoice", "card_holder": "System", "department": "Maintenance"},
    {"id": "TXN-1006", "date": "2024-03-11", "vendor": "SafetyFirst Equipment", "amount": 900.00, "description": "Safety goggles bulk order", "payment_type": "Invoice", "card_holder": "System", "department": "HSE"},
    {"id": "TXN-1007", "date": "2024-03-12", "vendor": "Pacific Bearing Co", "amount": 250.00, "description": "Bearings 6205-2RS pack 20", "payment_type": "Invoice", "card_holder": "System", "department": "Maintenance"},
    {"id": "TXN-1008", "date": "2024-03-13", "vendor": "HydroFlow Systems", "amount": 2100.00, "description": "Hydraulic hose assembly x5", "payment_type": "Invoice", "card_holder": "System", "department": "Maintenance"},
    {"id": "TXN-1009", "date": "2024-03-15", "vendor": "WeldPro Supplies", "amount": 480.00, "description": "Welding rod E6013 50kg", "payment_type": "Invoice", "card_holder": "System", "department": "Fabrication"},
    {"id": "TXN-1010", "date": "2024-03-16", "vendor": "AirTech HVAC", "amount": 640.00, "description": "HVAC filters 20x25 set", "payment_type": "Invoice", "card_holder": "System", "department": "Facilities"},
    {"id": "TXN-1011", "date": "2024-03-18", "vendor": "National Electric Supply", "amount": 1700.00, "description": "PLC module S7-1200 x2", "payment_type": "Invoice", "card_holder": "System", "department": "Engineering"},
    {"id": "TXN-1012", "date": "2024-03-19", "vendor": "ChemGuard Industrial", "amount": 320.00, "description": "Industrial degreaser 20L x4", "payment_type": "Invoice", "card_holder": "System", "department": "Maintenance"},
    {"id": "TXN-1013", "date": "2024-03-20", "vendor": "SteelCraft Manufacturing", "amount": 1800.00, "description": "Steel plate 4x8 10 sheets", "payment_type": "Invoice", "card_holder": "System", "department": "Fabrication"},

    # ❌ SHADOW PURCHASES — No matching PO (emergency/bypass purchases)
    # -- Emergency repairs (high urgency, no time for PO)
    {"id": "TXN-2001", "date": "2024-03-08", "vendor": "Emergency Hardware Supply", "amount": 850.00, "description": "Emergency HVAC compressor repair parts — valve and seals", "payment_type": "Corporate Card", "card_holder": "John Miller", "department": "Maintenance"},
    {"id": "TXN-2002", "date": "2024-03-10", "vendor": "QuickFix Parts Shop", "amount": 175.00, "description": "Assorted O-rings and gaskets for pump station A", "payment_type": "Corporate Card", "card_holder": "Sarah Chen", "department": "Production"},
    {"id": "TXN-2003", "date": "2024-03-14", "vendor": "Emergency Hardware Supply", "amount": 1250.00, "description": "Replacement motor 2HP for conveyor belt B3", "payment_type": "Corporate Card", "card_holder": "John Miller", "department": "Production"},
    {"id": "TXN-2004", "date": "2024-03-16", "vendor": "Bob's Hardware Store", "amount": 67.50, "description": "Workshop cleaning supplies and rags", "payment_type": "Expense Claim", "card_holder": "Dave Wilson", "department": "Facilities"},
    {"id": "TXN-2005", "date": "2024-03-17", "vendor": "QuickFix Parts Shop", "amount": 320.00, "description": "Hydraulic fittings emergency order", "payment_type": "Corporate Card", "card_holder": "Sarah Chen", "department": "Maintenance"},
    {"id": "TXN-2006", "date": "2024-03-19", "vendor": "Industrial Parts Express", "amount": 89.00, "description": "Electrical tape and cable ties", "payment_type": "Expense Claim", "card_holder": "Mike Johnson", "department": "Maintenance"},
    {"id": "TXN-2007", "date": "2024-03-20", "vendor": "TechnoElec Solutions", "amount": 2200.00, "description": "PLC module replacement rush order — line 4 down", "payment_type": "Corporate Card", "card_holder": "Alex Rivera", "department": "Engineering"},

    # -- Weekend/after-hours emergency purchases
    {"id": "TXN-2008", "date": "2024-03-16", "vendor": "Midnight Auto Parts", "amount": 445.00, "description": "Emergency drive belt and tensioner for main compressor", "payment_type": "Corporate Card", "card_holder": "John Miller", "department": "Maintenance"},
    {"id": "TXN-2009", "date": "2024-03-17", "vendor": "Bob's Hardware Store", "amount": 125.00, "description": "PVC pipes and fittings for coolant line repair", "payment_type": "Expense Claim", "card_holder": "Tom Brown", "department": "Maintenance"},
    {"id": "TXN-2010", "date": "2024-03-23", "vendor": "Joe's Corner Shop", "amount": 42.00, "description": "WD-40 and misc lubricants night shift", "payment_type": "Expense Claim", "card_holder": "Dave Wilson", "department": "Maintenance"},

    # -- Bulk emergency (high value, high risk)
    {"id": "TXN-2011", "date": "2024-03-22", "vendor": "Emergency Hardware Supply", "amount": 4500.00, "description": "Bulk emergency pump rebuild kit for planned shutdown", "payment_type": "Corporate Card", "card_holder": "John Miller", "department": "Maintenance"},
    {"id": "TXN-2012", "date": "2024-03-24", "vendor": "Random Online Seller", "amount": 890.00, "description": "Specialty pressure relief valve — 3 day shipping", "payment_type": "Corporate Card", "card_holder": "Alex Rivera", "department": "Engineering"},
    {"id": "TXN-2013", "date": "2024-03-25", "vendor": "QuickFix Parts Shop", "amount": 560.00, "description": "Bearing replacement set for mixer unit", "payment_type": "Corporate Card", "card_holder": "Sarah Chen", "department": "Production"},

    # -- Small miscellaneous (pattern of many small purchases)
    {"id": "TXN-2014", "date": "2024-03-11", "vendor": "Bob's Hardware Store", "amount": 34.00, "description": "Duct tape and zip ties", "payment_type": "Expense Claim", "card_holder": "Tom Brown", "department": "Production"},
    {"id": "TXN-2015", "date": "2024-03-13", "vendor": "Joe's Corner Shop", "amount": 28.50, "description": "Spray paint and markers", "payment_type": "Expense Claim", "card_holder": "Dave Wilson", "department": "Facilities"},
    {"id": "TXN-2016", "date": "2024-03-21", "vendor": "Midnight Auto Parts", "amount": 210.00, "description": "Alternator for forklift #3", "payment_type": "Corporate Card", "card_holder": "Mike Johnson", "department": "Maintenance"},
    {"id": "TXN-2017", "date": "2024-03-26", "vendor": "Emergency Hardware Supply", "amount": 1800.00, "description": "Control valve assembly for boiler room", "payment_type": "Corporate Card", "card_holder": "John Miller", "department": "Maintenance"},
    {"id": "TXN-2018", "date": "2024-03-27", "vendor": "Random Online Seller", "amount": 155.00, "description": "Replacement thermocouple sensor", "payment_type": "Corporate Card", "card_holder": "Alex Rivera", "department": "Engineering"},
    {"id": "TXN-2019", "date": "2024-03-28", "vendor": "QuickFix Parts Shop", "amount": 95.00, "description": "Pipe thread sealant and teflon tape bulk", "payment_type": "Expense Claim", "card_holder": "Sarah Chen", "department": "Maintenance"},
    {"id": "TXN-2020", "date": "2024-03-15", "vendor": "Midnight Auto Parts", "amount": 780.00, "description": "Starter motor and solenoid for generator backup", "payment_type": "Corporate Card", "card_holder": "John Miller", "department": "Maintenance"},

    # -- Shift-end rush purchases
    {"id": "TXN-2021", "date": "2024-03-18", "vendor": "Emergency Hardware Supply", "amount": 340.00, "description": "Fire extinguisher refills emergency", "payment_type": "Corporate Card", "card_holder": "Tom Brown", "department": "HSE"},
    {"id": "TXN-2022", "date": "2024-03-22", "vendor": "Bob's Hardware Store", "amount": 78.00, "description": "Extension cords and power strips", "payment_type": "Expense Claim", "card_holder": "Dave Wilson", "department": "Facilities"},
    {"id": "TXN-2023", "date": "2024-03-26", "vendor": "Joe's Corner Shop", "amount": 55.00, "description": "First aid kit refill supplies", "payment_type": "Expense Claim", "card_holder": "Tom Brown", "department": "HSE"},

    # ✅ MORE MATCHED transactions
    {"id": "TXN-1014", "date": "2024-03-21", "vendor": "PumpMaster International", "amount": 4200.00, "description": "Centrifugal pump CP-200", "payment_type": "Invoice", "card_holder": "System", "department": "Maintenance"},
    {"id": "TXN-1015", "date": "2024-03-22", "vendor": "GasketPro Ltd", "amount": 440.00, "description": "Gasket set industrial box", "payment_type": "Invoice", "card_holder": "System", "department": "Maintenance"},
    {"id": "TXN-1016", "date": "2024-03-23", "vendor": "Fastener World", "amount": 180.00, "description": "Hex nut M10 box 1000pc", "payment_type": "Invoice", "card_holder": "System", "department": "Production"},
    {"id": "TXN-1017", "date": "2024-03-24", "vendor": "Precision Tools Inc", "amount": 520.00, "description": "Digital caliper set x4", "payment_type": "Invoice", "card_holder": "System", "department": "QC"},
    {"id": "TXN-1018", "date": "2024-03-25", "vendor": "SafetyFirst Equipment", "amount": 625.00, "description": "Hard hat type II 25pc", "payment_type": "Invoice", "card_holder": "System", "department": "HSE"},

    # ❌ ANOMALOUS (unusually high value or odd pattern)
    {"id": "TXN-2024", "date": "2024-03-28", "vendor": "Emergency Hardware Supply", "amount": 8750.00, "description": "Complete hydraulic system rebuild — unplanned outage", "payment_type": "Corporate Card", "card_holder": "John Miller", "department": "Maintenance"},
    {"id": "TXN-2025", "date": "2024-03-29", "vendor": "Random Online Seller", "amount": 3200.00, "description": "Custom fabricated mounting bracket express delivery", "payment_type": "Corporate Card", "card_holder": "Alex Rivera", "department": "Engineering"},
]

with open("data/financial_transactions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "date", "vendor", "amount", "description", "payment_type", "card_holder", "department"])
    w.writeheader(); w.writerows(transactions)

# ─── MAINTENANCE LOGS (10+) ───────────────────────────────────
logs = [
    {"id": "ML-001", "date": "2024-03-08", "equipment": "HVAC Compressor Unit 3", "technician": "John Miller", "issue": "Compressor failure — emergency repair", "parts_used": "HVAC compressor repair parts", "resolution": "Replaced faulty valve and seals"},
    {"id": "ML-002", "date": "2024-03-10", "equipment": "Pump Station A", "technician": "Sarah Chen", "issue": "Seal leakage on primary pump", "parts_used": "O-rings and gaskets set", "resolution": "Replaced seals, tested under pressure"},
    {"id": "ML-003", "date": "2024-03-14", "equipment": "Conveyor Belt B3", "technician": "John Miller", "issue": "Motor burnout — line stopped", "parts_used": "Replacement motor 2HP", "resolution": "Installed new motor, belt re-tensioned"},
    {"id": "ML-004", "date": "2024-03-16", "equipment": "Main Air Compressor", "technician": "John Miller", "issue": "Drive belt snapped during weekend shift", "parts_used": "Drive belt and tensioner", "resolution": "Emergency belt replacement from auto parts store"},
    {"id": "ML-005", "date": "2024-03-17", "equipment": "Coolant System Line 2", "technician": "Tom Brown", "issue": "Coolant line crack — leaking on floor", "parts_used": "PVC pipe fittings", "resolution": "Temporary pipe repair, scheduled full replacement"},
    {"id": "ML-006", "date": "2024-03-17", "equipment": "Hydraulic Press HP-02", "technician": "Sarah Chen", "issue": "Hydraulic line burst", "parts_used": "Hydraulic fittings", "resolution": "Emergency fitting replacement"},
    {"id": "ML-007", "date": "2024-03-20", "equipment": "PLC Cabinet Line 4", "technician": "Alex Rivera", "issue": "PLC module failure — line 4 down", "parts_used": "PLC module Siemens S7-1200", "resolution": "Module swapped, program restored from backup"},
    {"id": "ML-008", "date": "2024-03-22", "equipment": "Pump Station B", "technician": "John Miller", "issue": "Planned shutdown — full pump overhaul", "parts_used": "Pump rebuild kit, bearings, seals", "resolution": "Complete rebuild during planned outage"},
    {"id": "ML-009", "date": "2024-03-24", "equipment": "Pressure System PS-01", "technician": "Alex Rivera", "issue": "Pressure relief valve malfunction", "parts_used": "Specialty pressure relief valve", "resolution": "Valve replaced, system re-certified"},
    {"id": "ML-010", "date": "2024-03-28", "equipment": "Hydraulic System Main", "technician": "John Miller", "issue": "Catastrophic hydraulic failure — full rebuild", "parts_used": "Complete hydraulic kit, hoses, valves", "resolution": "Full system rebuild, 48hr downtime"},
]
with open("data/maintenance_logs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "date", "equipment", "technician", "issue", "parts_used", "resolution"])
    w.writeheader(); w.writerows(logs)

print("=" * 60)
print("✅ COMPREHENSIVE DATASETS GENERATED")
print("=" * 60)
print(f"   📦 {len(vendors)} vendors (6 high-risk, 5 medium, 10 low)")
print(f"   📋 {len(inventory_items)} inventory items")
print(f"   📄 {len(procurement)} procurement records (POs)")
print(f"   💳 {len(transactions)} financial transactions")
print(f"      ├─ {sum(1 for t in transactions if t['payment_type'] == 'Invoice')} matched invoices")
print(f"      ├─ {sum(1 for t in transactions if t['payment_type'] == 'Corporate Card')} corporate card purchases")
print(f"      └─ {sum(1 for t in transactions if t['payment_type'] == 'Expense Claim')} expense claims")
print(f"   🔧 {len(logs)} maintenance logs")
print(f"\n   Data simulates ERP extraction from structured databases.")
