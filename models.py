from pydantic import BaseModel, EmailStr


# 건강 기록 입력
class RecordIn(BaseModel):
    date: str
    weight: float
    height: float
    systolic: int
    diastolic: int
    blood_sugar: int
    steps: int = 0
    sleep_hours: float = 0.0
    memo: str = ""


# 회원가입 요청
# username 대신 email을 로그인 아이디로 사용
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


# 로그인 요청
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# 로그인 응답 (JWT)
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# 목표 설정 요청 (FR-12)
class GoalIn(BaseModel):
    target_weight: float | None = None
    target_systolic: int | None = None
    target_diastolic: int | None = None