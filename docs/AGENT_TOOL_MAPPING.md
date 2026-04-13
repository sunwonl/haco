# HarnessCore Agent-to-Tool Mapping (Audit Alignment)

이 문서는 `IR-013` 감사 결과를 바탕으로, 각 에이전트에게 실제로 부여할 도구(Tools)의 최종 매핑 안을 정의합니다.

## 1. 생성 및 실행 그룹 (Generate & Execute)

### 1.1 Core Developer (CD)
- **추가 예정**: `ShellTool.run_command` (동기식)
- **용도**: 의존성 설치(`pip`, `uv`), DB 마이그레이션 실행, 빌드 스크립트 실행.
- **기존**: `FileIOTool`, `GitTool`, `_run_pytest` (내장).

### 1.2 UI Engineer (UI)
- **추가 예정**: `ShellTool.run_command`
- **용도**: `npm install`, `npm build` 등 빌드 도구 제어.
- **기존**: `FileIOTool`, `GitTool`, `ProcessControlTool` (서버 제어용).

## 2. 평가 및 검증 그룹 (Evaluate & Verify)

### 2.1 QA Evaluator (QA)
- **추가 예정**: `NetworkTool.ping`, `NetworkTool.http_request`, `ShellTool.run_command`
- **용도**: 로컬 서버 가용성 체크, API 엔드포인트 통합 테스트, `pytest`/`playwright` 테스트 러너 실행.
- **기존**: `FileIOTool`, `ProcessControlTool` (로그 확인용).


### 2.2 Design Reviewer (DR)
- **추가 예정**: `ValidationTool.validate_schema`, `ValidationTool.compare_context`
- **용도**: Pydantic/SQLAlchemy 모델의 논리적 모순 검사, 요구사항(PRD)과의 일치성 확인.
- **기존**: N/A (현재 더미 상태).

## 3. 오케스트레이션 및 설계 그룹 (Orchestrate & Design)

### 3.1 Product Owner (PO)
- **추가 예정**: `FileIOTool` (읽기 전용), `ShellTool.run_command` (진단용)
- **용도**: 프로젝트 구조 파악(`ls`, `tree`), 현재 환경 상태 확인(`env`, `git status`). 에이전트 호출 없이 유저에게 즉각적인 응답 제공.
- **기존**: N/A (상태 추론만 수행).

### 3.2 System Architect (SA)
- **추가 예정**: `ContextTool.read_project_docs`
- **용도**: `docs/` 폴더 내의 PRD, 로드맵, 이슈 로그를 지능적으로 파이프라인에 주입.
- **기존**: `FileIOTool.search_files`.

---

## 4. 구현 우선순위
1.  **Priority 1**: `ShellTool` (CD/UI의 명령행 자유도 확보)
2.  **Priority 2**: `NetworkTool` (QA의 실제 API 검증 능력 확보)
3.  **Priority 3**: `ValidationTool` (Design Reviewer 에이전트 활성화)
