import json

from database import get_connection
from utils import enrich_record
from utils import enrich_record, classify_activity

def _row_to_dict(row) -> dict:
    record = dict(row)
    # warnings는 DB에 JSON 문자열로 저장 → 응답 시 리스트로 복원
    record["warnings"] = json.loads(record["warnings"]) if record["warnings"] else []
    record["activity_level"] = classify_activity(record["steps"])
    return record


# 기록 추가 (FR-05)

def create_record(user_id: int, record_in: dict) -> dict:
    enriched = enrich_record(dict(record_in))  # bmi/분류/경고 계산

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO records
        (
            user_id, date, weight, height, systolic, diastolic, blood_sugar,
            steps, sleep_hours, memo,
            bmi, bmi_category, bp_category, sugar_category, warnings
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            enriched["date"], enriched["weight"], enriched["height"],
            enriched["systolic"], enriched["diastolic"], enriched["blood_sugar"],
            enriched["steps"], enriched["sleep_hours"], enriched["memo"],
            enriched["bmi"], enriched["bmi_category"], enriched["bp_category"],
            enriched["sugar_category"], json.dumps(enriched["warnings"], ensure_ascii=False)
        )
    )

    conn.commit()
    record_id = cursor.lastrowid
    conn.close()

    return get_record(record_id, user_id)


# 전체 기록 조회 - 본인 것만 (FR-06)

def get_records(user_id: int) -> list:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM records WHERE user_id = ? ORDER BY date DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_dict(r) for r in rows]


# 단건 조회 - 본인 소유만 (FR-07)

def get_record(record_id: int, user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM records WHERE id = ? AND user_id = ?",
        (record_id, user_id)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return _row_to_dict(row)



# 수정 - 본인 소유만 (FR-08)

def update_record(record_id: int, user_id: int, record_in: dict):
    # 소유권 확인
    if get_record(record_id, user_id) is None:
        return None

    enriched = enrich_record(dict(record_in))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE records
        SET date = ?, weight = ?, height = ?, systolic = ?, diastolic = ?,
            blood_sugar = ?, steps = ?, sleep_hours = ?, memo = ?,
            bmi = ?, bmi_category = ?, bp_category = ?, sugar_category = ?, warnings = ?
        WHERE id = ? AND user_id = ?
        """,
        (
            enriched["date"], enriched["weight"], enriched["height"],
            enriched["systolic"], enriched["diastolic"], enriched["blood_sugar"],
            enriched["steps"], enriched["sleep_hours"], enriched["memo"],
            enriched["bmi"], enriched["bmi_category"], enriched["bp_category"],
            enriched["sugar_category"], json.dumps(enriched["warnings"], ensure_ascii=False),
            record_id, user_id
        )
    )

    conn.commit()
    conn.close()

    return get_record(record_id, user_id)



# 삭제 - 본인 소유만 (FR-08)

def delete_record(record_id: int, user_id: int) -> bool:
    if get_record(record_id, user_id) is None:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM records WHERE id = ? AND user_id = ?",
        (record_id, user_id)
    )

    conn.commit()
    conn.close()

    return True


# 날짜 범위 검색 - 본인 것만 (FR-09)

def search_records(user_id: int, start: str, end: str) -> list:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM records
        WHERE user_id = ? AND date >= ? AND date <= ?
        ORDER BY date ASC
        """,
        (user_id, start, end)
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_dict(r) for r in rows]


# 통계 조회 - 본인 것만 (FR-10)

def get_stats(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*) as count,
            AVG(weight) as avg_weight,
            AVG(bmi) as avg_bmi,
            AVG(systolic) as avg_systolic,
            AVG(diastolic) as avg_diastolic,
            AVG(blood_sugar) as avg_blood_sugar
        FROM records
        WHERE user_id = ?
        """,
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row["count"] == 0:
        return {
            "count": 0,
            "avg_weight": None,
            "avg_bmi": None,
            "avg_systolic": None,
            "avg_diastolic": None,
            "avg_blood_sugar": None
        }

    return {
        "count": row["count"],
        "avg_weight": round(row["avg_weight"], 2),
        "avg_bmi": round(row["avg_bmi"], 2),
        "avg_systolic": round(row["avg_systolic"], 2),
        "avg_diastolic": round(row["avg_diastolic"], 2),
        "avg_blood_sugar": round(row["avg_blood_sugar"], 2)
    }