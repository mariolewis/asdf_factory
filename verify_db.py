import sqlite3
import os

db_path = os.path.join("data", "klyve.db")

if not os.path.exists(db_path):
    print(f"❌ Database not found at {db_path}")
else:
    try:
        # Attempt to connect using standard, unencrypted sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print(f"🔓 UNENCRYPTED: Standard SQLite opened the file successfully. (Correct for Dev Mode)")
        conn.close()
    except sqlite3.DatabaseError as e:
        print(f"🔒 ENCRYPTED: Standard SQLite failed to open the file.")
        print(f"   Error message: {e}")
        print(f"   (This result is CORRECT for Production Mode)")