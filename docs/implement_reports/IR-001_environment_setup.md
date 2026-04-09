# [IR-001] 기반 환경 구성 (Environment Setup)

**날짜**: 2026-04-09  
**단계**: Phase 1 — 프로젝트 초기화

---

## 구현 내용

### 1. uv 프로젝트 초기화
- `uv init --app --python 3.11`으로 Python 3.11 기반 프로젝트 생성
- `pyproject.toml`에 `[build-system]` (hatchling), `[tool.hatch.build.targets.wheel]` 설정으로 `src/` 레이아웃 선언

### 2. 의존성 설치
| 패키지 | 용도 |
|---|---|
| `langgraph` | 에이전트 오케스트레이션 |
| `langchain-google-genai` | Gemini LLM 연동 |
| `fastapi` + `uvicorn` | 백엔드 API 서버 |
| `pydantic` | 스키마 및 설정 유효성 검사 |
| `textual` + `rich` | TUI 클라이언트 |
| `typer` | CLI 진입점 |
| `pytest`, `ruff`, `pyright` | 개발 도구 |

### 3. 프로젝트 디렉토리 구조

```
src/harnesscore/
├── __init__.py
├── cli.py              ← harness init / cli / web 진입점 (Typer)
├── schema.py           ← SystemState, TaskLog Pydantic 스키마
├── config/
│   └── loader.py       ← .harness/settings.json 로더
├── checkpointer/
│   └── file_checkpointer.py  ← LangGraph용 커스텀 FileCheckpointer
├── agents/             ← (예정) 에이전트 구현
├── tools/              ← (예정) File I/O, Git 도구
└── tui/                ← (예정) Textual TUI 앱
```

### 4. 핵심 파일

- **`schema.py`**: LangGraph를 순환하는 공유 상태 객체 `SystemState`, 로그 단위 `TaskLog` Pydantic 모델 정의
- **`config/loader.py`**: `HarnessConfig` 모델 기반으로 `.harness/settings.json` 자동 생성 및 로드
- **`checkpointer/file_checkpointer.py`**: `BaseCheckpointSaver`를 상속하여 DB 없이 `.harness/state.json`(기계용)과 `.harness/journals.md`(사람용)로 상태를 저장하는 커스텀 구현
- **`cli.py`**: `harness init`, `harness cli`, `harness web` 3개 서브커맨드 (cli/web은 Phase 4에서 구현 예정)

### 5. 검증 결과

```bash
$ uv run harness --help     # ✅ 3개 서브커맨드 정상 노출
$ uv run harness init       # ✅ .harness/settings.json 자동 생성
```

**생성된 `.harness/settings.json`**:
```json
{
  "llm_model": "gemini-2.0-flash",
  "max_iterations": 10,
  "project_root": null,
  "ignore_patterns": [".git", "node_modules", "__pycache__", ".harness"],
  "mcp_servers": {}
}
```

---

## 다음 단계
- `IR-002`: 에이전트 공통 Tool 모듈 구현 (File I/O, Git, ProcessControl)
