# HarnessCore 구현 계획 (Implementation Roadmap)

> 마지막 업데이트: 2026-04-20

---

## 🎯 구현 우선순위 큐

> 기준: **제품 핵심 가치 > 난이도 대비 임팩트 > 의존성 순서**

| 순위 | ID | 항목 | 이유 |
|:---:|---|---|---|
| 순위 | ID | 항목 | 이유 |
|:---:|---|---|---|
| 1 | **WEB-03** | StatusBar 실시간 연동 | 노드 상태, 토큰 사용량 등 실행 정보 가시화 (빠른 구현 가능) |
| 2 | **IR-012** | MCP 서버 연동 | 외부 도구 확장성 및 생태계 연결 |
| 3 | **CFG-01** | 멀티 모델 지원 (OpenAI/Anthropic) | 모델별 성능 최적화 및 사용자 선택권 보장 |
| 4 | **WEB-02-B** | Config/Docs 탭 실제 구현 | 현재 더미 페이지로 되어 있는 설정/문서 탭의 기능 내재화 |
| 5 | **CFG-02** | 설정 파일 계층화 | 글로벌 vs 로컬 설정 병합 로직 (고도화 단계 필수) |
| 6 | **SEC-01** | 보안 강화 (Path Guard) | 외부 배포 전 필수 보안 레이어 |

---

## ✅ 완료

| IR | 내용 | 구현 위치 |
|---|---|---|
| **TEST-01** | E2E 전체 파이프라인 테스트 및 429 Retry 로직 | `tests/test_e2e_pipeline.py`, `agents/base.py` |
| **WEB-01** | GraphCanvas 실시간 애니메이션 및 커스텀 노드 | `GraphCanvas.tsx`, `useHarnessStore.ts` |
| **WEB-02** | Sidebar 탭 전환 및 더미 페이지 연동 | `App.tsx`, `Sidebar.tsx` |
| **WEB-03** | 가로 폭 조절 리사이저 (Resizable Splitter) | `App.tsx` (커스텀 드래그 로직) |
| **WEB-04** | LogPanel 탭 시스템 및 Graph 통합 | `LogPanel.tsx` (Tabs: Logs / State Graph) |
| **IR-013** | Skills 시스템 구축 및 프롬프트 주입 | `agents/base.py`, `.harness/skills/` |
| **WEB-05** | Artifact/Diff 뷰 + AutoFocus | `LogPanel.tsx`, `useHarnessStore.ts` |
| **UX-01** | HITL 가시성 강화 및 서버 안정화 | `ChatWorkspace.tsx`, `cli.py` (Reload OFF) |

---

## ⚠️ 부분 구현 / 방향 변경

| IR | 원래 계획 | 현재 상태 |
|---|---|---|
| IR-010 | PO→SA→DR→CD→QA 전체 E2E 루프 단일 시나리오 검증 | HITL/SSE/Tool 단위 테스트만 존재. **전체 E2E 시나리오 테스트 미작성** |
| IR-011 | Textual 기반 TUI 클라이언트 | `tui/` 디렉토리: `__init__.py`만 존재. `harness chat` (Rich 기반 CLI)로 **사실상 대체됨** |

---

## 🔲 미구현 — 다음 구현 대상

### IR-012: MCP 서버 연동
- `.harness/settings.json`의 `mcp_servers` 키가 이미 예약되어 있으나 실제 연결 로직 없음
- **구현 필요:**
  - [ ] `mcp_servers` 설정 읽어 부트스트래핑 시 연결하는 로직
  - [ ] MCP 노출 Tools를 에이전트 Tool 레지스트리에 동적 등록

### IR-013: Skills 시스템
- [ ] `.harness/skills/*.md` 파일을 읽어 에이전트 시스템 프롬프트에 자동 주입
- [ ] 프로젝트별 코딩 컨벤션 / 자주 쓰는 패턴 템플릿 적용

---

## 🆕 신규 필요 기능 (코드베이스 분석 결과 추가)

### WEB-01: GraphCanvas 실시간 라우팅
- [x] `next_agent` 값을 읽어서 **현재 라우팅 중인 엣지(화살표)를 실시간 애니메이션**으로 강조
- [x] 노드 상태별 색상 분리: `Active(파란)` / `Done(초록)` / `Error(빨간)` / `Idle(회색)`
- [x] 노드 내부에 에이전트별 마지막 작업 내용(Mini-log) 실시간 표시

### WEB-02: Sidebar 탭 콘텐츠 연결
현재 탭 클릭은 동작하나 `workspace` 외 콘텐츠가 비어있음

| 탭 (TabType) | 연결할 콘텐츠 |
|---|---|
| `monitor` | GraphCanvas + 에이전트 Live 상태 |
| `config` | `.harness/settings.json` 설정 뷰어/에디터 |
| `docs` | `.harness/memory.md` + `timeline.md` 뷰어 |

### WEB-03: StatusBar 실시간 연동
- [ ] 현재 실행 중인 노드 이름 표시 (현재 정적 텍스트)
- [ ] 전체 토큰 사용량 누적 표시
- [ ] 마지막 완료 시각 표시

### WEB-05: Artifact/Diff 뷰
- [ ] 에이전트가 생성한 출력물(Artifact)을 별도 창으로 확인
- [ ] `git diff` 유사한 형식의 파일 변경사항 시각화 탭 추가
- [ ] 에이전트가 현재 편집 중인 파일에 자동 포커싱

### CFG-01: 멀티 모델 지원
- [ ] OpenAI, Anthropic 등 `provider` 설정 기반 LLM 전환 (`llm.py` 확장)
- [ ] 에이전트 단위 Temperature / Max Tokens 커스터마이징

### CFG-02: 설정 파일 계층화
- [ ] 글로벌 설정 (`~/.harness/settings.json`) 과 프로젝트별 `.harness/settings.json` 분리 병합

### ✅ TEST-01: E2E 전체 파이프라인 테스트
- [x] PO → SA → DR → CD → QA 전체 루프 단일 시나리오 자동 검증 인프라 (`tests/test_e2e_pipeline.py`)
- [x] `base.py`에 Exponential Backoff 기반 LLM 재시도 로직 추가 (429 Rate Limit 대응)
- [x] `recursion_limit` 제동 확인

### SEC-01: 보안 강화
- [ ] Path Guard: 프로젝트 루트 외부 파일 접근 차단 로직 보강
- [ ] 민감 정보 스캔: 생성 코드/로그에서 API 키 등 필터링
- [ ] Sandbox 실행 환경 (선택적)
