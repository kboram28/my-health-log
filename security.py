import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv()  # .env 파일이 있으면 환경변수로 불러옴


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ────────────────────────────────
# JWT 설정
# ────────────────────────────────
# SECRET_KEY는 코드에 하드코딩하지 않고 .env / 환경변수에서만 읽는다.
# (.env는 .gitignore에 포함되어 있어 저장소에는 올라가지 않음)
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "환경변수 SECRET_KEY가 설정되지 않았습니다. "
        "프로젝트 루트에 .env 파일을 만들고 SECRET_KEY=... 를 추가하세요. "
        "(.env.example 참고)"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24시간


def create_access_token(data: dict) -> str:
    """
    JWT 액세스 토큰 생성

    data 예: {"sub": "1", "role": "user"}  (sub = 사용자 id, 문자열이어야 함)
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    JWT 검증 및 payload 반환
    - 서명 위조 / 만료 시 None 반환 (FR-03: 401 처리는 호출하는 쪽에서)
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# 비밀번호 암호화
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# 비밀번호 검증
def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password
    )