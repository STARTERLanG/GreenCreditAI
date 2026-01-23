from sqlmodel import Session
from app.core.db import engine
from app.models.file import FileParsingCache
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE file_parsing_cache ADD COLUMN indexed BOOLEAN DEFAULT 0"))
            conn.commit()
            print("Successfully added 'indexed' column to file_parsing_cache.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Column 'indexed' already exists, skipping.")
            else:
                print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
