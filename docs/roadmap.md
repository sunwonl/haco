# HarnessCore 로드맵 (Roadmap)

HarnessCore AI의 개발 방향과 주요 마일스톤입니다.

## 🚀 마일스톤

### Phase 4: Core Agent Implementation (진행 중)
- [x] IR-004: 오케스트레이션 엔진 (LangGraph)
- [x] IR-005: System Architect 에이전트
- [ ] IR-006: Design Reviewer 에이전트
- [ ] IR-007: Core Developer 에이전트

### Phase 5: Interactive REPL & Conversational Loop (우선순위 상향)
- [ ] IR-011: 대화형 CLI (REPL) 인터페이스 보완
- [ ] 에이전트와의 실시간 대화 및 피드백 루프 강화
- [ ] 슬래시 커맨드 (/help, /reset, /undo 등) 지원
- [ ] 로컬 세션 영속성 관리

### Phase 6: Web Dashboard
- [ ] 에이전트 상태 실시간 대시보드
- [ ] 시각화된 노드 그래프 및 작업 로그
- [ ] 원클릭 배포 및 마이그레이션 도구

### Phase 7: 멀티 모델 및 MCP 지원
- [ ] OpenAI, Anthropic 등 멀티 모델 지원
- [ ] Model Context Protocol (MCP) 연동
- [ ] 커스텀 스킬 (Prompt Templates) 확장 시스템

## 🛡️ Phase 8: 보안 및 실행 환경 강화
코드 생성 엔진의 특성상 발생할 수 있는 보안 취약점을 방지하고 안전한 구동 환경을 조성합니다.
- [ ] **Sandbox 실행 환경**: 에이전트가 생성한 코드를 격리된 환경(Docker 또는 파이썬 가상환경)에서 실행하도록 강제.
- [ ] **파일 접근 권한 정교화 (Path Guard)**: 프로젝트 외부 파일에 대한 접근을 원격으로 차단하는 논리 보강.
- [ ] **민감 정보 스캔**: 생성된 코드나 로그에 API 키 등의 민감 정보가 포함되지 않도록 검수하는 필터링 도입.

## ⚙️ Phase 7: 고도화된 상세 설정 지원
에이전트별로 세밀한 동작 제어가 가능하도록 설정을 확장합니다.
- [ ] **Agent-level System Prompt 지원**: 각 에이전트에게 개별적인 작업 지시서(Instruction)를 주입할 수 있는 기능.
- [ ] **상세 모델 커스터마이징**: 에이전트 단위로 모델별 파라미터(Temperature, Max Tokens 등)를 다르게 설정 가능하도록 지원.
- [ ] **설정 파일 계층화**: 글로벌 설정과 프로젝트별 설정을 분리하여 관리 편의성 증대.
