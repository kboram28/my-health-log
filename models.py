from pydantic import BaseModel


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
class UserCreate(BaseModel):
    username: str
    password: str
    name: str


# 로그인 요청
class UserLogin(BaseModel):
    username: str
    password: str