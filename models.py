from pydantic import BaseModel, EmailStr, Field


import re

from pydantic import BaseModel, EmailStr, Field, field_validator


# 건강 기록 입력
class RecordIn(BaseModel):
    date: str
    weight: float = Field(gt=0, le=300, description="kg, 0 초과 300 이하")
    height: float = Field(gt=0, le=250, description="cm, 0 초과 250 이하")
    systolic: int = Field(ge=50, le=300, description="mmHg")
    diastolic: int = Field(ge=30, le=200, description="mmHg")
    blood_sugar: int = Field(ge=20, le=600, description="mg/dL")
    steps: int = Field(default=0, ge=0, le=100000)
    sleep_hours: float = Field(default=0.0, ge=0, le=24)
    memo: str = ""

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다.")
        return v


# 회원가입 요청
# username 대신 email을 로그인 아이디로 사용
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="최소 8자 이상")
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
    target_weight: float | None = Field(default=None, gt=0, le=300)
    target_systolic: int | None = Field(default=None, ge=50, le=300)
    target_diastolic: int | None = Field(default=None, ge=30, le=200)