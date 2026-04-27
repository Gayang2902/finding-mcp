# Finding MCP

보안 분석 특화 MCP 서버. LLM 에이전트가 소스코드를 탐색하고, taint 분석을 수행하고, 라우트 인증 커버리지를 검사할 수 있게 합니다.

## 빠른 시작

```bash
git clone https://github.com/Gayang2902/finding-mcp.git
cd finding-mcp
claude mcp add finding-mcp -- ./run.sh /path/to/target/repo
```

끝. venv 생성과 패키지 설치는 첫 실행 시 자동으로 처리됩니다.

### install.sh로 등록 (Claude Code)

```bash
./install.sh /path/to/target/repo            # user scope (기본)
./install.sh /path/to/target/repo -s project # project scope
./install.sh .                               # 현재 디렉토리
```

### install-gemini.sh로 등록 (Gemini CLI)

```bash
./install-gemini.sh /path/to/target/repo            # user scope (기본)
./install-gemini.sh /path/to/target/repo -s project # project scope
```

## 아키텍처

### 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                      LLM Agent (Claude)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ JSON-RPC (stdio / SSE / HTTP)
┌──────────────────────────▼──────────────────────────────────┐
│                    FastMCP Server (server.py)                │
│                     20 tools registered                     │
├─────────┬─────────┬──────────┬──────────┬─────────┬─────────┤
│ Symbol  │Structure│  Search  │   Meta   │  Taint  │  Route  │
│ (3)     │ (5)     │  (2)     │  (4)     │  (4)    │  (2)    │
├─────────┼─────────┼──────────┼──────────┼─────────┼─────────┤
│ tools_  │ tools_  │ tools_   │ tools_   │ tools_  │ tools_  │
│ symbols │structure│ search   │ meta     │ taint   │ routes  │
├─────────┴────┬────┴──────────┴─────┬────┴─────────┴─────────┤
│              │    Index / Cache    │                         │
│  ctags_index │ treesitter_index    │  semgrep    ripgrep     │
├──────────────┼─────────────────────┼────────────────────────-┤
│              │  External Binaries  │                         │
│  universal-  │   tree-sitter       │  semgrep    ripgrep     │
│  ctags       │   (library)         │  (optional) (rg)       │
└──────────────┴─────────────────────┴─────────────────────────┘
```

### 모듈 구성

```
src/finding_mcp/
├── __main__.py              # 엔트리포인트 → server.main()
├── server.py                # FastMCP 서버, 20개 도구 등록
├── config.py                # CLI 인자 > 환경변수 > 기본값 (Settings dataclass)
├── models.py                # Pydantic 응답 모델 (CodeLocation, SymbolDefinition, ...)
│
├── tools_symbols.py         # 심볼 탐색 도구 (ctags 기반)
├── tools_structure.py       # 코드 구조 도구 (tree-sitter 기반)
├── tools_search.py          # 검색 도구 (ripgrep 기반)
├── tools_meta.py            # 메타데이터 도구 (파일시스템 + git)
├── tools_taint.py           # Taint 분석 도구 (semgrep 기반)
├── tools_routes.py          # 라우트/인증 도구
│
├── ctags_index.py           # universal-ctags 래퍼, JSON 캐시
├── treesitter_index.py      # tree-sitter 파서, 언어별 초기화
├── ripgrep.py               # ripgrep 서브프로세스 실행기
├── semgrep.py               # semgrep 실행기, SARIF 파서
│
├── framework_detect.py      # 프레임워크 자동 감지
├── languages.py             # 확장자→언어 매핑
├── git_utils.py             # HEAD 커밋 해시, dirty 감지
│
├── route_extractors/        # 프레임워크별 라우트 추출
│   ├── express.py           # tree-sitter 기반
│   ├── spring.py            # 어노테이션 스캔
│   └── laravel.py           # ripgrep 기반
│
└── rules/                   # 내장 Semgrep taint 규칙 (YAML)
    ├── js_taint.yaml
    ├── java_spring_taint.yaml
    └── php_taint.yaml
