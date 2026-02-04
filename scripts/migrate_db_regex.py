
import sqlite3
import os

db_path = "app/db/hoshino.db"

if not os.path.exists(db_path):
    print("DB file not found, skipping migration.")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE subscriptions ADD COLUMN filter_regex VARCHAR")
    print("Column 'filter_regex' added successfully.")
    conn.commit()
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column 'filter_regex' already exists.")
    else:
        print(f"Error: {e}")
finally:
    conn.close()
