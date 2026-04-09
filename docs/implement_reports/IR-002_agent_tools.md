# [IR-002] 에이전트 공통 도구 모듈 (Agent Tools)

**날짜**: 2026-04-09  
**단계**: Phase 2 — 에이전트 Tool 레이어 구현

---

## 구현 내용

### 1. FileIOTool (`tools/file_io.py`)

에이전트가 프로젝트 내 파일을 안전하게 읽고 쓸 수 있도록 **Path Guard** 로직이 내장된 파일 I/O 도구입니다.

| 메서드 | 설명 |
|---|---|
| `view_file(path, start, end)` | 파일 읽기 (라인 범위 지정 가능) |
| `write_file(path, content)` | 파일 생성 또는 덮어쓰기 |
| `append_file(path, content)` | 파일 끝에 내용 추가 |
| `replace_content(path, target, replacement)` | 첫 번째 일치 문자열 교체 |
| `search_files(query, pattern)` | Grep 스타일 파일 내 텍스트 검색 |
| `list_directory(path)` | 디렉토리 목록 반환 |

**Path Guard**: 선언된 `project_root` 외부 경로(`../` 등) 접근 시 `PathGuardError` 예외 발생.

### 2. GitTool (`tools/git_tool.py`)

안전한 Git 작업을 위한 허용 목록(Allow-list) 기반 래퍼입니다.

- **허용 서브커맨드**: `status`, `log`, `diff`, `branch`, `checkout`, `add`, `commit`, `reset`, `stash`
- 허용 목록 외 명령 시도 → `PermissionError` 즉시 발생

| 메서드 | Git 명령 |
|---|---|
| `status()` | `git status --short` |
| `log(n)` | `git log -n --oneline` |
| `diff(path)` | `git diff [path]` |
| `create_branch(name)` | `git checkout -b <name>` |
| `add(path)`, `commit(msg)` | 스테이징 및 커밋 |
| `rollback(mode)` | `git reset --hard/soft/mixed HEAD` |

### 3. ProcessControlTool (`tools/process_control.py`)

개발 서버나 테스트 러너 같은 백그라운드 프로세스를 *레이블(label)* 기반으로 관리하는 도구입니다.

| 메서드 | 설명 |
|---|---|
| `start(label, command, wait_seconds)` | 백그라운드 프로세스 실행 |
| `stop(label)` | 프로세스 종료 |
| `restart(label)` | stop → start 재시작 |
| `read_log(label, n)` | 마지막 n줄 출력 확인 |
| `status()` | 전체 프로세스 상태 목록 |
| `stop_all()` | 앱 종료 시 전체 프로세스 정리 |

---

## 테스트 결과

```
tests/test_tools.py::test_write_and_read          PASSED
tests/test_tools.py::test_append                  PASSED
tests/test_tools.py::test_replace_content         PASSED
tests/test_tools.py::test_path_guard_blocks_escape PASSED
tests/test_tools.py::test_search_files            PASSED
tests/test_tools.py::test_git_status              PASSED
tests/test_tools.py::test_git_create_and_list_branches PASSED
tests/test_tools.py::test_git_add_commit          PASSED
tests/test_tools.py::test_git_disallow_unknown_subcommand PASSED

9 passed in 0.11s
```

---

## 다음 단계
- `IR-003`: LangGraph 그래프 및 PO 에이전트(Supervisor Node) 구현
