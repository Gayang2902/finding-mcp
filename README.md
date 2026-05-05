# Finding MCP

LLM 에이전트가 코드 베이스를 효율적으로 탐색할 수 있도록 도구를 제공하는 MCP 서버
- 소스코드 탐색
- taint 분석
- 라우트 인증 커버리지 검사
```bash
# 테스트는 mcp inspector로 진행
npx @modelcontextprotocol/inspector ./run.sh <target_repo>
```

## 빠른 시작

```bash
git clone https://github.com/Gayang2902/finding-mcp.git
cd finding-mcp
claude mcp add finding-mcp -- ./run.sh /path/to/target/repo
```
venv 생성과 패키지 설치는 첫 실행 시 자동으로 처리

### 동적 모드 (대상 프로젝트 자유 전환, 추천)

대상 레포를 고정하지 않고 등록 시, 에이전트가 세션 중 자유롭게 프로젝트를 전환 가능

```bash
# 대상 경로 없이 등록
claude mcp add finding-mcp -- /path/to/finding-mcp/run.sh
```

에이전트가 분석 시작 시 `set_project_root` 도구를 호출:

```
→ set_project_root("/home/user/project-a")   # project-a 분석 시작
→ get_repo_info()
→ run_taint_analysis()
→ set_project_root("/home/user/project-b")   # project-b로 전환
→ map_routes()
```

### 고정 모드 (단일 대상)

분석 대상이 항상 같다면 등록 시 경로를 고정

```bash
claude mcp add finding-mcp -- ./run.sh /path/to/target/repo
```

### install.sh로 등록 (Claude Code)

```bash
./install.sh /path/to/target/repo            # user scope (기본)
./install.sh /path/to/target/repo -s project # project scope
./install.sh .                               # 현재 디렉토리
```

## 아키텍처

### 전체 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                   LLM Agent (Claude, Gemini, ...)               │
└──────────────────────────────┬──────────────────────────────────┘
                               │ JSON-RPC (stdio / SSE / HTTP)
┌──────────────────────────────▼──────────────────────────────────┐
│                     FastMCP Server (server.py)                   │
│                       21 tools registered                       │
├──────────┬───────────┬─────────┬────────┬─────────┬─────────────┤
│  Symbol  │ Structure │ Search  │  Meta  │  Taint  │   Route     │
│   (3)    │   (5)     │  (2)    │  (5)   │  (4)    │   (2)       │
├──────────┴───────────┴─────────┴────────┴─────────┴─────────────┤
│                        tools/ package                            │
│  symbols.py  structure.py  search.py  meta.py  taint.py routes.py│
├─────────────────────────────────────────────────────────────────┤
│                      core/ + indexers/                           │
│  ripgrep.py  git_utils.py  languages.py │ ctags.py treesitter.py│
├─────────────────────────────────────────────────────────────────┤
│                       analyzers/                                 │
│         semgrep.py          framework_detect.py                  │
├─────────────────────────────────────────────────────────────────┤
│                    External Binaries                             │
│  universal-ctags    tree-sitter (lib)    ripgrep    semgrep     │
└─────────────────────────────────────────────────────────────────┘
```

### 소스 구조

```
src/finding_mcp/
├── __main__.py                  # 엔트리포인트 → server.main()
├── server.py                    # FastMCP 서버, stdout 보호, 도구 등록
├── config.py                    # Settings dataclass (CLI > 환경변수 > 기본값)
├── models.py                    # Pydantic 응답 모델 (CodeLocation, SymbolDefinition, ...)
│
├── core/                        # 공통 유틸리티
│   ├── ripgrep.py               # ripgrep 서브프로세스 래퍼, regex_escape()
│   ├── git_utils.py             # HEAD 커밋 해시, dirty 감지, cache_key()
│   └── languages.py             # 확장자→언어 매핑 (CTAGS_LANGUAGE, RIPGREP_TYPE)
│
├── indexers/                    # 파싱/인덱싱 계층
│   ├── ctags.py                 # universal-ctags 래퍼, JSON 캐시, 커밋별 1-entry 유지
│   └── treesitter.py            # tree-sitter 파서, 256-entry LRU 캐시
│
├── analyzers/                   # 고수준 분석기
│   ├── semgrep.py               # Semgrep 실행기, SARIF 파서, compact_findings
│   └── framework_detect.py      # 프레임워크 자동 감지 (Express/Spring/Laravel)
│
├── tools/                       # MCP 도구 정의 (각 모듈에 register() 함수)
│   ├── symbols.py               # 심볼 탐색 도구 (ctags 기반)
│   ├── structure.py             # 코드 구조 도구 (tree-sitter 기반)
│   ├── search.py                # 검색 도구 (ripgrep 기반)
│   ├── meta.py                  # 메타데이터 도구 (파일시스템 + git)
│   ├── taint.py                 # Taint 분석 도구 (semgrep 기반)
│   └── routes.py                # 라우트/인증 도구
│
├── route_extractors/            # 프레임워크별 라우트 추출기
│   ├── express.py               # tree-sitter 기반 Express.js 라우트 파싱
│   ├── spring.py                # 어노테이션 스캔 (Spring Boot)
│   └── laravel.py               # ripgrep 기반 Laravel 라우트 파싱
│
└── rules/                       # 내장 Semgrep taint 규칙 (YAML)
    ├── js_taint.yaml
    ├── java_spring_taint.yaml
    └── php_taint.yaml
