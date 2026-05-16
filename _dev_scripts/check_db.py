import sqlite3
conn = sqlite3.connect('shadow_supply.db')
cursor = conn.cursor()

tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
for table in tables:
    tname = table[0]
    try:
        columns = cursor.execute(f"PRAGMA table_info({tname});").fetchall()
        for col in columns:
            if col[2] in ('VARCHAR', 'TEXT', 'STRING', 'String'):
                res = cursor.execute(f"SELECT {col[1]} FROM {tname} WHERE {col[1]} LIKE '%â%';").fetchall()
                if res:
                    print(f"Found in {tname}.{col[1]}: {len(res)} rows. First: {res[0]}")
    except Exception as e:
        print(e)
