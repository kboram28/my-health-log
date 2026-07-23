from datetime import datetime

from database import get_connection


def set_goal(user_id: int, target_weight, target_systolic, target_diastolic) -> dict:
    """
    목표 설정 (FR-12)
    - 이미 목표가 있으면 갱신(upsert), 없으면 새로 생성
    """
    conn = get_connection()
    cursor = conn.cursor()
    updated_at = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO goals (user_id, target_weight, target_systolic, target_diastolic, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            target_weight = excluded.target_weight,
            target_systolic = excluded.target_systolic,
            target_diastolic = excluded.target_diastolic,
            updated_at = excluded.updated_at
        """,
        (user_id, target_weight, target_systolic, target_diastolic, updated_at)
    )
    conn.commit()
    conn.close()

    return get_goal(user_id)


def get_goal(user_id: int):
    """현재 설정된 목표 조회 (없으면 None)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def _latest_record(user_id: int):
    """가장 최근(날짜 기준) 기록 1건"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM records WHERE user_id = ? ORDER BY date DESC LIMIT 1",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_goal_progress(user_id: int) -> dict:
    """
    목표 달성률 조회 (FR-13)

    - 체중: 최근 기록이 목표에 얼마나 가까운지를 %로 환산
        achievement(%) = 100 - |현재-목표| / 목표 * 100  (0~100 범위로 자름)
    - 혈압: 최근 기록의 수축기/이완기가 목표 이하이면 "달성", 아니면 "미달성"
      (혈압은 방향성 있는 수치를 %로 나타내는 게 부적절해 달성/미달성으로 판단)
    """
    goal = get_goal(user_id)
    if goal is None:
        return {
            "has_goal": False,
            "message": "설정된 목표가 없습니다. 먼저 목표를 설정해주세요.",
        }

    latest = _latest_record(user_id)
    if latest is None:
        return {
            "has_goal": True,
            "goal": goal,
            "message": "아직 건강 기록이 없어 달성률을 계산할 수 없습니다.",
        }

    result = {
        "has_goal": True,
        "goal": goal,
        "latest_record_date": latest["date"],
    }

    if goal["target_weight"] is not None:
        current_weight = latest["weight"]
        target_weight = goal["target_weight"]
        diff_ratio = abs(current_weight - target_weight) / target_weight * 100
        achievement = max(0, min(100, round(100 - diff_ratio, 1)))
        result["weight_achievement_percent"] = achievement
        result["current_weight"] = current_weight

    if goal["target_systolic"] is not None or goal["target_diastolic"] is not None:
        systolic_ok = (
            goal["target_systolic"] is None or latest["systolic"] <= goal["target_systolic"]
        )
        diastolic_ok = (
            goal["target_diastolic"] is None or latest["diastolic"] <= goal["target_diastolic"]
        )
        result["bp_goal_status"] = "달성" if (systolic_ok and diastolic_ok) else "미달성"
        result["current_bp"] = f'{latest["systolic"]}/{latest["diastolic"]}'

    return result