```

### 외부 라이브러리 역할

| 라이브러리 | 역할 | 사용하는 모듈 |
|-----------|------|--------------|
| **universal-ctags** | 소스코드에서 심볼(함수, 클래스, 변수) 정의를 추출. JSON 출력으로 파싱하여 `find_definition`, `list_symbols` 등에 활용 | `indexers/ctags.py` |
| **ripgrep (rg)** | 대규모 코드베이스에서 고속 정규식/리터럴 검색. .gitignore 자동 반영, 언어별 필터링 지원 | `core/ripgrep.py` |
| **tree-sitter** | 소스코드를 AST(Abstract Syntax Tree)로 파싱. 함수 본문 추출, 호출 관계 분석, 라우트 추출에 사용 | `indexers/treesitter.py` |
| **semgrep** | SAST(Static Application Security Testing) 엔진. Taint 분석으로 source→sink 데이터 흐름 추적. SARIF 포맷 출력 | `analyzers/semgrep.py` |
| **FastMCP** | MCP(Model Context Protocol) 서버 프레임워크. 도구 등록, JSON-RPC 라우팅, 다중 트랜스포트(stdio/SSE/HTTP) 제공 | `server.py` |
| **Pydantic** | 응답 직렬화 및 검증. 모든 도구 응답이 타입 안전한 모델을 거쳐 JSON으로 변환 | `models.py` |

### 데이터 흐름

```
1. 부트스트랩
   run.sh → PATH 보강 → .venv 자동 생성/설치 → python -m finding_mcp

2. 초기화
   __main__.py → server.main()
     → config.load_settings()          # CLI/env/default 우선순위
     → _guard_stdout()                 # stdio 모드에서 fd 보호
     → _build_server(settings)         # 21개 도구를 FastMCP에 등록
     → mcp.run(transport=...)          # stdio | sse | streamable-http

