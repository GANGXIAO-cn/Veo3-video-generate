import sqlite3
import os
from datetime import datetime

# ====== 配置数据库路径 ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ad_videos.db")


def init_db():
    """
    初始化数据库，创建 video_logs 表（如果不存在）。
    """
    if not os.path.exists(DB_PATH):
        print(f"[DB INIT] 创建数据库文件: {DB_PATH}")
    else:
        print(f"[DB INIT] 数据库已存在: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            prompt TEXT,
            status TEXT,
            task_id TEXT,
            video_url TEXT,
            error TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("[DB INIT] 数据库初始化完成 ✅")


def log_to_db(data: dict, row_id: int = None) -> int:
    """
    插入或更新一条记录。

    :param data: 包含要写入的字段字典（如 title、prompt、status 等）
    :param row_id: 如果提供，则更新对应 ID 的行，否则插入新行
    :return: 插入或更新的记录 ID
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if row_id is not None:
        # 更新记录
        set_clause = ", ".join(f"{key}=?" for key in data.keys())
        values = list(data.values()) + [row_id]
        sql = f"UPDATE video_logs SET {set_clause} WHERE id=?"
        cursor.execute(sql, values)
        print(f"[DB] 更新记录 ID={row_id}")
    else:
        # 插入新记录
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        values = list(data.values())
        sql = f"INSERT INTO video_logs ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, values)
        row_id = cursor.lastrowid
        print(f"[DB] 插入新记录 ID={row_id}")

    conn.commit()
    conn.close()
    return row_id


def get_current_date():
    """
    返回当前时间字符串，格式为 YYYY-MM-DD HH:MM
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M")
