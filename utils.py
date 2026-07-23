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
    record["activity_level"] = classify_activity(record["steps"])
    return record

def classify_activity(steps: int) -> str:
    """걸음 수 기준 활동량 등급 (FR-16)"""
    if steps < 5000:
        return "부족"
    elif steps < 10000:
        return "적정"
    else:
        return "우수"