3. 도구 호출
   LLM → JSON-RPC request → FastMCP 라우터 → tools/*.py
     → settings.require_project_root() # 프로젝트 경로 검증
     → indexers/ (ctags, tree-sitter)  # 파싱/인덱싱
     → core/ (ripgrep, git_utils)      # 검색/메타데이터
     → analyzers/ (semgrep)            # 고수준 분석
     → Pydantic 모델 직렬화 → JSON-RPC response
```

### 캐싱 전략

| 계층 | 저장 위치 | 키 | 무효화 | 용량 제한 |
|------|-----------|-----|--------|-----------|
| ctags 인덱스 | `~/.cache/finding-mcp/tags/` (디스크) | `(commit_hash, project_root)` | 커밋 변경 시 교체 | project_root당 1 entry |
| tree-sitter AST | 인메모리 | `Path(file)` | 파일 mtime 변경 시 | 최대 256 entry (초과 시 oldest half 제거) |
| semgrep 결과 | 인메모리 + SARIF 파일 | `analysis_id (UUID)` | 세션 종료 시 | 최대 10 분석 (FIFO) |

모든 캐시 접근은 `threading.Lock`으로 보호

### 설정 우선순위

```
CLI 인자  >  환경변수 (FINDING_MCP_*)  >  기본값
```

| 설정 | 기본값 |
|------|--------|
| `transport` | `stdio` |
| `host` | `0.0.0.0` |
| `port` | `8080` |
| `cache_dir` | `~/.cache/finding-mcp` |
| `max_response_bytes` | `200,000` (200KB) |
| `semgrep_timeout` | `300`초 |
| `semgrep_max_findings` | `1,000` |

## 시스템 요구사항

필수:
- Python 3.10+
- [universal-ctags](https://github.com/universal-ctags/ctags)
- [ripgrep](https://github.com/BurntSushi/ripgrep)

```bash
brew install universal-ctags ripgrep    # macOS
apt-get install universal-ctags ripgrep # Debian/Ubuntu
```

선택:
```bash
pip install semgrep   # taint 분석용
```

## 실행

```bash
# 기본 (stdio) — Claude Code MCP에서 사용하는 모드
finding-mcp /path/to/target/repo

# 동적 모드 — 대상 없이 시작, 에이전트가 set_project_root로 설정
finding-mcp

# SSE 서버로 실행
finding-mcp /path/to/repo -t sse -p 3000

# Streamable HTTP
finding-mcp /path/to/repo -t streamable-http -p 8080

# 환경변수로도 가능
FINDING_MCP_PROJECT_ROOT=/path/to/repo finding-mcp
```

### CLI 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `PROJECT_ROOT` (위치) | 분석 대상 레포 경로 | - |
| `--project-root` | 위치 인자 대체 | - |
| `-t, --transport` | `stdio`, `sse`, `streamable-http` | `stdio` |
| `-p, --port` | SSE/HTTP 포트 | `8080` |
| `--host` | 바인드 주소 | `0.0.0.0` |
| `--cache-dir` | 캐시 디렉토리 | `~/.cache/finding-mcp` |

환경변수(`FINDING_MCP_*`)도 동일 설정 가능. CLI 인자가 우선.

## Claude Code 연동

### stdio (권장)

```bash
claude mcp add finding-mcp -- /path/to/finding-mcp/run.sh /path/to/target/repo
```

### .mcp.json (프로젝트별)

```json
{
  "mcpServers": {
    "finding-mcp": {
      "command": "/path/to/finding-mcp/run.sh",
      "args": ["/path/to/target/repo"]
    }
  }
}
```

### SSE 모드 (원격)

```json
{
  "mcpServers": {
    "finding-mcp": {
      "type": "sse",
      "url": "http://localhost:3000/sse"
    }
  }
}
```

## 도구 (21개)

### 프로젝트 설정

| 도구 | 설명 | 모듈 |
|------|------|------|
| `set_project_root(path)` | 분석 대상 레포 설정/전환. 동적 모드에서 필수 | `server.py` |

### 심볼 탐색 — `tools/symbols.py`

universal-ctags 인덱스를 사용하여 심볼 정의/참조를 검색합니다.

| 도구 | 설명 |
|------|------|
| `find_definition(symbol, language?)` | 심볼 정의 위치 (함수, 클래스, 변수) |
| `find_references(symbol, language?, limit?)` | 심볼이 사용된 모든 위치 |
| `list_symbols(file_path)` | 파일 내 모든 심볼 나열 |

### 코드 구조 — `tools/structure.py`

tree-sitter AST를 사용하여 함수 본문과 호출 관계를 분석합니다.

| 도구 | 설명 |
|------|------|
| `get_function(file_path, function_name)` | 함수 전체 본문 + 시그니처 |
| `get_function_at(file_path, line)` | 특정 라인이 속한 함수 반환 |
| `get_callees(file_path, function_name)` | 함수 내부에서 호출하는 모든 대상 |
| `get_callers(symbol, limit?)` | 코드베이스에서 심볼을 호출하는 곳 |
| `get_imports(file_path)` | import/require/use 선언 목록 |

### 검색 — `tools/search.py`

ripgrep을 사용하여 코드베이스를 고속 검색합니다.

| 도구 | 설명 |
|------|------|
| `search_code(pattern, glob?, language?, limit?)` | PCRE 정규식 검색 |
| `search_literal(text, glob?, language?, limit?)` | 리터럴 문자열 검색 (메타문자 이스케이프 불필요) |

### 메타데이터 — `tools/meta.py`

파일시스템과 git 정보를 조회합니다.

| 도구 | 설명 |
|------|------|
| `list_files(glob?, limit?)` | 프로젝트 파일 목록 (.gitignore 반영) |
| `get_file(file_path, line_start?, line_end?)` | 파일 내용 조회 (범위 지정 가능) |
| `get_repo_info()` | 프로젝트 정보 (언어 분포, 커밋 해시, 파일 수) |
| `get_project_structure(max_depth?, include_file_sizes?)` | 디렉토리 트리 구조 |
| `find_similar_files(file_path, limit?)` | 유사 파일 탐색 |

### Taint 분석 — `tools/taint.py`

Semgrep을 사용하여 source→sink 데이터 흐름을 추적합니다.

| 도구 | 설명 |
|------|------|
| `run_taint_analysis(rule_file?, language?, target_dir?)` | Taint 분석 실행 (내장/커스텀 규칙) |
| `get_taint_paths(analysis_id, limit?, offset?)` | 분석 결과 목록 (페이지네이션) |
| `get_taint_path_detail(analysis_id, finding_id)` | 개별 finding 상세 (dataflow 경로) |
| `list_taint_analyses()` | 완료된 분석 세션 목록 |

### 라우트 & 인증 — `tools/routes.py`

HTTP 라우트를 추출하고 인증 커버리지를 검사합니다.

| 도구 | 설명 |
|------|------|
| `map_routes(framework?)` | HTTP 라우트 매핑 + 미들웨어 + 핸들러 |
| `check_auth_coverage(framework?, auth_patterns?)` | 인증 누락 라우트 탐지 |

지원 프레임워크: Express, Spring, Laravel (자동 감지)

## 내장 Taint 규칙

- **JavaScript**: `eval`, `child_process.exec`, `innerHTML`, open redirect, SSRF
- **PHP**: SQL injection, command injection, file inclusion, XSS, SSRF
- **Java Spring**: SQL injection, command injection, path traversal, SSRF, SpEL injection

커스텀 규칙: `run_taint_analysis(rule_file="my_rules.yaml")`

## 지원 언어

| 언어 | ctags | tree-sitter | ripgrep | Semgrep 규칙 | 라우트 추출 |
|------|:-----:|:-----------:|:-------:|:------------:|:-----------:|
| Java | O | O | O | O | O (Spring) |
| PHP | O | O | O | O | O (Laravel) |
| JavaScript | O | O | O | O | O (Express) |
| TypeScript | O | O | O | O | O (Express) |
| TSX | O | O | O | - | - |

## 응답 규약

모든 응답에 **파일경로 + 라인번호 + 커밋해시** 포함. LLM이 도구 체이닝 시 좌표를 그대로 사용 가능.

```json
{
  "definitions": [
    {
      "name": "processInput",
      "kind": "function",
      "location": { "file_path": "src/handler.js", "line": 42 }
    }
  ],
  "commit_hash": "abc123def456"
}
```

페이지네이션 지원:
```json
{
  "items": ["..."],
  "total": 100,
  "truncated": true,
  "next_cursor": "offset=50",
  "commit_hash": "abc123def456"
}
```

## 개발

```bash
pip install -e ".[dev]"
pytest
ruff check src/ tests/
```
