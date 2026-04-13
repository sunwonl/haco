# [Audit] 에이전트 도구 현황 비교 보고서 (문서 vs 코드)

**날짜**: 2026-04-12  
**대상**: `AGENT_TOOLS.md` 규격 대비 현재 `src/harnesscore/agents/` 구현 상태

---

## 1. 계획 그룹 (Plan Group)

| 에이전트 | 설계 명세 (`AGENT_TOOLS.md`) | 실제 구현 (`src/harnesscore/agents/*.py`) | 현황 및 차이점 |
|---|---|---|---|
| **PO** | `Update_Task_Board`, `Ask_Human`, `Read_Issue`, `Assign_Agent` | LangGraph State 직접 제어 (tasks, next_agent 업데이트), 의도 분류(Intent) | 태스크 관리 및 라우팅은 완성. 인간 개입(HITL) 및 이슈 읽기 도구는 아직 명시적 도구로 분리되지 않음. |
| **SA** | `Search_Codebase` (RAG/Grep), `Write_Architecture_Doc` | `FileIOTool` (list, search) 연동, `.harness/arch_notes.md` 직접 기록 | 검색 및 문서 작성 기능은 노드 로직 내에 내재화됨. 유저 요청 시 실제 코드 검색 수행 가능. |

## 2. 생성 그룹 (Generate Group)

| 에이전트 | 설계 명세 (`AGENT_TOOLS.md`) | 실제 구현 (`src/harnesscore/agents/*.py`) | 현황 및 차이점 |
|---|---|---|---|
| **CD** | `View`, `Search`, `Replace`, `Write`, `Run_Bash` (pip 등), `Git` | `FileIOTool` (view, write), `subprocess` (pytest 실행), `GitTool` (add, commit) | 핵심 도구들(파일 수정, 테스트 실행, Git)은 거의 일치하게 구현됨. |
| **UI** | `View`, `Replace`, `Run_Bash` (npm 등), `Manage_Dev_Server` | `FileIOTool` (write), `GitTool` (add, commit) | 파일 작성 및 Git은 구현되었으나, `npm` 및 개발 서버 관리(`Manage_Dev_Server`) 기능은 아직 미구현. |

## 3. 평가 그룹 (Evaluate Group)

| 에이전트 | 설계 명세 (`AGENT_TOOLS.md`) | 실제 구현 (`src/harnesscore/agents/*.py`) | 현황 및 차이점 |
|---|---|---|---|
| **DR** | `Compare_PRD`, `Validate_Schema`, `Design_Revision` | **Dummy Node** | `graph.py`에서 더미 노드로 존재하며, 실제 검증 로직은 미구현 상태. |
| **QA** | `Ping_Endpoint`, `Run_E2E_Test`, `Read_Process_Log`, `Feedback` | `FileIOTool` (view), 히스토리 로그 분석, 상태 기반 피드백 생성 | 기본적인 피드백과 소스 분석은 가능하나, 실제 네트워크 요청(Ping)이나 E2E 테스트 실행 도구는 미구현. |

---

## 🔍 종합 진단

1. **핵심 인프라 완성**: 파일 I/O, Git, 그리고 기본적인 프로세스 실행(pytest)은 모든 에이전트에 잘 녹아들어 있습니다.
2. **도구의 내재화**: `AGENT_TOOLS.md`에서는 도구들이 별도의 함수(Function)처럼 정의되어 있으나, 현재 코드는 에이전트 노드 내부 로직에서 `FileIOTool` 등을 **직접 호출**하는 방식입니다. (추후 MCP나 독립 Toolset으로 분리 가능)
3. **평가 계층 강화 필요**: `Design Reviewer`의 부재와 `QA`의 네트워크/E2E 도구 부족이 현재 가장 큰 간극입니다.

이 리포트를 바탕으로 다음 구현 우선순위를 정해 주시면 바로 착수하겠습니다.
