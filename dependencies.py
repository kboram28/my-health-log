from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth import get_user_by_id
from security import decode_access_token


# Swagger의 Authorize 버튼에 "Value"란 하나만 뜨고,
# 거기에 /auth/login에서 받은 access_token 값을 그대로 붙여넣으면 됨
# (Bearer 접두어는 자동으로 붙음)
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    """
    FR-03: 요청 헤더의 JWT를 검증해 현재 사용자 식별
    - 토큰 없음/만료/위조 시 401
    - 토큰은 유효하지만 사용자가 DB에 없는 경우(탈퇴 등)도 401
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="인증 정보가 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = get_user_by_id(int(user_id))
    if user is None:
        raise credentials_exception

    return user


def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    FR-04: role 기반 접근 제어
    - 관리자 전용 API에서 이 의존성을 쓰면 일반 사용자는 403
    - (Phase 4 관리자 기능에서 사용 예정. 지금 미리 만들어 둠)
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")

    return current_user