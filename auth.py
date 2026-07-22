from datetime import datetime
import sqlite3

from database import get_connection
from security import hash_password, verify_password


# 회원가입

def create_user(
    email: str,
    password: str,
    name: str
):
    """
    사용자 회원가입 처리

    1. 비밀번호 암호화
    2. users 테이블 저장 (role은 기본값 'user'로 고정)
       -> 관리자 계정은 회원가입 API로 만들 수 없고, 별도로 지정
          (누구나 회원가입만으로 관리자가 될 수 있으면 안 되기 때문)
    """

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
                role,
                created_at
            )
            VALUES (?, ?, ?, 'user', ?)
            """,
            (
                email,
                hashed_password,
                name,
                created_at
            )
        )

        conn.commit()
        user_id = cursor.lastrowid

        return {
            "id": user_id,
            "email": email,
            "name": name,
            "role": "user",
            "created_at": created_at
        }

    except sqlite3.IntegrityError:
        # email UNIQUE 중복
        return None

    finally:
        conn.close()


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