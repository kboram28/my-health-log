from fastapi import FastAPI, HTTPException, Depends

from models import (RecordIn, UserCreate, UserLogin, Token)

from database import create_tables

from auth import (create_user, authenticate_user)
from security import create_access_token
from dependencies import get_current_user
import records as records_crud


app = FastAPI(title="마이 헬스 로그 API", version="1.0")


create_tables()


@app.get("/")
def read_root():
    return {"message": "마이 헬스 로그 API"}


@app.post("/auth/signup")
def signup(user: UserCreate):
    result = create_user(
        email=user.email,
        password=user.password,
        name=user.name
    )

    if result is None:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    return {"message": "회원가입 성공", "user": result}


@app.post("/auth/login")
def login(user: UserLogin):
    result = authenticate_user(
        email=user.email,
        password=user.password
    )

    if result is None:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    # JWT에는 사용자 id(sub)와 role을 담아 이후 인증/권한 체크에 사용
    access_token = create_access_token(
        data={"sub": str(result["id"]), "role": result["role"]}
    )

    return {
        "message": "로그인 성공",
        "user": result,
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.post("/records")
def add_record(
    record: RecordIn,
    current_user: dict = Depends(get_current_user)
):
    saved = records_crud.create_record(current_user["id"], record.model_dump())
    return {"message": "기록이 추가되었습니다", "record": saved}


@app.get("/records")
def list_records(current_user: dict = Depends(get_current_user)):
    items = records_crud.get_records(current_user["id"])
    return {"count": len(items), "records": items}


@app.get("/records/{record_id}")
def get_record_detail(
    record_id: int,
    current_user: dict = Depends(get_current_user)
):
    record = records_crud.get_record(record_id, current_user["id"])
    if record is None:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    return record


@app.put("/records/{record_id}")
def update_record_detail(
    record_id: int,
    record: RecordIn,
    current_user: dict = Depends(get_current_user)
):
    updated = records_crud.update_record(record_id, current_user["id"], record.model_dump())
    if updated is None:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    return {"message": "기록이 수정되었습니다", "record": updated}


@app.delete("/records/{record_id}")
def delete_record_detail(
    record_id: int,
    current_user: dict = Depends(get_current_user)
):
    deleted = records_crud.delete_record(record_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    return {"message": "기록이 삭제되었습니다"}


@app.get("/search")
def search_records(
    start: str,
    end: str,
    current_user: dict = Depends(get_current_user)
):
    items = records_crud.search_records(current_user["id"], start, end)
    return {"count": len(items), "records": items}


@app.get("/stats")
def get_stats(current_user: dict = Depends(get_current_user)):
    print("Current user:", current_user)  # Debugging line  
    return records_crud.get_stats(current_user["id"])