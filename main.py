from fastapi import FastAPI, HTTPException

from utils import enrich_record
from models import (RecordIn, UserCreate, UserLogin)

from database import create_tables

from auth import (create_user, authenticate_user)


app = FastAPI(title="마이 헬스 로그 API", version="1.0")


# 서버 실행 시 테이블 생성
create_tables()


# ==================================
# 기본 API
# ==================================

@app.get("/")
def read_root():
    return {
        "message": "마이 헬스 로그 API"
    }


# ==================================
# 회원가입 / 로그인
# ==================================

# 회원가입
@app.post("/auth/signup")
def signup(user: UserCreate):

    result = create_user(
        username=user.username,
        password=user.password,
        name=user.name
    )

    if result is None:
        raise HTTPException(
            status_code=400,
            detail="이미 존재하는 사용자입니다."
        )

    return {
        "message": "회원가입 성공",
        "user": result
    }



# 로그인
@app.post("/auth/login")
def login(user: UserLogin):

    result = authenticate_user(
        username=user.username,
        password=user.password
    )

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="아이디 또는 비밀번호가 올바르지 않습니다."
        )

    return {
        "message": "로그인 성공",
        "user": result
    }



# ==================================
# 건강 기록 API
# ==================================

# 현재 임시 메모리 저장
# (나중에 user_id 연결하면서 DB 저장으로 변경)
records = []

next_id = 1



# 건강 기록 추가
@app.post("/records")
def create_record(record: RecordIn):

    global next_id


    new_record = record.model_dump()

    new_record["id"] = next_id


    # BMI / 혈압 / 혈당 분석 추가
    new_record = enrich_record(
        new_record
    )


    records.append(new_record)

    next_id += 1


    return new_record



# 전체 건강 기록 조회
@app.get("/records")
def get_records():

    return {
        "count": len(records),
        "records": records
    }



# 특정 건강 기록 조회
@app.get("/records/{record_id}")
def get_record(record_id: int):

    for record in records:

        if record["id"] == record_id:
            return record


    raise HTTPException(
        status_code=404,
        detail="해당 기록을 찾을 수 없습니다."
    )



# 건강 기록 수정
@app.put("/records/{record_id}")
def update_record(
    record_id: int,
    record: RecordIn
):

    for index, old_record in enumerate(records):

        if old_record["id"] == record_id:


            updated_record = record.model_dump()

            updated_record["id"] = record_id


            updated_record = enrich_record(
                updated_record
            )


            records[index] = updated_record


            return updated_record


    raise HTTPException(
        status_code=404,
        detail="해당 기록을 찾을 수 없습니다."
    )



# 건강 기록 삭제
@app.delete("/records/{record_id}")
def delete_record(record_id: int):

    for index, record in enumerate(records):

        if record["id"] == record_id:

            deleted = records.pop(index)

            return {
                "message": "삭제되었습니다.",
                "deleted": deleted
            }


    raise HTTPException(
        status_code=404,
        detail="해당 기록을 찾을 수 없습니다."
    )



# ==================================
# 통계 API
# ==================================

@app.get("/stats")
def get_stats():

    if not records:

        return {
            "count": 0,
            "avg_weight": None,
            "avg_bmi": None,
            "avg_systolic": None,
            "avg_diastolic": None,
            "avg_blood_sugar": None
        }


    count = len(records)


    return {

        "count": count,

        "avg_weight":
            round(
                sum(r["weight"] for r in records) / count,
                2
            ),

        "avg_bmi":
            round(
                sum(r["bmi"] for r in records) / count,
                2
            ),

        "avg_systolic":
            round(
                sum(r["systolic"] for r in records) / count,
                2
            ),

        "avg_diastolic":
            round(
                sum(r["diastolic"] for r in records) / count,
                2
            ),

        "avg_blood_sugar":
            round(
                sum(r["blood_sugar"] for r in records) / count,
                2
            )
    }