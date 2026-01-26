import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


def migrate():
    """手动添加 user_id 列到 chat_sessions 表"""
    db_path = settings.SQLITE_DB_PATH.replace("sqlite:///", "")
    print(f"Migrating database at: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查列是否存在
        cursor.execute("PRAGMA table_info(chat_sessions)")
        columns = [info[1] for info in cursor.fetchall()]

        if "user_id" in columns:
            print("Column 'user_id' already exists. Skipping.")
        else:
            print("Adding column 'user_id'...")
            cursor.execute("ALTER TABLE chat_sessions ADD COLUMN user_id TEXT")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id ON chat_sessions (user_id)")
            print("Column added successfully.")

        conn.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
