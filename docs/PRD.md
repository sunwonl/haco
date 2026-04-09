# [PRD] HarnessCore AI: Self-Iterative Multi-Agent Coding Engine

## 1. 제품 개요 (Product Overview)
**HarnessCore AI**는 사람이 작성한 모호한 요구사항을 바탕으로 **기획, 설계, 개발, 검증, 배포**의 전 과정을 자율적으로 수행하는 멀티에이전트 시스템입니다. 별도의 샌드박스 없이 기존 코드베이스 환경에서 안전하게 공존하며, Git 기반의 버전 관리와 엄격한 Evaluator 루프를 통해 고품질의 코드를 지속적으로 생산하는 것을 목표로 합니다.

## 2. 핵심 가치 (Core Values)
* **Safety without Isolation:** 샌드박스 없이도 Git과 Path Guard를 통해 안전한 직접 코드 수정 지원.
* **High-Fidelity Evaluation:** 개발자와 검수자의 인격을 분리하여 '동작하는 코드' 이상의 '신뢰할 수 있는 코드' 지향.
* **Durable Orchestration:** 장기 실행(Long-running) 중 중단되어도 PostgreSQL 체크포인트를 통해 중단 지점부터 완벽 복구.

---

## 3. 사용자 및 페르소나 (Roles & Agents)

하네스 내부에서 구동될 5인의 AI 에이전트 팀은 하네스 엔지니어링 역학에 따라 **계획(Plan) - 생성(Generate) - 평가(Evaluate)** 의 구조로 나뉩니다.

### [Plan] 계획 그룹
| 역할 | 명칭 | 핵심 지침 (Instruction Key) |
| :--- | :--- | :--- |
| **오케스트레이터** | **PO (Product Owner)** | 사용자 입력(NL) 분석 및 요구사항 구체화, 태스크 분할 및 작업 할당. |
| **설계자** | **System Architect** | 주어진 구체화 요구사항을 바탕으로 상세 기술 설계 (DB 스키마 설계, API 규격 정의). |

### [Generate] 생성 그룹
| 역할 | 명칭 | 핵심 지침 (Instruction Key) |
| :--- | :--- | :--- |
| **Backend** | **Core Developer** | 설계된 스키마 기반 비즈니스 로직 작성, 단위 테스트, 엔드포인트 구축. |
| **Frontend** | **UI Engineer** | API 연동 및 컴포넌트 설계 등 사용자 인터페이스 작성 프로세스. |

### [Evaluate] 평가 그룹
| 역할 | 명칭 | 핵심 지침 (Instruction Key) |
| :--- | :--- | :--- |
| **설계 리뷰어**| **Design Reviewer** | 기획/설계 문서 및 DB 스키마의 논리적 정합성 검증(정적 분석) 및 수정 요구. |
| **검증자** | **QA Evaluator** | 프로세스 모니터링, E2E 테스트를 통한 품질 평가 및 재시도 피드백 루프 작동. |


---

## 4. 핵심 기능 요구사항 (Functional Requirements)

### 4.1 에이전트 라이브 워크스페이스 (Live Workspace)
* **Direct File I/O Tool:** 에이전트가 지정된 루트 디렉토리 내에서 파일을 읽고 쓸 수 있는 도구 제공.
* **Git Life-cycle Management:** 작업 전 브랜치 자동 생성, 작업 중 자동 커밋, 실패 시 자동 롤백(`git reset --hard`) 기능.
* **Process Control:** `npm run dev`나 `uvicorn` 등 기존 서버 프로세스를 재시작하거나 상태를 모니터링하는 기능.

### 4.2 하네스 오케스트레이션 (LangGraph 기반)
* **State Persistence:** PostgreSQL을 사용하여 에이전트 간의 모든 대화 기록과 작업 상태를 영구 저장.
* **Conditional Loop:** QA 에이전트의 승인이 떨어질 때까지 개발 에이전트에게 수정을 반복 요청하는 루프 로직.
* **Human-in-the-loop (HITL):** 중요한 아키텍처 결정이나 최종 Merge 전 사용자 승인을 기다리는 인터럽트 기능.

### 4.3 데이터 및 타입 보안 (Pydantic 통합)
* **Schema Enforcement:** 에이전트 간의 모든 소통물(기획서, 이슈 리포트 등)을 Pydantic 모델로 정의하여 파싱 에러 원천 차단.
* **Self-Healing:** 에이전트가 잘못된 JSON 형식을 내놓을 경우, Pydantic 에러 메시지를 피드백으로 주어 자동 수정 유도.

---

## 5. 기술 스택 (Technical Stack)

* **Language:** Python 3.11+
* **LLM:** Google Gemini 3 Flash & Pro (Multi-modal 지원으로 UI 검증 활용)
* **Framework:** LangGraph (Orchestration), Pydantic (Data Validation)
* **Infrastructure:** 호스트 OS 직접 접근 (Python `os`, `subprocess` 모듈 활용)
* **Database:** PostgreSQL (State Store & Checkpointer)
* **VCS:** Git (Branching & Safety Rollback)

---

## 6. 성공 지표 (Success Metrics)
1.  **Zero Manual Intervention:** 단순 기능 추가 시 사용자의 코드 수정 없이 성공적으로 배포 브랜치까지 생성하는 비율 90% 이상.
2.  **Safety Rate:** 에이전트의 작업 중 호스트 시스템의 핵심 파일이 손상되거나 서비스가 영구 중단되는 사고 0건.
3.  **Iteration Efficiency:** QA 루프를 평균 3회 이내로 통과하여 최종 결과물을 도출하는 속도.
