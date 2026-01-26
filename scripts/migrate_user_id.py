import os
import sqlite3

DB_PATH = "data/greencredit.db"


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    print(f"Migrating database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables = ["agenttool", "mcpserver"]

    for table in tables:
        try:
            print(f"Attempting to add user_id to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN user_id TEXT")
            print(f"✅ Successfully added user_id to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e):
                print(f"ℹ️  Column user_id already exists in {table}")
            else:
                print(f"❌ Error altering {table}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
