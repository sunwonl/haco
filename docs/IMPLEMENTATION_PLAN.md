# HarnessCore 구현 계획 (Implementation Roadmap)

현재까지 완료된 작업(IR-001~003)을 기반으로 앞으로 진행할 구현 항목들을 정리합니다.

---

## ✅ 완료

| IR | 내용 |
|---|---|
| IR-001 | 프로젝트 초기화 (uv, 디렉토리 구조, 기반 스키마, FileCheckpointer, CLI) |
| IR-002 | 에이전트 공통 도구 모듈 (FileIOTool, GitTool, ProcessControlTool) |
| IR-003 | 설정 스키마 개선 (LLMConfig, CredentialsConfig, GitConfig, agent_paths) |

---

## 🔲 진행 예정

### IR-004: LangGraph 그래프 및 PO Supervisor Node
- `StateGraph` 정의 (`SystemState` 기반)
- PO 노드: 요구사항 분석 → Task 분할 → `next_agent` 라우팅 결정
- Conditional Edge: `next_agent` 값에 따라 하위 에이전트 노드로 분기
- `FileCheckpointer` 연동하여 `.harness/state.json` + `journals.md` 기록
- **HITL 인터럽트 포인트**: PO가 `HITL` 신호 반환 시 사용자 입력 대기

### IR-005: System Architect 에이전트
- 설계 문서(Pydantic 스키마, API 규격) 작성 도구(`Write_Architecture_Doc`) 구현
- 코드베이스 맥락 파악을 위한 `Search_Codebase` (FileIOTool.search_files 래핑) 구현
- LangGraph 노드로 등록 및 PO 라우팅 연동

### IR-006: Design Reviewer 에이전트
- PRD 파일과 현재 아키텍처 명세서를 LLM으로 교차 비교하는 정적 검증 로직
- `Validate_Schema`: 지정 파일의 Pydantic 스펙 파싱 가능 여부 실행 검증
- 실패 시 `next_agent = "System Architect"` 피드백 라우팅

### IR-007: Core Developer 에이전트
- FileIOTool + GitTool + ProcessControlTool 풀 접근으로 백엔드 코드 작성
- pytest 기반 단위 테스트 자동 실행 및 결과 반환
- 자체 에러 분석(Self-Correction) 루프: 테스트 실패 시 최대 N회 자체 재시도

### IR-008: UI Engineer 에이전트
- 프론트엔드 경로(`agent_paths["UI Engineer"]`) 제한 적용
- `Manage_Dev_Server`: ProcessControlTool로 `npm run dev` 백그라운드 관리
- 스크린샷 캡처(향후 Playwright 연동) 후 QA 에이전트로 전달

### IR-009: QA Evaluator 에이전트
- `Ping_Endpoint`: httpx 기반 엔드포인트 헬스체크
- `Run_E2E_Test`: 외부 pytest / Playwright 스크립트 실행 및 결과 파싱
- 실패 시 에러 로그 추출 → `latest_error` State 업데이트 → 개발 에이전트로 피드백

### IR-010: 전체 파이프라인 통합 테스트
- PO → SA → DR → CD → QA 전체 루프 단일 시나리오로 검증
- GAN 수준의 단순 기능 ("hello.txt 파일 생성") 태스크 End-to-End 실행
- recursion_limit 검증 (무한루프 제동 확인)

---

## 🔲 보류 (후속 Phase)

### IR-011: TUI 클라이언트 (Phase 4)
- Textual 기반 화면 레이아웃 (에이전트 상태 패널, 채팅 입력, Diff 뷰어)
- FastAPI 백엔드 Daemon 스레드로 내장, `harness cli` 단일 명령어로 구동
- HITL 인터럽트 → TUI 팝업 → 사용자 응답 → 재개 흐름

### IR-012: MCP 서버 연동 (Phase 5)
- `.harness/settings.json`의 `mcp_servers` 엔드포인트 목록 읽어 부트스트래핑 시 연결
- MCP가 노출하는 도구(Tools)를 에이전트 Tool 레지스트리에 동적 등록

### IR-013: Skills 시스템 (Phase 5)
- `.harness/skills/*.md` 파일을 읽어 에이전트 시스템 프롬프트에 자동 주입
- 프로젝트별 코딩 컨벤션, 자주 쓰는 패턴 템플릿 적용

### IR-WEB: Web 대시보드 (Phase 6)
- React 기반 대시보드 (노드 그래프, 실시간 diff 뷰어, HITL 승인 버튼)
- FastAPI Static 파일 서빙으로 별도 서버 없이 `harness web` 단일 커맨드 실행
