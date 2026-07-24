import re
from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


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
        try:
            parsed = date.fromisoformat(v)
        except ValueError:
            raise ValueError("존재하지 않는 날짜입니다.")
        if parsed > date.today():
            raise ValueError("미래 날짜는 입력할 수 없습니다.")
        return v


NAME_PATTERN = re.compile(r"^[가-힣]{2,10}$")
PHONE_PATTERN = re.compile(r"^01[016789]-?\d{3,4}-?\d{4}$")


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="최소 8자 이상")
    password_confirm: str
    name: str
    phone: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not NAME_PATTERN.match(v):
            raise ValueError("이름은 한글 2~10자만 입력 가능합니다. (공백, 숫자, 영문, 특수문자 불가)")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not PHONE_PATTERN.match(v):
            raise ValueError("전화번호 형식이 올바르지 않습니다. (예: 010-1234-5678)")
        digits = re.sub(r"-", "", v)
        return f"{digits[:3]}-{digits[3:-4]}-{digits[-4:]}"

    @model_validator(mode="after")
    def validate_password_match(self):
        if self.password != self.password_confirm:
            raise ValueError("비밀번호와 비밀번호 확인이 일치하지 않습니다.")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoalIn(BaseModel):
    target_weight: float | None = Field(default=None, gt=0, le=300)
    target_systolic: int | None = Field(default=None, ge=50, le=300)
    target_diastolic: int | None = Field(default=None, ge=30, le=200)

class AccountDelete(BaseModel):
    password: str