"""
관리자 계정 시딩 스크립트 (PRD 가정: '관리자 계정은 최초 1개를 수동으로 생성')

API 엔드포인트가 아니라 서버 운영자가 터미널에서 직접 실행하는 용도입니다.
(회원가입 API로는 절대 admin 계정을 만들 수 없도록 설계했기 때문)

사용법:
    python seed_admin.py <email> <password> <name>

예:
    python seed_admin.py admin@myhealthlog.com adminpw123 관리자
"""

import sys
from datetime import datetime

from database import get_connection, create_tables
from security import hash_password


def seed_admin(email: str, password: str, name: str):
    create_tables()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        print(f"이미 존재하는 이메일입니다: {email}")
        conn.close()
        return

    cursor.execute(
        """
        INSERT INTO users (email, password, name, role, created_at)
        VALUES (?, ?, ?, 'admin', ?)
        """,
        (email, hash_password(password), name, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    print(f"관리자 계정이 생성되었습니다: {email}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("사용법: python seed_admin.py <email> <password> <name>")
        sys.exit(1)

    seed_admin(sys.argv[1], sys.argv[2], sys.argv[3])