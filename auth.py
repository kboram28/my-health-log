from datetime import datetime
import sqlite3

from database import get_connection
from security import hash_password, verify_password


# 회원가입

def create_user(
    email: str,
    password: str,
    name: str,
    phone: str
):
    conn = get_connection()
    cursor = conn.cursor()

    hashed_password = hash_password(password)
    created_at = datetime.now().isoformat()

    try:
        cursor.execute(
            """
            INSERT INTO users
            (
                email,
                password,
                name,
                phone,
                role,
                created_at
            )
            VALUES (?, ?, ?, ?, 'user', ?)
            """,
            (
                email,
                hashed_password,
                name,
                phone,
                created_at
            )
        )

        conn.commit()
        user_id = cursor.lastrowid

        return {
            "id": user_id,
            "email": email,
            "name": name,
            "phone": phone,
            "role": "user",
            "created_at": created_at
        }

    except sqlite3.IntegrityError:
        return None

    finally:
        conn.close()

def email_exists(email: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


# 로그인

def authenticate_user(
    email: str,
    password: str
):
    """
    로그인 처리

    1. email로 사용자 검색
    2. 비밀번호 비교
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (email,)
    )

    user = cursor.fetchone()
    conn.close()

    if user is None:
        return None

    if not verify_password(password, user["password"]):
        return None

    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "created_at": user["created_at"]
    }



# id로 사용자 조회 (JWT 인증 미들웨어에서 사용)

def get_user_by_id(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    user = cursor.fetchone()
    conn.close()

    if user is None:
        return None

    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "created_at": user["created_at"]
    }


# 회원 탈퇴 (계정 삭제)

def delete_user(user_id: int) -> dict:
    """
    계정 삭제
    - 연관된 records/goals도 함께 삭제 (SQLite는 FK CASCADE를 자동으로 강제하지 않으므로 직접 정리)
    - 마지막 남은 관리자 계정은 삭제하지 못하게 막음
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return {"success": False, "reason": "not_found"}

    if row["role"] == "admin":
        cursor.execute("SELECT COUNT(*) as c FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()["c"]
        if admin_count <= 1:
            conn.close()
            return {"success": False, "reason": "last_admin"}

    cursor.execute("DELETE FROM records WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return {"success": True}