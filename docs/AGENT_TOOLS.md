# 에이전트별 도구 명세서 (Agent Tools Specification)

이 문서는 HarnessCore 내의 각 에이전트가 부여받은 역할을 수행하기 위해 실제로 접근하고 사용하는 핵심 Tools (Functions) 목록을 식별합니다. 최소 권한의 원칙(Principle of Least Privilege)에 따라 각 에이전트별로 권한 범위를 제한합니다.

---

## 1. [Plan] 계획 그룹 도구 리스트

### 1.1 오케스트레이터 (PO - Product Owner)
PO는 시스템의 상태를 전역적으로 이해하고 태스크를 기록하며, 유저와 소통하는 역할입니다. 최초 응대 시 상황 파악을 위해 기본적인 조회 도구를 가집니다.

*   **File I/O (Read-only)**: `View_File`, `List_Directory`.
*   **System Diagnostics**: `ShellTool`을 통한 `ls`, `git status`, `env` 등 단순 조회성 명령 실행.
*   `Update_Task_Board`: LangGraph State 내의 작업 목록 업데이트.
*   `Ask_Human_Clarification` (HITL): 사용자에게 질문 전달 및 응답 대기.
*   `Assign_Agent`: 분석된 Task를 바탕으로 적절한 에이전트 라우팅.

### 1.2 시스템 설계자 (System Architect)
아키텍처의 기준이 되는 설계 문서 저장 및 코드베이스의 거시적 맥락을 파악합니다.

*   `Search_Codebase` (RAG / Grep 기반): 프로젝트 내 기존 DB 설계(models.py 등) 및 API 구조를 검색하여 충돌 없는 디자인을 유도.
*   `Write_Architecture_Doc`: `docs/` 폴더 내에 DB 스키마 명세서(Pydantic/SQLAlchemy) 및 OpenAPI Swagger 스펙 마크다운 작성.
*   *(주의: 핵심 런타임 코드를 직접 수정하는 도구는 배제)*

---

## 2. [Generate] 생성 그룹 도구 리스트

생성 에이전트들은 실제 코드를 구현하므로 로컬 파일 직접 제어 및 개발 명령어 실행 도구가 필요합니다.

### 2.1 백엔드 개발자 (Core Developer)
*   **File I/O Tools**:
    *   `View_File`, `Search_File`: 소스코드 탐색.
    *   `Replace_Content`, `Write_File`: `main.py`, `models.py` 등 백엔드 로직 파일 편집.
*   **Command Line Tools (Backend)**: 
    *   `Run_Bash_Command`: 백엔드 패키지 설치(`pip install`), DB 마이그레이션(`alembic upgrade head`) 등을 터미널에서 수행.
    *   *보안: Path Guard 설정을 통해 `/backend` 폴더 내부 및 지정된 명령어만 허용.*
*   **VCS Tools**:
    *   `Git_Operation`: `commit`, 새 브랜치 생성 등을 통해 작업 스냅샷 저장.

### 2.2 프론트엔드 개발자 (UI Engineer)
*   **File I/O Tools**:
    *   `View_File`, `Replace_Content`: React/Vue 등 프론트엔드 컴포넌트 수정.
*   **Command Line Tools (Frontend)**:
    *   `Run_Bash_Command`: `npm install`, 컴포넌트 빌드 도구 실행.
    *   `Manage_Dev_Server`: 빠른 수정을 확인하기 위해 `npm run dev` 등을 백그라운드 프로세스로 관리(Start/Stop/Restart).

---

## 3. [Evaluate] 평가 그룹 도구 리스트

### 3.1 설계 리뷰어 (Design Reviewer)
코드 배포 전 아키텍처 및 기획 문서를 검증합니다.
*   **Review Tools**:
    *   `Compare_PRD_to_Spec`: 초기 사용자 요구사항(PRD)과 최신 기술 명세서 간의 내용 교차 비교.
    *   `Validate_Schema`: Pydantic/SQLAlchemy 모델 스펙 파일의 논리적 모순, 구조 점검.
*   **Feedback Tool**:
    *   `Request_Design_Revision`: 설계상 문제점 발견 시 System Architect / PO 노드 측으로 재설계 피드백 라우팅.

### 3.2 검증자 (QA Evaluator)
QA 에이전트는 코드 수정 권한을 가지지 않으며, 오직 실행 환경 검증 및 로그 확인만 담당합니다.

*   **Network / E2E Tools**:
    *   `Ping_Endpoint`: 특정 API (`/health` 등)에 HTTP GET/POST 요청을 보내어 반환되는 상태 코드 및 Body 확인.
    *   `Run_E2E_Test`: Playwright/Cypress 기반 통합 테스트 스크립트 실행 및 결과 파싱.
*   **Log Inspection Rule**:
    *   `Read_Process_Log`: Core / UI 에이전트가 실행해둔 서버의 표준 출력(stdout) 및 에러 로그(stderr) 추출.
*   **Feedback Tool**:
    *   `Issue_Feedback_Report`: 검증 실패 시, 추출된 에러 로그와 함께 "수정 지시사항(Feedback)"을 작성하여 다시 개발 에이전트의 State로 밀어 넣음.
