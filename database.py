import sqlite3

DB_NAME = "health.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # 회원 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 건강기록 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT NOT NULL,
        weight REAL NOT NULL,
        height REAL NOT NULL,
        systolic INTEGER NOT NULL,
        diastolic INTEGER NOT NULL,
        blood_sugar INTEGER NOT NULL,
        steps INTEGER DEFAULT 0,
        sleep_hours REAL DEFAULT 0,
        memo TEXT,
        bmi REAL,
        bmi_category TEXT,
        bp_category TEXT,
        sugar_category TEXT,
        warnings TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()