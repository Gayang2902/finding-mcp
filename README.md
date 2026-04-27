# Finding MCP

보안 분석 특화 MCP 서버. LLM 에이전트가 소스코드를 탐색하고, taint 분석을 수행하고, 라우트 인증 커버리지를 검사할 수 있게 합니다.

## 시스템 요구사항

```bash
brew install universal-ctags ripgrep    # macOS
apt-get install universal-ctags ripgrep # Debian/Ubuntu
pip install semgrep                     # taint 분석용 (선택)
```

## 설치

```bash
git clone https://github.com/Gayang2902/finding-mcp.git
cd finding-mcp
pip install -e .
```

SSE/HTTP 트랜스포트를 사용하려면:
```bash
pip install -e ".[sse]"
```

## 실행

```bash
# 기본 (stdio)
finding-mcp /path/to/target/repo

# SSE 서버로 실행
finding-mcp /path/to/repo -t sse -p 3000

# Streamable HTTP
finding-mcp /path/to/repo -t streamable-http -p 8080

# 환경변수로도 가능 (하위 호환)
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

`.mcp.json` (프로젝트) 또는 `~/.claude/mcp_servers.json` (전역):

```json
{
  "mcpServers": {
    "finding-mcp": {
      "command": "finding-mcp",
      "args": ["/path/to/target/repo"]
    }
  }
}
```

SSE 모드로 원격 연동:
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

## 응답 규약

모든 응답에 **파일경로 + 라인번호 + 커밋해시** 포함. LLM이 도구 체이닝 시 좌표를 그대로 사용 가능.

## 개발

```bash
pip install -e ".[dev]"
pytest
ruff check src/ tests/
```
