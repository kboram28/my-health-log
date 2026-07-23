from datetime import date, timedelta

from database import get_connection


def _period_avg(user_id: int, start_date: str, end_date: str):
    """start_date <= date <= end_date 범위의 평균값들, 기록 없으면 None들"""
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
        WHERE user_id = ? AND date >= ? AND date <= ?
        """,
        (user_id, start_date, end_date)
    )
    row = cursor.fetchone()
    conn.close()

    if row["count"] == 0:
        return None

    return {
        "count": row["count"],
        "avg_weight": round(row["avg_weight"], 2),
        "avg_bmi": round(row["avg_bmi"], 2),
        "avg_systolic": round(row["avg_systolic"], 2),
        "avg_diastolic": round(row["avg_diastolic"], 2),
        "avg_blood_sugar": round(row["avg_blood_sugar"], 2),
    }


def get_weekly_report(user_id: int) -> dict:
    """
    주간 리포트 (FR-14, FR-15)
    - 오늘(서버 기준 날짜)로부터 최근 7일 평균
    - 그 직전 7일과 비교한 증감
    """
    today = date.today()

    this_week_start = today - timedelta(days=6)
    last_week_end = this_week_start - timedelta(days=1)
    last_week_start = last_week_end - timedelta(days=6)

    this_week = _period_avg(user_id, this_week_start.isoformat(), today.isoformat())
    last_week = _period_avg(user_id, last_week_start.isoformat(), last_week_end.isoformat())

    result = {
        "period": {
            "this_week": f"{this_week_start.isoformat()} ~ {today.isoformat()}",
            "last_week": f"{last_week_start.isoformat()} ~ {last_week_end.isoformat()}",
        },
        "this_week": this_week,
        "last_week": last_week,
    }

    if this_week is None:
        result["message"] = "최근 7일 이내 기록이 없어 주간 리포트를 계산할 수 없습니다."
        result["change"] = None
        return result

    if last_week is None:
        result["message"] = "지난주 기록이 없어 전주 대비 변화는 계산할 수 없습니다."
        result["change"] = None
        return result

    def diff(key):
        return round(this_week[key] - last_week[key], 2)

    result["change"] = {
        "weight": diff("avg_weight"),
        "bmi": diff("avg_bmi"),
        "systolic": diff("avg_systolic"),
        "diastolic": diff("avg_diastolic"),
        "blood_sugar": diff("avg_blood_sugar"),
    }

    return result


def get_sleep_analysis(user_id: int) -> dict:
    """
    수면 분석 (FR-17)
    - 전체 기록의 평균 수면 시간과 권장 수면 시간(7~9시간) 비교
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as count, AVG(sleep_hours) as avg_sleep FROM records WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row["count"] == 0:
        return {
            "count": 0,
            "avg_sleep_hours": None,
            "status": None,
            "message": "아직 건강 기록이 없어 수면 분석을 할 수 없습니다.",
        }

    avg_sleep = round(row["avg_sleep"], 2)

    if avg_sleep < 7:
        status = "부족"
    elif avg_sleep <= 9:
        status = "적정"
    else:
        status = "과다"

    return {
        "count": row["count"],
        "avg_sleep_hours": avg_sleep,
        "recommended_range": "7~9시간",
        "status": status,
    }