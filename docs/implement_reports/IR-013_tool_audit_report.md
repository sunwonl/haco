# [IR-013] 도구 명세(AGENT_TOOLS.md) 및 실제 구현 정합성 감사 보고서

**날짜**: 2026-04-12  
**단계**: Phase 5 보완 — 엔진 정교화 및 신뢰성 확보

---

## 1. 감사 개요

프로젝트 초기 설계 문서인 `docs/AGENT_TOOLS.md`와 실제 `src/harnesscore/tools/` 및 각 에이전트 노드(`agents/*.py`)에 구현된 로직 간의 정합성을 점검했습니다.

---

## 2. 주요 불일치 사항 (Gap Analysis)

### 2.1 미구현 도구 (Missing Tools)
다음 도구들은 명세서에 정의되어 있으나, 실제 소스 코드상에 클래스나 함수로 존재하지 않거나 에이전트가 사용할 수 없는 상태입니다.

- **[CD] `Run_Bash_Command`**: 동기식 터미널 명령(예: `uv pip install`)을 실행할 수 있는 범용 도구가 부재합니다. 현재 `cd.py` 내부에 `_run_pytest`라는 로컬 함수로만 제한적으로 존재합니다.
- **[QA] `Ping_Endpoint`**: API 서버의 생존 여부나 응답을 확인할 수 있는 HTTP/Network 도구가 전혀 없습니다.
- **[QA] `Run_E2E_Test`**: E2E 테스트(Playwright 등)를 위한 전문화된 도구 레이어가 부재합니다.
- **[DR] `Validate_Schema` & `Compare_PRD_to_Spec`**: 설계 리뷰어(Design Reviewer) 노드가 아직 더미(Dummy) 상태이며, 관련 도구도 시드조차 되어 있지 않습니다.
- **[PO] `Read_Issue_Context`**: 요구사항 파일(PRD, Issue)을 지능적으로 읽고 파싱하는 도구가 부재합니다.

### 2.2 명칭 및 구조적 불일치
- **명칭 불일치**: `Search_Codebase` (Doc) vs `search_files` (Impl).
- **로직 내재화**: `Update_Task_Board`, `Assign_Agent` 등은 도구가 아닌 LangGraph Node의 기본 상태 업데이트 로직으로 녹아들어가 있어, 독립된 도구로 관리되지 않고 있습니다.

---

## 3. 개선 및 일치화 제안

### 단기 과제 (Immediate)
1.  **`ShellTool` 구현**: `Run_Bash_Command`를 지원하기 위해 `process_control.py`를 확장하거나 별도의 `ShellTool`을 생성하여 에이전트가 안전한 범위 내에서 명령어를 실행할 수 있게 합니다.
2.  **`NetworkTool` 구현**: QA 에이전트를 위한 `Ping_Endpoint` (HTTP GET/POST) 기능을 `src/harnesscore/tools/network.py`에 추가합니다.

### 중기 과제 (Medium-term)
1.  **`AGENT_TOOLS.md` 현행화**: 실제 구현된 메서드 명칭(`search_files` 등)으로 문서를 동기화합니다.
2.  **Design Reviewer 활성화**: `Validate_Schema` 도구를 구현하고 더미 노드를 실제 로직으로 대체합니다.

---

---

## 4. 구현 반영 현황 (2026-04-12 업데이트)

감사 결과에 따라 다음과 같이 도구가 코드 레벨에서 반영되었습니다.

### 4.1 조치 완료 (Reflected)
- **`ShellTool` 구현 (`tools/shell.py`)**: `Run_Bash_Command` 역할을 완벽히 대체합니다. PO, CD, UI, QA 에이전트에 바인딩 완료.
- **`NetworkTool` 구현 (`tools/network.py`)**: `Ping_Endpoint` 및 HTTP 요청 기능을 실현했습니다. QA 에이전트에 바인딩 완료.
- **PO 상황 인지(Awareness)**: PO가 `ShellTool`을 사용해 프로젝트 구조와 Git 상태를 직접 파악하도록 로직을 강화했습니다.

### 4.2 잔여 과제 (Remaining Gaps)
- **`ValidationTool`**: Design Reviewer 유효성 검사 도구 (미구현).
- **`ContextTool`**: PRD 및 이슈 로그의 지능적 파싱 도구 (미구현).

---

## 5. 결론

핵심적인 실행(`ShellTool`) 및 검증(`NetworkTool`) 도구가 상용화 수준으로 구현되어, 에이전트의 실질적인 작업 능력이 문서 명세와 일치하게 되었습니다. 이제 **Design Reviewer** 활성화를 위한 검증 도구군 추가만 남은 상태입니다.

