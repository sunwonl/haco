# HarnessCore - 개발 로드맵 및 구현 계획

> 마지막 업데이트: 2026-04-20  
> 이 파일은 다음 세션에서 이어서 사용하기 위한 개발 기록입니다.

---

## ✅ 완료된 작업들

### Phase 4~6: Agent 코어 구축
- LangGraph, FileCheckpointer, Agent Tools (File, Git, Shell, Network, Journal, Memory, Validation, ProcessControl) 구현
- PO, SA, CD, UI, QA, DR 6개 에이전트 완성 및 통합
- 모든 에이전트를 Generic ReAct Loop 템플릿으로 통합 (`base.py`)
- Debug 모드(`harness chat --debug`), HITL Breakpoints, 대화 세션(REPL) 구현
- Global Semantic Memory (`.harness/memory.md`) 자동 주입
- `harness init` — 프로젝트 초기화 및 `.harness/instructions/` 템플릿 생성
- `harness reset` — `.harness/` 초기화 (백업 옵션 포함)
- `harness cli` — 단발성 파이프라인 실행
- `harness chat` — 대화형 REPL (`/help`, `/reset`, `/quit`, `/exit` 슬래시 커맨드 포함)
- [x] REPL 인터페이스 (`harness chat`) 및 슬래시 커맨드 (/help, /reset, /quit) 구현
- [x] E2E 파이프라인 통합 테스트 인프라 및 엔진 견고화 (429 Retry) 구현
- [x] 도구 목록: Shell, Network, FileIO, Git, PathGuard, Journaler

### Phase 7~8: Web UI 구축 (완료)
- Vite + React + TypeScript + Tailwind v4 프론트엔드 기반
- **Stitch 디자인** 기반 3열 레이아웃 (FileExplorer | ChatWorkspace | LogPanel)
- `src/harnesscore/web.py` FastAPI 백엔드 → 정적 파일 서빙 통합
  - `harness web` 한 줄로 프론트+백 동시 가동
- **Zustand** 전역 State Store (`useHarnessStore.ts`) 중앙화

### Phase 8.1: 백엔드 API 완성 (완료)
| 엔드포인트 | 역할 |
|---|---|
| `GET /api/health` | 프론트엔드 연결 상태 폴링 (5초 주기) |
| `GET /api/files?path=.` | CWD 기준 파일 트리 리스팅 |
| `GET /api/files/content?path=...` | 파일 내용 읽기 |
| `POST /api/interrupt/{thread_id}` | HITL 승인 후 그래프 재개 (SSE 반환) |
| `GET /api/state/{thread_id}` | 브라우저 새로고침 후 회화 기록 복원 |

---

## 🔜 Phase 8.2: 채팅창 외 UI 요소 기능 구현

### 우선순위 순서 (높은 순)

#### **1순위 — GraphCanvas 실시간 연동** `frontend/src/components/GraphCanvas.tsx`
이 프로젝트의 핵심 차별점. 에이전트가 어디에서 어디로 이동하는지 실시간으로 시각화.

현재 상태:
- `@xyflow/react` 기반 6개 노드 렌더링 ✅
- `activeNode`에 따라 노드 하이라이트 ✅

부족한 부분 (구현 필요):
- [ ] `next_agent` 값을 읽어서 **현재 라우팅 중인 엣지(화살표)를 실시간 애니메이션**으로 강조
- [ ] 노드 상태별 색상 분리: `Active(파란)` / `Done(초록)` / `Error(빨간)` / `Idle(회색)`
- [ ] 노드 호버 시 마지막 실행 로그를 툴팁으로 표시
- [ ] `monitoring` 탭 전환 시 중앙 패널에 GraphCanvas 노출

#### **2순위 — Sidebar 탭 전환 콘텐츠 연결**
현재 탭 클릭은 되지만 `workspace` 외 콘텐츠가 비어있음.

| 탭 | 전환할 콘텐츠 |
|---|---|
| `monitoring` | GraphCanvas + 에이전트 Live 상태 |
| `settings_suggest` | `.harness/config.yaml` 설정 뷰어 |
| `menu_book` | `.harness/memory.md` + `timeline.md` 뷰어 |

#### **3순위 — StatusBar 실시간 연동**
현재 정적 텍스트.

- [ ] 현재 실행 중인 노드 이름 표시
- [ ] 전체 토큰 사용량 누적 표시
- [ ] 마지막 완료 시각 표시

#### **4순위 — LogPanel 에이전트별 탭 분리**
현재 모든 에이전트 로그가 한 패널에 섞여 있음.

- [ ] 에이전트별 탭 분리 (PO | SA | CD | UI | QA | DR)
- [ ] 파일 Diff 뷰 (에이전트가 생성/편집한 파일 변경사항)

#### **5순위 — FileExplorer 자동 포커싱**
- [ ] 에이전트가 현재 편집 중인 파일에 FileExplorer 자동 스크롤 및 하이라이트

#### **6순위 이후 — TopBar, Config 탭, Memory 탭**
- [ ] `Swarm / Runtime / Memory` 탭 클릭 시 뷰 전환
- [ ] Config 에디터 (`.harness/config.yaml` 읽기/쓰기)
- [ ] Memory 뷰어 (`.harness/memory.md`, 저널 파일)

---

## 🏗 아키텍처 핵심 원칙

### 1. CWD 바인딩 (워크스페이스 연동)
```
harness web 을 실행한 디렉토리 = 에이전트의 작업 루트
```
- `web.py`의 `_harness_dir()` 함수가 `os.getcwd()` 기준으로 `.harness` 폴더를 결정
- 에이전트의 모든 파일 접근은 이 CWD 기준으로 동작

### 2. 실시간 통신 구조 (REST + SSE 하이브리드)
```
사용자 입력 → POST /api/run → GET /api/stream/{thread_id} (SSE)
HITL 승인   → POST /api/interrupt/{thread_id}              (SSE 재개)
```
- **SSE**: 에이전트 로그, 노드 업데이트, 인터럽트 모두 단방향 스트리밍
- **REST**: 단발성 액션 (run, interrupt, files, state)

### 3. 프론트엔드 데이터 흐름
```
SSE payload
  └─ dispatchSSE() in useHarnessStore.ts
       ├─ Thought    → ChatWorkspace (회색 버블)
       ├─ Message    → ChatWorkspace (파란 버블)
       ├─ ToolAction → LogPanel (터미널 로그)
       ├─ Interrupt  → ChatWorkspace (노란 배너) + HITL 입력창 전환
       └─ node_update → GraphCanvas activeNode 업데이트
```

---

## 📁 주요 파일 경로

| 파일 | 역할 |
|---|---|
| `src/harnesscore/web.py` | FastAPI 백엔드 + 정적 서빙 |
| `src/harnesscore/agents/base.py` | 공통 ReAct 루프 템플릿 |
| `src/harnesscore/agents/po.py` | Product Owner 에이전트 |
| `frontend/src/store/useHarnessStore.ts` | Zustand 전역 상태 Store |
| `frontend/src/hooks/useHarnessEngine.ts` | SSE 연결 + API 호출 훅 |
| `frontend/src/components/GraphCanvas.tsx` | State Graph 시각화 |
| `frontend/src/components/FileExplorer.tsx` | 파일 탐색기 |
| `frontend/src/components/ChatWorkspace.tsx` | AI 채팅 중앙 패널 |
| `frontend/src/components/LogPanel.tsx` | 우측 실행 로그 패널 |
| `.harness/memory.md` | 전역 에이전트 메모리 |
| `.harness/instructions/*.md` | 에이전트별 커스텀 지시사항 |
