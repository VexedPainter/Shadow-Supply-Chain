import sqlite3
from database import engine, Base

# 1. Create missing tables
Base.metadata.create_all(bind=engine)

# 2. Add missing columns to vendors table
conn = sqlite3.connect('shadow_supply.db')
cursor = conn.cursor()

columns = [
    ("tier", "INTEGER DEFAULT 1"),
    ("alternative_vendors", "TEXT DEFAULT ''"),
    ("esg_score", "REAL DEFAULT 50.0"),
    ("carbon_rating", "TEXT DEFAULT 'C'"),
    ("sustainability_certified", "BOOLEAN DEFAULT 0")
]

for col_name, col_type in columns:
    try:
        cursor.execute(f"ALTER TABLE vendors ADD COLUMN {col_name} {col_type}")
        print(f"Added column {col_name}")
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower():
            print(f"Column {col_name} already exists")
        else:
            print(f"Error adding {col_name}: {e}")

conn.commit()
conn.close()

import uuid
from database import SessionLocal, Vendor
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE vendors ADD COLUMN portal_token TEXT"))
        conn.commit()
    except Exception:
        pass

db = SessionLocal()
for vendor in db.query(Vendor).filter(Vendor.portal_token == None).all():
    vendor.portal_token = str(uuid.uuid4())
db.commit()
db.close()
print("Vendor portal tokens generated.")

print("Database upgrade complete.")
