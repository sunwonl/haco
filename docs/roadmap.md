# HarnessCore 로드맵 (Roadmap)

> 마지막 업데이트: 2026-04-20

HarnessCore AI의 개발 방향과 주요 마일스톤입니다.

## ✅ 완료된 Phase

### Phase 4: Core Agent Implementation
- [x] IR-004: 오케스트레이션 엔진 (LangGraph + `graph.py`)
- [x] IR-005: System Architect 에이전트 (`agents/sa.py`)
- [x] IR-006: Design Reviewer 에이전트 (`agents/dr.py`) — PASS/REVISE 판정 로직 포함
- [x] IR-007: Core Developer 에이전트 (`agents/cd.py`)
- [x] UI Engineer 에이전트 (`agents/ui.py`)
- [x] QA Evaluator 에이전트 (`agents/qa.py`)
- [x] Product Owner 에이전트 (`agents/po.py`) — 오케스트레이션 허브

### Phase 5: Interactive REPL & Conversational Loop
- [x] IR-011: 대화형 CLI (`harness chat`) — `prompt_toolkit` 기반 REPL
- [x] 에이전트와의 실시간 대화 및 피드백 루프 (`chat` 커맨드 내 while 루프)
- [x] 슬래시 커맨드 지원 (`/help`, `/reset`, `/quit`, `/exit`)
- [x] 로컬 세션 영속성 (`FileCheckpointer` + `.harness/` JSON 저장)
- [x] HITL (Human-In-The-Loop) 인터럽트 및 Manual Override 제공
- [x] Debug 모드 (`harness chat --debug`)

### Phase 6: Web Dashboard (기본 완성)
- [x] Vite + React + TypeScript + Tailwind v4 프론트엔드
- [x] FastAPI 백엔드 (`web.py`) + 정적 파일 서빙 통합
- [x] `harness web` 한 줄로 프론트+백 동시 가동
- [x] Zustand 전역 State Store (`useHarnessStore.ts`)
- [x] SSE 기반 실시간 에이전트 로그 스트리밍
- [x] GraphCanvas 노드 렌더링 + activeNode 하이라이트
- [x] FileExplorer (파일 트리 탐색 + 내용 미리보기)
- [x] ChatWorkspace (채팅 UI + HITL 승인 배너)
- [x] LogPanel (실시간 에이전트 로그 패널)

---

## � 진행 중 / 예정 Phase

### Phase 6.2: Web Dashboard 기능 완성
- [ ] **GraphCanvas 실시간 라우팅 애니메이션**: `next_agent` 값 기반 엣지 강조
- [ ] **GraphCanvas 노드 상태 색상 분리**: Active(파란) / Done(초록) / Error(빨간) / Idle(회색)
- [ ] **Sidebar 탭 전환 콘텐츠 연결**: `monitor` → GraphCanvas, `config` → `.harness/config.yaml`, `docs` → memory.md/timeline.md
- [ ] **StatusBar 실시간 연동**: 현재 노드명, 토큰 사용량, 마지막 완료 시각
- [ ] **LogPanel 에이전트별 탭 분리**: PO / SA / CD / UI / QA / DR
- [ ] **FileExplorer 자동 포커싱**: 에이전트가 편집 중인 파일로 자동 스크롤

### Phase 7: 멀티 모델 및 설정 고도화
- [ ] OpenAI, Anthropic 등 멀티 모델 지원
- [ ] Model Context Protocol (MCP) 연동
- [ ] 커스텀 스킬 (Prompt Templates) 확장 시스템
- [ ] **Agent-level System Prompt 지원**: 개별 에이전트 지시서 주입 기능
- [ ] **상세 모델 커스터마이징**: 에이전트 단위 Temperature / Max Tokens 설정
- [ ] **설정 파일 계층화**: 글로벌 설정과 프로젝트별 설정 분리

## 🛡️ Phase 8: 보안 및 실행 환경 강화
- [ ] **Sandbox 실행 환경**: 에이전트 생성 코드를 격리된 환경에서 실행 강제
- [ ] **파일 접근 권한 정교화 (Path Guard)**: 프로젝트 외부 파일 접근 차단 보강
- [ ] **민감 정보 스캔**: 생성 코드/로그에서 API 키 등 필터링
