from fastapi import FastAPI, HTTPException, Depends

from models import (RecordIn, UserCreate, UserLogin, Token, GoalIn)
from database import create_tables
from auth import (create_user, authenticate_user)
from security import create_access_token
from dependencies import get_current_user, get_current_admin_user
import records as records_crud
import admin as admin_crud
import goals as goals_crud
import reports as reports_crud
from web import router as web_router


app = FastAPI(title="마이 헬스 로그 API", version="1.0")

create_tables()
app.include_router(web_router)


@app.get("/")
def read_root():
    return {"message": "마이 헬스 로그 API"}


@app.post("/auth/signup")
def signup(user: UserCreate):
    result = create_user(email=user.email, password=user.password, name=user.name)
    if result is None:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    return {"message": "회원가입 성공", "user": result}


@app.post("/auth/login")
def login(user: UserLogin):
    result = authenticate_user(email=user.email, password=user.password)
    if result is None:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    access_token = create_access_token(data={"sub": str(result["id"]), "role": result["role"]})

    return {"message": "로그인 성공", "user": result, "access_token": access_token, "token_type": "bearer"}


@app.post("/records")
def add_record(record: RecordIn, current_user: dict = Depends(get_current_user)):
    saved = records_crud.create_record(current_user["id"], record.model_dump())
    return {"message": "기록이 추가되었습니다", "record": saved}


@app.get("/records")
def list_records(current_user: dict = Depends(get_current_user)):
    items = records_crud.get_records(current_user["id"])
    return {"count": len(items), "records": items}


@app.get("/records/{record_id}")
def get_record_detail(record_id: int, current_user: dict = Depends(get_current_user)):
    record = records_crud.get_record(record_id, current_user["id"])
    if record is None:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    return record


@app.put("/records/{record_id}")
def update_record_detail(record_id: int, record: RecordIn, current_user: dict = Depends(get_current_user)):
    updated = records_crud.update_record(record_id, current_user["id"], record.model_dump())
    if updated is None:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    return {"message": "기록이 수정되었습니다", "record": updated}


@app.delete("/records/{record_id}")
def delete_record_detail(record_id: int, current_user: dict = Depends(get_current_user)):
    deleted = records_crud.delete_record(record_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    return {"message": "기록이 삭제되었습니다"}


@app.get("/search")
def search_records(start: str, end: str, current_user: dict = Depends(get_current_user)):
    items = records_crud.search_records(current_user["id"], start, end)
    return {"count": len(items), "records": items}


@app.get("/stats")
def get_stats(current_user: dict = Depends(get_current_user)):
    return records_crud.get_stats(current_user["id"])


# ==================================
# 관리자 전용 API (FR-19~21)
# ==================================

@app.get("/admin/users")
def admin_list_users(current_admin: dict = Depends(get_current_admin_user)):
    users = admin_crud.get_all_users()
    return {"count": len(users), "users": users}


@app.get("/admin/users/{user_id}/records")
def admin_get_user_records(
    user_id: int,
    current_admin: dict = Depends(get_current_admin_user)
):
    records = admin_crud.get_user_records(user_id)
    if records is None:
        raise HTTPException(status_code=404, detail="해당 사용자를 찾을 수 없습니다.")
    return {"user_id": user_id, "count": len(records), "records": records}


@app.delete("/admin/users/{user_id}/records/{record_id}")
def admin_delete_user_record(
    user_id: int,
    record_id: int,
    current_admin: dict = Depends(get_current_admin_user)
):
    deleted = admin_crud.admin_delete_record(user_id, record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="해당 기록을 찾을 수 없습니다.")
    return {"message": "관리자 권한으로 기록이 삭제되었습니다."}


@app.get("/admin/stats")
def admin_service_stats(current_admin: dict = Depends(get_current_admin_user)):
    return admin_crud.get_service_stats()

# ==================================
# 목표 관리 (FR-12, FR-13)
# ==================================

@app.post("/goals")
def set_goal(goal: GoalIn, current_user: dict = Depends(get_current_user)):
    result = goals_crud.set_goal(
        current_user["id"],
        goal.target_weight,
        goal.target_systolic,
        goal.target_diastolic,
    )
    return {"message": "목표가 저장되었습니다.", "goal": result}


@app.get("/goals/progress")
def get_goal_progress(current_user: dict = Depends(get_current_user)):
    return goals_crud.get_goal_progress(current_user["id"])


# ==================================
# 주간 리포트 (FR-14, FR-15)
# ==================================

@app.get("/reports/weekly")
def weekly_report(current_user: dict = Depends(get_current_user)):
    return reports_crud.get_weekly_report(current_user["id"])


@app.get("/reports/sleep")
def sleep_analysis(current_user: dict = Depends(get_current_user)):
    return reports_crud.get_sleep_analysis(current_user["id"])