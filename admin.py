from database import get_connection
from utils import classify_activity

# ────────────────────────────────
# 관리자 전용 로직 (FR-19~21)
# ────────────────────────────────

def get_all_users() -> list:
    """관리 대상인 일반 사용자 목록 + 각자 기록 개수 (관리자 계정은 제외)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            u.id, u.email, u.name, u.role, u.created_at,
            COUNT(r.id) as record_count
        FROM users u
        LEFT JOIN records r ON r.user_id = u.id
        WHERE u.role = 'user'
        GROUP BY u.id
        ORDER BY u.created_at ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_records(user_id: int):
    """
    특정 (일반) 사용자의 기록 목록 반환
    - 사용자가 없거나, 그 사용자가 관리자 계정이면 None (관리 대상이 아님)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, role FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if target is None or target["role"] != "user":
        conn.close()
        return None

    cursor.execute(
        "SELECT * FROM records WHERE user_id = ? ORDER BY date DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    import json
    result = []
    for r in rows:
        record = dict(r)
        record["warnings"] = json.loads(record["warnings"]) if record["warnings"] else []
        record["activity_level"] = classify_activity(record["steps"])
        result.append(record)
    return result


def admin_delete_record(user_id: int, record_id: int) -> bool:
    """관리자가 특정 (일반) 사용자의 특정 기록을 삭제 - 대상이 관리자 계정이면 거부"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if target is None or target["role"] != "user":
        conn.close()
        return False

    cursor.execute(
        "SELECT id FROM records WHERE id = ? AND user_id = ?",
        (record_id, user_id)
    )
    if cursor.fetchone() is None:
        conn.close()
        return False

    cursor.execute(
        "DELETE FROM records WHERE id = ? AND user_id = ?",
        (record_id, user_id)
    )
    conn.commit()
    conn.close()
    return True


def get_daily_record_counts(days: int = 14) -> list:
    """
    최근 N일간 전체 서비스에 등록된 기록 수 추이 (관리자 대시보드 선 그래프용)
    - 기록이 없는 날짜도 0으로 채워서 반환 (그래프에서 빈 구간이 안 생기도록)
    """
    from datetime import date, timedelta

    end = date.today()
    start = end - timedelta(days=days - 1)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT date, COUNT(*) as count
        FROM records
        WHERE date >= ? AND date <= ?
        GROUP BY date
        """,
        (start.isoformat(), end.isoformat())
    )
    counts_by_date = {row["date"]: row["count"] for row in cursor.fetchall()}
    conn.close()

    result = []
    for i in range(days):
        d = (start + timedelta(days=i)).isoformat()
        result.append({"date": d, "count": counts_by_date.get(d, 0)})
    return result


def get_warning_summary() -> dict:
    """
    각 (일반) 사용자의 가장 최근 기록 기준으로 비만/고혈압/당뇨의심 인원 집계
    (관리자 대시보드 막대 그래프용 - 관리자 계정은 집계에서 제외)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT r.bmi_category, r.bp_category, r.sugar_category
        FROM records r
        INNER JOIN users u ON u.id = r.user_id
        INNER JOIN (
            SELECT user_id, MAX(date) as max_date FROM records GROUP BY user_id
        ) latest ON r.user_id = latest.user_id AND r.date = latest.max_date
        WHERE u.role = 'user'
        """
    )
    rows = cursor.fetchall()
    conn.close()

    return {
        "total_evaluated": len(rows),
        "obesity": sum(1 for r in rows if r["bmi_category"] == "비만"),
        "hypertension": sum(1 for r in rows if r["bp_category"] == "고혈압"),
        "diabetes_risk": sum(1 for r in rows if r["sugar_category"] == "당뇨 의심"),
    }


def get_service_stats() -> dict:
    """서비스 전체 통계"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as c FROM users")
    total_users = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(*) as c FROM users WHERE role = 'admin'")
    total_admins = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(*) as c FROM records")
    total_records = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(DISTINCT user_id) as c FROM records")
    users_with_records = cursor.fetchone()["c"]

    conn.close()

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "general_users": total_users - total_admins,
        "total_records": total_records,
        "users_with_at_least_one_record": users_with_records,
    }