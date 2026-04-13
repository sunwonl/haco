# [IR-019] 완전 초기화 명령어 (Complete Reset Command) 구현

**날짜**: 2026-04-13  
**단계**: Phase 5.6 — 관리 기능 고도화

---

## 구현 배경

기존 `harness init` 명령어는 누락된 설정 파일만 생성하는 "보수적"인 방식으로 동작하여, 전체 환경을 완전히 초기 상태로 되돌리고 싶어하는 사용자의 요구를 충족하지 못했습니다. 이를 해결하기 위해 기존 데이터를 보호(백업)하면서도 환경을 완전히 재구축할 수 있는 `reset` 기능을 추가했습니다.

---

## 주요 구현 내용 (`cli.py`)

### 1. `harness reset` 명령어 추가
사용자로부터 확인을 거친 후 `.harness/` 디렉토리를 초기화하는 명령어를 구현했습니다.

*   **백업 기능 (Default):** 삭제 전 기존 `.harness/` 폴더를 `.harness_backup_[YYYYMMDD_HHMMSS]` 형식으로 이름을 변경하여 보존합니다.
*   **삭제 기능 (Optional):** `--no-backup` 옵션 사용 시 백업 없이 즉시 삭제합니다.
*   **안전 장치:** 파괴적인 작업이므로 실행 전 `typer.confirm`을 통해 사용자 승인을 받습니다 (`-y` 옵션으로 생략 가능).
*   **재초기화 연동:** 삭제(또는 백업) 후 즉시 `init()` 로직을 호출하여 기본 설정 파일들과 에이전트 지침(instructions)들을 다시 생성합니다.

### 2. 예외 처리
*   `.harness` 폴더가 존재하지 않을 경우 경고 메시지를 출력하고 종료합니다.
*   파일 권한 등의 이유로 백업/삭제 실패 시 에러 메시지를 출력하고 안전하게 종료합니다.

---

## 실행 예시

```bash
$ harness reset
This will delete all configurations, agent instructions, and journals. Proceed? [y/N]: y
  • Backing up existing configuration to .harness_backup_20260413_133000/...
  • Re-initializing environment...

HarnessCore Initialization
  • Config Directory : .harness/
  ...
✓ Project ready!
```

---

## 다음 단계
- [ ] 에이전트들의 실제 동작 테스트 및 REPL 대화 검증
