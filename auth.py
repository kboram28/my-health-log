from passlib.context import CryptContext
from datetime import datetime
import sqlite3

from database import get_connection


# 비밀번호 암호화 설정
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ────────────────────────────────
# 비밀번호 관련 함수
# ────────────────────────────────

def hash_password(password: str) -> str:
    """
    입력받은 비밀번호를 bcrypt로 암호화
    """
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    입력 비밀번호와 DB의 암호화된 비밀번호 비교
    """
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# ────────────────────────────────
# 회원가입
# ────────────────────────────────

def create_user(
    username: str,
    password: str,
    name: str
):
    """
    사용자 회원가입 처리

    1. 비밀번호 암호화
    2. users 테이블 저장
    """

    conn = get_connection()
    cursor = conn.cursor()

    # 비밀번호 암호화
    hashed_password = hash_password(password)

    created_at = datetime.now().isoformat()

    try:
        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                password,
                name,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                username,
                hashed_password,
                name,
                created_at
            )
        )

        conn.commit()

        user_id = cursor.lastrowid

        return {
            "id": user_id,
            "username": username,
            "name": name,
            "created_at": created_at
        }

    except sqlite3.IntegrityError:
        # username UNIQUE 중복
        return None

    finally:
        conn.close()



# ────────────────────────────────
# 로그인
# ────────────────────────────────

def authenticate_user(
    username: str,
    password: str
):
    """
    로그인 처리

    1. username으로 사용자 검색
    2. 비밀번호 비교
    """

    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (username,)
    )

    user = cursor.fetchone()

    conn.close()


    # 사용자가 없음
    if user is None:
        return None


    # 비밀번호 검사
    if not verify_password(
        password,
        user["password"]
    ):
        return None


    return {
        "id": user["id"],
        "username": user["username"],
        "name": user["name"],
        "created_at": user["created_at"]
    }