import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="마이 헬스 로그 API", version="1.0")

DATA_FILE = "data.json"


# ────────────────────────────────
# 파일 저장 / 불러오기 함수
# ────────────────────────────────

def load_records():
    """서버 시작할 때 data.json이 있으면 불러오고, 없으면 빈 리스트로 시작"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_records():
    """현재 records를 data.json에 저장"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


records = load_records()
# 서버 재시작 시 next_id도 기존 데이터 기준으로 이어서 부여
next_id = max([r["id"] for r in records], default=0) + 1


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


# ────────────────────────────────
# BMI / 혈압 / 혈당 계산 & 분류 함수들
# ────────────────────────────────

def calculate_bmi(weight: float, height: float) -> float:
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    return round(bmi, 2)


def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "저체중"
    elif bmi < 23:
        return "정상"
    elif bmi < 25:
        return "과체중"
    else:
        return "비만"


def classify_bp(systolic: int, diastolic: int) -> str:
    if systolic >= 140 or diastolic >= 90:
        return "고혈압"
    elif systolic >= 120 or diastolic >= 80:
        return "주의"
    else:
        return "정상"


def classify_sugar(blood_sugar: int) -> str:
    if blood_sugar >= 126:
        return "당뇨 의심"
    elif blood_sugar >= 100:
        return "공복혈당장애"
    else:
        return "정상"


def generate_warnings(bmi_category: str, bp_category: str, sugar_category: str) -> list:
    warnings = []
    if bmi_category == "비만":
        warnings.append("BMI가 비만 범위입니다. 체중 관리가 필요할 수 있습니다.")
    if bp_category == "고혈압":
        warnings.append("혈압이 고혈압 범위입니다. 전문가 상담을 권장합니다.")
    if sugar_category == "당뇨 의심":
        warnings.append("혈당 수치가 당뇨 의심 범위입니다. 전문가 상담을 권장합니다.")
    return warnings


def enrich_record(record: dict) -> dict:
    bmi = calculate_bmi(record["weight"], record["height"])
    bmi_category = classify_bmi(bmi)
    bp_category = classify_bp(record["systolic"], record["diastolic"])
    sugar_category = classify_sugar(record["blood_sugar"])
    warnings = generate_warnings(bmi_category, bp_category, sugar_category)

    record["bmi"] = bmi
    record["bmi_category"] = bmi_category
    record["bp_category"] = bp_category
    record["sugar_category"] = sugar_category
    record["warnings"] = warnings
    return record


@app.get("/")
def read_root():
    return {"message": "마이 헬스 로그 API"}


# POST /records : 기록 추가 (BMI/분류/경고 자동 계산 + 파일 저장)
@app.post("/records")
def create_record(record: RecordIn):
    global next_id
    new_record = record.model_dump()
    new_record["id"] = next_id
    new_record = enrich_record(new_record)
    records.append(new_record)
    next_id += 1
    save_records()
    return new_record


# GET /records : 전체 조회 (개수 포함)
@app.get("/records")
def get_records():
    return {"count": len(records), "records": records}


# GET /search : 날짜 범위(start, end)로 검색
@app.get("/search")
def search_records(start: str, end: str):
    result = [r for r in records if start <= r["date"] <= end]
    return {"count": len(result), "records": result}


# GET /stats : 평균 체중 등 통계 반환
@app.get("/stats")
def get_stats():
    if not records:
        return {
            "count": 0,
            "avg_weight": None,
            "avg_bmi": None,
            "avg_systolic": None,
            "avg_diastolic": None,
            "avg_blood_sugar": None,
        }

    count = len(records)
    avg_weight = round(sum(r["weight"] for r in records) / count, 2)
    avg_bmi = round(sum(r["bmi"] for r in records) / count, 2)
    avg_systolic = round(sum(r["systolic"] for r in records) / count, 2)
    avg_diastolic = round(sum(r["diastolic"] for r in records) / count, 2)
    avg_blood_sugar = round(sum(r["blood_sugar"] for r in records) / count, 2)

    return {
        "count": count,
        "avg_weight": avg_weight,
        "avg_bmi": avg_bmi,
        "avg_systolic": avg_systolic,
        "avg_diastolic": avg_diastolic,
        "avg_blood_sugar": avg_blood_sugar,
    }


# GET /records/{record_id} : 단건 조회 (없으면 404)
@app.get("/records/{record_id}")
def get_record(record_id: int):
    for r in records:
        if r["id"] == record_id:
            return r
    raise HTTPException(status_code=404, detail="해당 id의 기록을 찾을 수 없습니다.")


# PUT /records/{record_id} : 기록 수정 (+ 파일 저장)
@app.put("/records/{record_id}")
def update_record(record_id: int, record: RecordIn):
    for i, r in enumerate(records):
        if r["id"] == record_id:
            updated_record = record.model_dump()
            updated_record["id"] = record_id
            updated_record = enrich_record(updated_record)
            records[i] = updated_record
            save_records()
            return updated_record
    raise HTTPException(status_code=404, detail="해당 id의 기록을 찾을 수 없습니다.")


# DELETE /records/{record_id} : 삭제 (+ 파일 저장)
@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    for i, r in enumerate(records):
        if r["id"] == record_id:
            deleted = records.pop(i)
            save_records()
            return {"message": "삭제되었습니다.", "deleted": deleted}
    raise HTTPException(status_code=404, detail="해당 id의 기록을 찾을 수 없습니다.")