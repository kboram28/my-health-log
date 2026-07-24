import calendar as calendar_module
from datetime import date

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from auth import authenticate_user, create_user, get_user_by_id, delete_user
import auth as auth_module
from security import create_access_token
from dependencies import get_current_user_from_cookie
from models import RecordIn
from models import RecordIn, UserCreate
import records as records_crud
import admin as admin_crud
import goals as goals_crud
import reports as reports_crud


router = APIRouter()
templates = Jinja2Templates(directory="templates")

COOKIE_MAX_AGE = 60 * 60 * 24


def _redirect_by_role(user: dict) -> RedirectResponse:
    target = "/web/admin" if user["role"] == "admin" else "/web/records"
    return RedirectResponse(url=target, status_code=303)


# ────────────────────────────────
# 인증
# ────────────────────────────────

@router.get("/web/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.get("/web/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.get("/web/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html", {"error": None, "form_values": None})


@router.get("/web/check-email")
def web_check_email(email: str):
    return {"available": not auth_module.email_exists(email)}


@router.post("/web/signup")
def signup_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    name: str = Form(...),
    phone: str = Form(...)
):
    submitted = {
        "email": email, "password": password, "password_confirm": password_confirm,
        "name": name, "phone": phone,
    }
    try:
        validated = UserCreate(**submitted)
    except ValidationError as e:
        first_error = e.errors()[0]
        message = first_error["msg"]
        form_values = {k: v for k, v in submitted.items() if k not in ("password", "password_confirm")}
        return templates.TemplateResponse(
            request, "signup.html",
            {"error": message, "form_values": form_values},
            status_code=400
        )
    result = create_user(
        email=validated.email, password=validated.password,
        name=validated.name, phone=validated.phone
    )
    if result is None:
        form_values = {"email": email, "name": name, "phone": phone}
        return templates.TemplateResponse(
            request, "signup.html",
            {"error": "이미 존재하는 이메일입니다.", "form_values": form_values},
            status_code=400
        )
    token = create_access_token(data={"sub": str(result["id"]), "role": result["role"]})
    response = _redirect_by_role(result)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=COOKIE_MAX_AGE)
    return response


@router.post("/web/login")
def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    user = authenticate_user(email=email, password=password)
    if user is None:
        return templates.TemplateResponse(
            request, "login.html", {"error": "이메일 또는 비밀번호가 올바르지 않습니다."}, status_code=401
        )

    token = create_access_token(data={"sub": str(user["id"]), "role": user["role"]})
    response = _redirect_by_role(user)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=COOKIE_MAX_AGE)
    return response


@router.get("/web/logout")
def logout():
    response = RedirectResponse(url="/web/login", status_code=303)
    response.delete_cookie("access_token")
    return response


# ────────────────────────────────
# 탭 1: 기록 추가
# ────────────────────────────────

@router.get("/web/records/add", response_class=HTMLResponse)
def records_add_page(request: Request):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)
    if user["role"] == "admin":
        return RedirectResponse(url="/web/admin", status_code=303)

    return templates.TemplateResponse(
        request, "records_add.html",
        {
            "user": user, "error": None, "form_values": None,
            "today": date.today().isoformat(), "active_tab": "add",
        }
    )


@router.post("/web/records/add")
def records_add_submit(
    request: Request,
    date_: str = Form(..., alias="date"),
    weight: float = Form(...),
    height: float = Form(...),
    systolic: int = Form(...),
    diastolic: int = Form(...),
    blood_sugar: int = Form(...),
    steps: int = Form(0),
    sleep_hours: float = Form(0.0),
    memo: str = Form("")
):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)

    submitted = {
        "date": date_, "weight": weight, "height": height,
        "systolic": systolic, "diastolic": diastolic, "blood_sugar": blood_sugar,
        "steps": steps, "sleep_hours": sleep_hours, "memo": memo
    }

    try:
        validated = RecordIn(**submitted)
    except ValidationError as e:
        field_labels = {
            "date": "날짜", "weight": "체중", "height": "키",
            "systolic": "수축기 혈압", "diastolic": "이완기 혈압",
            "blood_sugar": "혈당", "steps": "걸음 수", "sleep_hours": "수면 시간"
        }
        first_error = e.errors()[0]
        field_name = field_labels.get(first_error["loc"][0], first_error["loc"][0])
        message = f"'{field_name}' 값을 확인해주세요. ({first_error['msg']})"
        return templates.TemplateResponse(
            request, "records_add.html",
            {
                "user": user, "error": message, "form_values": submitted,
                "today": date.today().isoformat(), "active_tab": "add",
            },
            status_code=400
        )

    records_crud.create_record(user["id"], validated.model_dump())
    return RedirectResponse(url="/web/records/add", status_code=303)


# ────────────────────────────────
# 탭 2: 기록 목록
# ────────────────────────────────

@router.get("/web/records", response_class=HTMLResponse)
def records_page(request: Request):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)
    if user["role"] == "admin":
        return RedirectResponse(url="/web/admin", status_code=303)

    items = records_crud.get_records(user["id"])
    return templates.TemplateResponse(
        request, "records.html",
        {"user": user, "records": items, "active_tab": "list"}
    )


@router.post("/web/records/{record_id}/delete")
def records_delete(record_id: int, request: Request):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)

    records_crud.delete_record(record_id, user["id"])
    return RedirectResponse(url="/web/records", status_code=303)


# ────────────────────────────────
# 탭 3: 내 대시보드
# ────────────────────────────────

