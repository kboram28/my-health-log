# 마이 헬스 로그 API

매일의 체중·키·혈압·혈당을 기록하면 BMI를 자동으로 계산하고, 혈압/혈당 상태를 분류해 경고를 알려주는 개인 건강 기록 관리 API입니다. 누구나 매일 자신의 건강 수치를 간단히 기록하고, 쌓인 기록으로 평균 추이를 확인할 수 있도록 돕습니다.

> ⚠️ 이 프로젝트의 건강 기준(BMI/혈압/혈당 분류)은 학습을 위해 단순화한 값이며, 실제 의학적 진단이 아닙니다.

## 기능 목록

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/` | API 실행 확인용 루트 |
| POST | `/records` | 건강 기록 추가 (BMI·분류·경고 자동 계산) |
| GET | `/records` | 전체 기록 조회 (개수 포함) |
| GET | `/records/{record_id}` | 기록 단건 조회 (없으면 404) |
| PUT | `/records/{record_id}` | 기록 수정 |
| DELETE | `/records/{record_id}` | 기록 삭제 |
| GET | `/search?start=...&end=...` | 날짜 범위로 기록 검색 |
| GET | `/stats` | 평균 체중·BMI·혈압·혈당 등 통계 조회 |

### 기록에 자동으로 포함되는 계산 값

- `bmi`, `bmi_category` (저체중 / 정상 / 과체중 / 비만)
- `bp_category` (정상 / 주의 / 고혈압)
- `sugar_category` (정상 / 공복혈당장애 / 당뇨 의심)
- `warnings` (비만·고혈압·당뇨 의심일 때 해당 경고 메시지 목록, 없으면 빈 배열)

## 기술 스택

- **Python 3.13** (로컬 실행 기준) / **Python 3.11** (Docker 이미지 기준: `python:3.11-slim`)
- **FastAPI** – REST API 프레임워크
- **Uvicorn** – ASGI 서버
- **Pydantic** – 요청 데이터 검증
- **JSON 파일 저장** – 서버 재시작 후에도 데이터 유지
- **Docker** – 컨테이너 실행

## 실행 방법

### 1) 로컬 실행

```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac / Linux

# 패키지 설치
pip install -r requirements.txt

# 서버 실행
uvicorn main:app --reload
```

브라우저에서 `http://127.0.0.1:8000/docs` 접속하면 API를 바로 테스트할 수 있습니다.

### 2) Docker 실행

```bash
# 이미지 빌드
docker build -t health-log-api .

# 컨테이너 실행 (호스트 8001번 포트 사용 예시)
docker run -d -p 8001:8000 --name health-log-container health-log-api
```

브라우저에서 `http://127.0.0.1:8001/docs` 접속하면 컨테이너로 실행된 API를 테스트할 수 있습니다.

## 예시 요청

```json
POST /records
{
  "date": "2026-07-20",
  "weight": 70,
  "height": 175,
  "systolic": 120,
  "diastolic": 80,
  "blood_sugar": 95,
  "steps": 8000,
  "sleep_hours": 7.5,
  "memo": "컨디션 좋음"
}
```

## 배포 접속 URL

로컬 / Docker 환경에서 실행하며, 별도의 클라우드 배포는 진행하지 않았습니다.
(배포 시 아래에 접속 URL을 추가합니다: `http://<서버 IP>:8000/docs`)

## 참고

FastAPI 수업자료 및 실습 워크북을 참고하여 작성했습니다.