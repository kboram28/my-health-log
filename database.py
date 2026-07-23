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
    # - username 대신 email을 로그인 아이디로 사용
    # - role: "user"(일반 사용자) / "admin"(관리자) 구분
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TEXT NOT NULL
    )
    """)

    # 건강기록 테이블 (기존 그대로, 이번 단계에서는 손대지 않음)
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

    # 목표 테이블 (1인당 1개, user_id에 UNIQUE 제약)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        target_weight REAL,
        target_systolic INTEGER,
        target_diastolic INTEGER,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()