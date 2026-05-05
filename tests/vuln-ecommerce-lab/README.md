# VulnShop - Vulnerable E-Commerce Lab

Local LLM 에이전트 기반 취약점 분석 파이프라인 테스트를 위한 의도적 취약 이커머스 애플리케이션.

## 아키텍처

- **Backend**: Java 17 + Spring Boot 3.2 + JPA + H2 (in-memory DB)
- **Frontend**: React 18 + TypeScript + Tailwind CSS + Vite
- **Scanner**: Python 3.11+ + httpx + OpenAI-compatible LLM API

## 실행 방법

### 사전 요구사항

```bash
brew install openjdk@17 maven node
pip install -r scanner/requirements.txt
```

### 1. Backend 실행

```bash
cd backend
./mvnw spring-boot:run
```

서버: http://localhost:8080/api  
Swagger UI: http://localhost:8080/api/swagger-ui.html  
H2 Console: http://localhost:8080/api/h2-console (JDBC URL: `jdbc:h2:mem:vulnshopdb`, user: `sa`, password 비워둠)

### 2. Frontend 실행

```bash
cd frontend
npm install
npm run dev
```

http://localhost:5173 에서 접속.

### 3. Scanner 실행

로컬 LLM 서버가 필요합니다 (ollama, vLLM, LM Studio 등 OpenAI-compatible API).

```bash
# ollama 예시
ollama serve
ollama pull llama3:8b

# 스캐너 실행
cd scanner
python -m scanner.main scan --target http://localhost:8080/api

# 특정 분석만 실행
python -m scanner.main analyze --agent idor
python -m scanner.main analyze --agent parameter-tampering
python -m scanner.main analyze --agent privilege-escalation
python -m scanner.main analyze --agent missing-access-control
python -m scanner.main analyze --agent business-logic

# 리포트만 생성
python -m scanner.main report --format html --output ./reports/
```

Scanner 설정은 `scanner/.env` 파일로 오버라이드:

```env
TARGET_URL=http://localhost:8080/api
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3:8b
```

## 테스트 계정

| 역할 | 이메일 | 비밀번호 |
|------|--------|----------|
| Admin | admin@vulnshop.com | admin123 |
| Seller | seller1@vulnshop.com | password123 |
| Seller | seller2@vulnshop.com | password123 |
| Customer | customer1@vulnshop.com | password123 |
| Customer | customer2@vulnshop.com | password123 |

## 의도적 취약점 목록

### 1. IDOR (Insecure Direct Object Reference)

| 엔드포인트 | 설명 |
|-----------|------|
| GET /orders/{id} | 소유자 검증 없이 타인 주문 조회 |
| GET /orders/number/{orderNumber} | 주문번호로 타인 주문 조회 |
| GET /users/{id} | 타인 프로필 조회 |
| PUT /addresses/{id} | 타인 주소 수정 |
| DELETE /reviews/{id} | 타인 리뷰 삭제 |
| GET /payments/{id} | 타인 결제 정보 조회 |
| PUT /cart/items/{itemId} | 타인 장바구니 항목 수정 |
| GET /shipping/order/{orderId} | 타인 배송 정보 조회 |
| PUT /notifications/{id}/read | 타인 알림 읽음 처리 |

### 2. Parameter Tampering

| 엔드포인트 | 설명 |
|-----------|------|
| POST /cart/items?priceOverride=0.01 | 클라이언트가 가격 직접 지정 |
| POST /payments | 클라이언트 전송 금액을 서버가 그대로 신뢰 |

### 3. Privilege Escalation

| 엔드포인트 | 설명 |
|-----------|------|
| PUT /users/{id}/role | 일반 사용자가 역할 변경 가능 |
| 수평적 접근 | customer1이 customer2의 리소스 접근 |

### 4. Missing Function-Level Access Control

| 엔드포인트 | 설명 |
|-----------|------|
| GET /admin/dashboard | 인증만 되면 접근 가능 (역할 검증 없음) |
| GET /admin/users | 일반 고객이 전체 사용자 목록 조회 |
| PUT /orders/{id}/status | 관리자 전용 기능이 역할 검증 없음 |

### 5. Business Logic Flaw

| 시나리오 | 설명 |
|---------|------|
| 쿠폰 다중 적용 | 동일 쿠폰 반복 사용, 여러 쿠폰 중복 적용 |
| 만료 쿠폰 | 사용 제한/기간 검증 우회 가능성 |
| 미구매 리뷰 | 구매하지 않은 상품 리뷰 작성 가능 |
| 재고 초과 | 재고보다 많은 수량 주문 시도 |

## 프로젝트 구조

```
vuln-ecommerce-lab/
├── backend/                     # Spring Boot API
│   └── src/main/java/com/vulnshop/
│       ├── config/              # 설정, 시드 데이터
│       ├── controller/          # REST 컨트롤러 (14개)
│       ├── dto/                 # 요청/응답 DTO (38개)
│       ├── entity/              # JPA 엔티티 (25개)
│       ├── exception/           # 예외 처리
│       ├── repository/          # 데이터 접근 (15개)
│       ├── security/            # JWT, 필터, 설정
│       └── service/             # 비즈니스 로직 (13개)
├── frontend/                    # React SPA
│   └── src/
│       ├── components/          # 재사용 컴포넌트 (43개)
│       ├── pages/               # 페이지 (18개)
│       ├── services/            # API 클라이언트 (12개)
│       ├── hooks/               # 커스텀 훅
│       ├── context/             # 인증 컨텍스트
│       └── types/               # TypeScript 타입
└── scanner/                     # LLM 취약점 분석기
    ├── agents/                  # 분석 에이전트 (5종)
    ├── crawlers/                # API 크롤러
    ├── reporters/               # 리포트 생성기 (HTML/JSON/SARIF)
    ├── models/                  # 데이터 모델
    ├── utils/                   # HTTP/LLM 클라이언트
    └── tests/                   # 유닛 테스트 (53개)
```

## 리포트 형식

Scanner는 4가지 형식으로 리포트를 생성합니다:

- **HTML**: 시각적 리포트 (severity 배지, 접이식 증거 섹션)
- **JSON**: 구조화된 데이터 (후처리/대시보드 연동용)
- **SARIF**: GitHub/GitLab Security Dashboard 연동용
- **Console**: Rich 터미널 출력

## 주의사항

이 프로젝트는 **보안 교육 및 테스트 목적**으로만 사용해야 합니다. 실제 프로덕션 환경에 배포하지 마세요.
