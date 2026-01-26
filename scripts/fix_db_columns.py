import sqlite3
from pathlib import Path


def migrate():
    db_path = Path("data/greencredit.db")
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取现有列
    cursor.execute("PRAGMA table_info(file_parsing_cache)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns: {columns}")

    # 需要添加的列
    new_cols = [
        ("status", "VARCHAR(20) DEFAULT 'COMPLETED'"),
        ("indexed", "BOOLEAN DEFAULT 0"),
        ("error_message", "TEXT"),
    ]

    for col_name, col_type in new_cols:
        if col_name not in columns:
            try:
                print(f"Adding column {col_name}...")
                cursor.execute(f"ALTER TABLE file_parsing_cache ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists.")

    # 强制将现有的所有小写状态更新为大写，防止映射失败
    cursor.execute("UPDATE file_parsing_cache SET status = 'COMPLETED' WHERE status = 'completed'")
    cursor.execute("UPDATE file_parsing_cache SET status = 'PENDING' WHERE status = 'pending'")
    cursor.execute("UPDATE file_parsing_cache SET status = 'FAILED' WHERE status = 'failed'")
    cursor.execute("UPDATE file_parsing_cache SET status = 'INDEXING' WHERE status = 'indexing'")

    conn.commit()
    conn.close()
    print("Migration finished.")


if __name__ == "__main__":
    migrate()
