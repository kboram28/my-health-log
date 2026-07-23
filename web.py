from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from auth import authenticate_user, create_user, get_user_by_id
from security import create_access_token
from dependencies import get_current_user_from_cookie
from models import RecordIn
import records as records_crud
import admin as admin_crud


router = APIRouter()
templates = Jinja2Templates(directory="templates")

COOKIE_MAX_AGE = 60 * 60 * 24  # 24시간, JWT 만료시간과 맞춤


def _redirect_by_role(user: dict) -> RedirectResponse:
    """역할에 따라 로그인 직후 보낼 화면을 결정 - 관리자는 대시보드로, 일반 사용자는 기록 화면으로"""
    target = "/web/admin" if user["role"] == "admin" else "/web/records"
    return RedirectResponse(url=target, status_code=303)


@router.get("/web/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.get("/web/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html", {"error": None})


@router.post("/web/signup")
def signup_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...)
):
    if len(password) < 8:
        return templates.TemplateResponse(
            request, "signup.html",
            {"error": "비밀번호는 8자 이상이어야 합니다."},
            status_code=400
        )

    result = create_user(email=email, password=password, name=name)
    if result is None:
        return templates.TemplateResponse(
            request, "signup.html",
            {"error": "이미 존재하는 이메일입니다."},
            status_code=400
        )

    # 가입 후 바로 로그인 처리 (다시 로그인 폼 안 거치도록)
    token = create_access_token(data={"sub": str(result["id"]), "role": result["role"]})
    response = _redirect_by_role(result)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=COOKIE_MAX_AGE
    )
    return response


@router.post("/web/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    user = authenticate_user(email=email, password=password)

    if user is None:
        return templates.TemplateResponse(
            request, "login.html",
            {"error": "이메일 또는 비밀번호가 올바르지 않습니다."},
            status_code=401
        )

    token = create_access_token(data={"sub": str(user["id"]), "role": user["role"]})

    response = _redirect_by_role(user)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,   # JS로 접근 불가 (XSS로 토큰 탈취 방지)
        max_age=COOKIE_MAX_AGE
    )
    return response


@router.get("/web/logout")
def logout():
    response = RedirectResponse(url="/web/login", status_code=303)
    response.delete_cookie("access_token")
    return response


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
        {"user": user, "records": items, "error": None, "form_values": None}
    )


@router.post("/web/records")
def records_add(
    request: Request,
    date: str = Form(...),
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
        "date": date, "weight": weight, "height": height,
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
        items = records_crud.get_records(user["id"])
        return templates.TemplateResponse(
            request, "records.html",
            {"user": user, "records": items, "error": message, "form_values": submitted},
            status_code=400
        )

    records_crud.create_record(user["id"], validated.model_dump())
    return RedirectResponse(url="/web/records", status_code=303)


@router.post("/web/records/{record_id}/delete")
def records_delete(record_id: int, request: Request):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)

    records_crud.delete_record(record_id, user["id"])
    return RedirectResponse(url="/web/records", status_code=303)


# ────────────────────────────────
# 관리자 전용 화면
# ────────────────────────────────

@router.get("/web/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    user = get_current_user_from_cookie(request)
    if user is None:
        return RedirectResponse(url="/web/login", status_code=303)
    if user["role"] != "admin":
        return RedirectResponse(url="/web/records", status_code=303)

    users = admin_crud.get_all_users()
    stats = admin_crud.get_service_stats()
    daily_counts = admin_crud.get_daily_record_counts(14)
    warning_summary = admin_crud.get_warning_summary()
    return templates.TemplateResponse(
        request, "admin_dashboard.html",
        {
            "user": user, "users": users, "stats": stats,
            "daily_counts": daily_counts, "warning_summary": warning_summary
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
        request, "admin_user_records.html",
        {"user": user, "target_user": target_user, "records": records}
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