```

### 데이터 흐름

```
1. 부트스트랩
   run.sh → .venv 자동 생성/설치 → python -m finding_mcp

2. 초기화
   __main__.py → server.main()
     → config.load_settings()   # CLI/env/default 우선순위
     → _build_server(settings)  # 20개 도구를 FastMCP에 등록
     → mcp.run(transport=...)   # stdio | sse | streamable-http

3. 도구 호출
   LLM → JSON-RPC request → FastMCP 라우터 → tools_*.py
     → 인덱스/캐시 계층 (ctags_index, treesitter_index, ...)
     → 외부 바이너리 실행 (ctags, rg, semgrep)
     → Pydantic 모델로 직렬화 → JSON-RPC response
```

### 캐싱 전략

| 계층 | 저장 위치 | 키 | 무효화 |
|------|-----------|-----|--------|
| ctags 인덱스 | `~/.cache/finding-mcp/tags/` (디스크) | `(commit_hash, project_root)` | 커밋 변경 시 |
| tree-sitter AST | 인메모리 | `Path(file)` | 파일 mtime 변경 시 |
| semgrep 결과 | 인메모리 + SARIF 파일 | `analysis_id (UUID)` | 세션 종료 시 |

모든 캐시 접근은 `threading.Lock`으로 보호됩니다.

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

## Gemini CLI 연동

### install-gemini.sh (권장)

```bash
./install-gemini.sh /path/to/target/repo
```

`~/.gemini/settings.json`에 자동 등록됩니다.

### settings.json 수동 설정

```json
{
  "mcpServers": {
    "finding-mcp": {
      "command": "/path/to/finding-mcp/run.sh",
      "args": ["/path/to/target/repo"],
      "timeout": 30000
    }
  }
}
```

| Scope | 파일 위치 |
|-------|-----------|
| user | `~/.gemini/settings.json` |
| project | `.gemini/settings.json` |

## 도구 (20개)

### 심볼 탐색 (ctags)

| 도구 | 설명 |
|------|------|
| `find_definition(symbol, language?)` | 심볼 정의 위치 |
| `find_references(symbol, language?, limit?)` | 심볼 참조 위치 |
| `list_symbols(file_path)` | 파일 내 모든 심볼 |

### 코드 구조 (tree-sitter)

| 도구 | 설명 |
|------|------|
| `get_function(file_path, function_name)` | 함수 전체 본문 |
| `get_function_at(file_path, line)` | 특정 라인이 속한 함수 |
| `get_callees(file_path, function_name)` | 함수가 호출하는 대상 |
| `get_callers(symbol, limit?)` | 심볼을 호출하는 곳 |
| `get_imports(file_path)` | import/require 목록 |

### 검색 (ripgrep)

| 도구 | 설명 |
|------|------|
| `search_code(pattern, glob?, language?, limit?)` | 정규식 검색 |
| `search_literal(text, glob?, language?, limit?)` | 리터럴 검색 |

### 메타

| 도구 | 설명 |
|------|------|
| `list_files(glob?, limit?)` | 파일 목록 |
| `get_file(file_path, line_start?, line_end?)` | 파일/부분 조회 |
| `get_repo_info()` | 프로젝트 정보, 언어 분포 |
| `get_project_structure(max_depth?, include_file_sizes?)` | 디렉토리 트리 |

### Taint 분석 (Semgrep)

| 도구 | 설명 |
|------|------|
| `run_taint_analysis(rule_file?, language?, target_dir?)` | Source→Sink 데이터 흐름 분석 |
| `get_taint_paths(analysis_id, limit?, offset?)` | 분석 결과 목록 (페이지네이션) |
| `get_taint_path_detail(analysis_id, finding_id)` | 개별 finding 상세 |
| `list_taint_analyses()` | 완료된 분석 목록 |

### 라우트 & 인증

| 도구 | 설명 |
|------|------|
| `map_routes(framework?)` | HTTP 라우트 매핑 + 미들웨어 |
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

## 라이선스

MIT
