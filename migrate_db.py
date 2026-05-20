import sqlite3

try:
    conn = sqlite3.connect('shadow_supply.db')
    cursor = conn.cursor()
    
    # Add the column
    cursor.execute("ALTER TABLE inventory ADD COLUMN last_updated TEXT")
    conn.commit()
    print("✓ Column 'last_updated' added successfully to inventory table")
    
except sqlite3.OperationalError as e:
    if 'duplicate column' in str(e):
        print("✓ Column 'last_updated' already exists")
    else:
        print(f"Error: {e}")
finally:
    conn.close()
