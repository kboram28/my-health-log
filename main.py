from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="마이 헬스 로그 API", version="1.0")

# 일단 메모리(리스트)에 저장. 나중에 파일 저장으로 발전시킬 예정
records = []
next_id = 1  # 기록마다 고유 id를 붙이기 위한 카운터


# 요청 본문 검증용 Pydantic 모델
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


@app.get("/")
def read_root():
    return {"message": "마이 헬스 로그 API"}


# POST /records : 기록 추가
@app.post("/records")
def create_record(record: RecordIn):
    global next_id
    new_record = record.model_dump()
    new_record["id"] = next_id
    records.append(new_record)
    next_id += 1
    return new_record


# GET /records : 전체 조회 (개수 포함)
@app.get("/records")
def get_records():
    return {"count": len(records), "records": records}


# GET /records/{record_id} : 단건 조회 (없으면 404)
@app.get("/records/{record_id}")
def get_record(record_id: int):
    for r in records:
        if r["id"] == record_id:
            return r
    raise HTTPException(status_code=404, detail="해당 id의 기록을 찾을 수 없습니다.")


# DELETE /records/{record_id} : 삭제
@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    for i, r in enumerate(records):
        if r["id"] == record_id:
            deleted = records.pop(i)
            return {"message": "삭제되었습니다.", "deleted": deleted}
    raise HTTPException(status_code=404, detail="해당 id의 기록을 찾을 수 없습니다.")