# HarnessCore AI - Detailed Requirements (요구사항 구체화)

본 문서는 `PRD.md`에 명시된 HarnessCore AI 멀티 에이전트 시스템에 대한 세부 기능적, 비기능적 요구사항 및 시스템 아키텍처 구현을 위한 기술적 행동 규약을 정의합니다.

---

## 1. 페르소나 및 하위 모듈별 요구사항 (Plan - Generate - Evaluate 구조)

하네스 엔지니어링 이론의 **'계획-생성-평가'** 3단계 모델에 기반하여 에이전트를 구분합니다.

### [Plan] 계획 담당 에이전트 그룹
#### 1.1 오케스트레이터 (PO - Product Owner)
* **목표**: 사용자 요구사항 분석 및 구체화, 태스크 분할 및 작업 할당.
* **기능 요건**:
  * 추상적인 사용자 입력(Natural Language)을 **분석하고 요구사항을 구체화**(Requirements Refinement).
  * 구체화된 요구를 달성하기 위한 개발 태스크 리스트 생성 및 적절한 에이전트에 라우팅.
  * 진행 상태 추적, 에이전트 간 분쟁 조정 및 Human-in-the-loop(HITL) 인터럽트 소통.

#### [Plan] 1.2 시스템 설계자 (System Architect)
* **목표**: PO가 구체화한 요구사항을 기반으로 시스템을 구현하기 위한 **상세 기술 설계**.
* **기능 요건**:
  * Pydantic 기반 DB Schema(PostgreSQL 등) 명세서 도출.
  * API 엔드포인트 규격 및 컴포넌트 설계 작성.

### [Generate] 생성 담당 에이전트 그룹
#### 1.3 백엔드 개발자 (Core Developer)
* **목표**: 설계된 스키마와 규격 위에서 실제 백엔드 로직 코드를 생성.
* **기능 요건**:
  * 파일 읽기/쓰기를 통해 `main.py` 등 서버 로직 파일 직접 수정.
  * DB Migration 또는 백엔드 빌드 도구 구동.
  * 단위 테스트 코드 자동 작성 및 실행.

#### [Generate] 1.4 프론트엔드 개발자 (UI Engineer)
* **목표**: 백엔드 API와 통신하는 프론트엔드 코드 생성.
* **기능 요건**:
  * UI 컴포넌트 시각적 렌더링을 위한 코드 수정 프로세스 수행.
  * 렌더링된 결과를 QA 에이전트에 스크린샷 렌더링 형태로 넘겨 검증받을 수 있는 구조 지원.

### [Evaluate] 평가 담당 에이전트 그룹
#### 1.5 설계 리뷰어 (Design Reviewer)
* **목표**: PO가 쪼갠 태스크 명세서와 System Architect가 작성한 아키텍처 문서가 논리적 결함 없이 완벽한지 정적 검증(Static Review)을 수행.
* **기능 요건**:
  * 초기 요구사항(PRD)과 도출된 로직 명세를 교차 비교 (기획 검증).
  * DB 스키마의 정규화 수준, 변수 타입, 누락된 스펙을 판단하여 설계 에이전트들에게 피드백/재설계 지시.

#### 1.6 QA 평가자 (QA Evaluator)
* **목표**: 사람이 개입하지 않고도 산출물의 품질을 평가 및 피드백.
* **기능 요건**:
  * Playwright/Selenium 또는 단순 프로세스 ping을 통한 E2E 로직 모니터링 트리거 도구 연동.
  * 실행 에러 로그를 분석하여 오류 코드 블록과 함께 원인 리포트를 생성하여 개발자 에이전트에게 재시도 요청(Feedback Loop).

---

## 2. 코어 메커니즘 및 툴 요구사항

### 2.1 직접 파일/운영체제 I/O (Safety without Isolation)
* **Tools**:
  * `read_file(path, lines)`, `write_file(path, content)`, `append_file(path, content)`, `replace_file_content(path, target, replacement)`
  * `execute_command(command, working_dir, timeout)`: 터미널 명령을 수행, timeout을 반드시 설정해 무한 대기 방지.

### 2.2 Git Life-cycle 기반 안전성 (VCS 기반 롤백/복구)
* **로직 파이프라인**:
  1. PO가 태스크 확정시, 기반 브랜치에서 분기 (`git checkout -b feature/agent-task-id`)
  2. 에이전트가 파일 수정 및 테스팅.
  3. QA Evaluator의 승인(Validation_Success) 시, Commit 및 Pull Request (또는 base branch 머지) 시도.
  4. 복잡한 에러 발생 시 PO 판단하에 `git reset --hard` 후 처음부터 다른 전략으로 코드 생성.

### 2.3 LangGraph 및 State Persistence
* **State 객체 구조(예시)**: 현재 작업자, 작업 히스토리 목록, 현재 파일 변경사항 목록, 최신 에러 메시지.
* **DB (Checkpointer) 적용**: PostgreSQL 기반 스토리지 객체를 LangGraph checkpointer로 선언해, 에이전트 중단/재기동 시 State 복원 기능 구현.

### 2.4 데이터 구조 안전성 (Pydantic 강제화)
* LLM의 응답은 JSON Mode (또는 Function Calling Structured Output)로 강제하며, 이를 런타임에서 특정 Pydantic 모델로 파싱 시도. 파싱 실패 시 예외를 잡아 프롬프트에 담아 다시 LLM으로 쿼리 (Self-Healing 메커니즘).

---

## 3. 확장성 및 사용자 프로젝트 환경 설정 (Extensibility & Config)

시스템은 통일된 사용자 경험(UX)을 위하여 작업 디렉토리 내에 독립적인 환경설정 및 도구를 프로비저닝할 수 있는 기능을 제공합니다.

### 3.1 파일 기반 프로젝트 설정 (`.harness/settings.json`)
*   해당 프로젝트의 무시(ignore) 규칙, 사용 프레임워크 힌트, LLM 선택 및 System Prompt 재정의 속성 등을 담는 환경 파일.
*   엔진 최초 구동 시 이 파일을 파싱하여 전체 에이전트의 기본 State 및 프롬프트에 주입(Injection)합니다.

### 3.2 작업 템플릿 (Skills)
*   사용자 정의 '스킬' 기능 제공 (`.harness/skills/` 디렉토리 내 마크다운 또는 JSON 스펙).
*   에이전트에게 "React 컴포넌트를 짤 때는 이렇게 해라" 같은 프로젝트만의 자체적인 코딩 가이드라인이나 템플릿을 등록하여 일관성 있는 산출물을 강제합니다.

### 3.3 로컬 및 외부 MCP 연동 (Model Context Protocol)
*   사용자가 사내 데이터베이스나 서드파티 툴(Jira, Slack 등)을 MCP 규격 서버로 띄워두고 `settings.json`에 엔드포인트를 등록할 수 있습니다.
*   부트스트래퍼가 시스템 시작 시 등록된 MCP 서버와 커넥션을 맺고, 제공되는 도구(Tools)들을 에이전트 인프라에 동적으로 매핑하여 사용 가능한 무기를 확장합니다.
