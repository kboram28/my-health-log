from database import get_connection
from utils import classify_activity

# ────────────────────────────────
# 관리자 전용 로직 (FR-19~21)
# ────────────────────────────────

def get_all_users() -> list:
    """전체 사용자 목록 + 각자 기록 개수"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            u.id, u.email, u.name, u.role, u.created_at,
            COUNT(r.id) as record_count
        FROM users u
        LEFT JOIN records r ON r.user_id = u.id
        GROUP BY u.id
        ORDER BY u.created_at ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_records(user_id: int):
    """특정 사용자의 존재 확인 + 기록 목록 반환 (사용자 없으면 None)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
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
    """관리자가 특정 사용자의 특정 기록을 삭제"""
    conn = get_connection()
    cursor = conn.cursor()

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