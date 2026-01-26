from app.core.db import init_db

if __name__ == "__main__":
    print("Initializing database to create users table...")
    init_db()
    print("Done.")
