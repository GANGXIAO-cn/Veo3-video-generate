import sqlite3
import os
from datetime import datetime

import json

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

import json
import sqlite3

def log_to_db(data: dict, row_id: int = None) -> int:
    """
    插入或更新一条记录，并打印每个字段的类型，帮助定位问题。
    """
    # 调试：打印字段及类型
    print("[DB DEBUG] log_to_db got data:")
    for k, v in data.items():
        print(f"  {k}: {v!r} ({type(v).__name__})")

    # 1. 安全化所有值
    safe_vals = []
    for v in data.values():
        if isinstance(v, (str, int, float)) or v is None:
            safe_vals.append(v)
        else:
            safe_vals.append(json.dumps(v, ensure_ascii=False))

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cols = list(data.keys())

    if row_id is not None:
        # UPDATE
        set_clause = ", ".join(f"{c}=?" for c in cols)
        sql = f"UPDATE video_logs SET {set_clause} WHERE id=?"
        cur.execute(sql, (*safe_vals, row_id))
        print(f"[DB] 更新记录 ID={row_id}")
    else:
        # INSERT
        placeholders = ", ".join("?" for _ in cols)
        cols_clause  = ", ".join(cols)
        sql = f"INSERT INTO video_logs ({cols_clause}) VALUES ({placeholders})"
        cur.execute(sql, safe_vals)
        row_id = cur.lastrowid
        print(f"[DB] 插入新记录 ID={row_id}")

    conn.commit()
    conn.close()
    return row_id


def get_current_date():
    """
    返回当前时间字符串，格式为 YYYY-MM-DD HH:MM
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M")
