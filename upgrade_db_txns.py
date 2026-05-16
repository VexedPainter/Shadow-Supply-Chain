import sqlite3

conn = sqlite3.connect('shadow_supply.db')
cursor = conn.cursor()

columns = [
    ("currency", "TEXT DEFAULT 'USD'"),
    ("amount_usd", "REAL"),
    ("exchange_rate", "REAL DEFAULT 1.0")
]

for col_name, col_type in columns:
    try:
        cursor.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_type}")
        print(f"Added column {col_name} to transactions")
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower():
            print(f"Column {col_name} already exists")
        else:
            print(f"Error adding {col_name}: {e}")

conn.commit()
conn.close()
print("Transactions upgrade complete.")