@router.get("/web/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)
    if user["role"] == "admin":
        return RedirectResponse(url="/web/admin", status_code=303)

    records = records_crud.get_records(user["id"])
    records_sorted = sorted(records, key=lambda r: r["date"])  # 그래프는 오래된 순서로
    stats = records_crud.get_stats(user["id"])
    weekly = reports_crud.get_weekly_report(user["id"])
    sleep = reports_crud.get_sleep_analysis(user["id"])
    goal_progress = goals_crud.get_goal_progress(user["id"])
    goal = goals_crud.get_goal(user["id"])

    return templates.TemplateResponse(
        request, "dashboard.html",
        {
            "user": user, "records": records_sorted, "stats": stats,
            "weekly": weekly, "sleep": sleep, "goal_progress": goal_progress,
            "goal": goal, "active_tab": "dashboard",
        }
    )


@router.post("/web/goals")
def set_goal_submit(
    request: Request,
    target_weight: str = Form(""),
    target_systolic: str = Form(""),
    target_diastolic: str = Form("")
):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)

    tw = float(target_weight) if target_weight.strip() != "" else None
    ts = int(float(target_systolic)) if target_systolic.strip() != "" else None
    td = int(float(target_diastolic)) if target_diastolic.strip() != "" else None

    goals_crud.set_goal(user["id"], tw, ts, td)
    return RedirectResponse(url="/web/dashboard", status_code=303)


# ────────────────────────────────
# 탭 4: 캘린더
# ────────────────────────────────

@router.get("/web/calendar", response_class=HTMLResponse)
def calendar_page(request: Request, year: int | None = None, month: int | None = None):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)
    if user["role"] == "admin":
        return RedirectResponse(url="/web/admin", status_code=303)

    today = date.today()
    year = year or today.year
    month = month or today.month

    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    records = records_crud.get_records_by_month(user["id"], year, month)
    records_by_date = {r["date"]: r for r in records}

    cal = calendar_module.Calendar(firstweekday=6)  # 일요일 시작
    weeks = cal.monthdayscalendar(year, month)

    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

    return templates.TemplateResponse(
        request, "calendar.html",
        {
            "user": user, "year": year, "month": month, "weeks": weeks,
            "records_by_date": records_by_date, "today": today.isoformat(),
            "prev_year": prev_year, "prev_month": prev_month,
            "next_year": next_year, "next_month": next_month,
            "active_tab": "calendar",
        }
    )


# ────────────────────────────────
# 회원 탈퇴
# ────────────────────────────────

@router.post("/web/delete-account")
def delete_account_submit(request: Request, password: str = Form(...)):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)

    verified = authenticate_user(email=user["email"], password=password)
    if verified is None:
        items = records_crud.get_records(user["id"])
        return templates.TemplateResponse(
            request, "records.html",
            {
                "user": user, "records": items,
                "error": "비밀번호가 일치하지 않아 탈퇴가 취소되었습니다.",
                "active_tab": "list",
            },
            status_code=401
        )

    result = delete_user(user["id"])
    if not result["success"]:
        message = (
            "마지막 남은 관리자 계정은 삭제할 수 없습니다."
            if result["reason"] == "last_admin"
            else "탈퇴 처리 중 문제가 발생했습니다."
        )
        items = records_crud.get_records(user["id"])
        return templates.TemplateResponse(
            request, "records.html",
            {"user": user, "records": items, "error": message, "active_tab": "list"},
            status_code=400
        )

    response = RedirectResponse(url="/web/login", status_code=303)
    response.delete_cookie("access_token")
    return response


# ────────────────────────────────
# 관리자 전용 화면 (기존 그대로, 변경 없음)
# ────────────────────────────────

@router.get("/web/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, page: int = 1, search: str = ""):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)
    if user["role"] != "admin":
        return RedirectResponse(url="/web/records", status_code=303)

    result = admin_crud.get_all_users(page=page, page_size=20, search=search)
    stats = admin_crud.get_service_stats()
    daily_counts = admin_crud.get_daily_record_counts(14)
    warning_summary = admin_crud.get_warning_summary()
    top_users = admin_crud.get_top_users_by_records(10)

    return templates.TemplateResponse(
        request, "admin_dashboard.html",
        {
            "user": user,
            "users": result["users"],
            "total_users": result["total"],
            "page": result["page"],
            "total_pages": result["total_pages"],
            "search": search,
            "stats": stats,
            "daily_counts": daily_counts,
            "warning_summary": warning_summary,
            "top_users": top_users,
        }
    )


@router.get("/web/admin/users/{user_id}", response_class=HTMLResponse)
def admin_view_user_records(user_id: int, request: Request):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)
    if user["role"] != "admin":
        return RedirectResponse(url="/web/records", status_code=303)

    target_user = get_user_by_id(user_id)
    if target_user is None:
        return RedirectResponse(url="/web/admin", status_code=303)

    records = admin_crud.get_user_records(user_id)
    return templates.TemplateResponse(
        request, "admin_user_records.html", {"user": user, "target_user": target_user, "records": records}
    )


@router.post("/web/admin/users/{user_id}/records/{record_id}/delete")
def admin_delete_user_record(user_id: int, record_id: int, request: Request):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)
    if user["role"] != "admin":
        return RedirectResponse(url="/web/records", status_code=303)

    admin_crud.admin_delete_record(user_id, record_id)
    return RedirectResponse(url=f"/web/admin/users/{user_id}", status_code=303)