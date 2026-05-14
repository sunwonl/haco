# 🛰️ HarnessCore AI: Autonomous Multi-Agent Engine

> **"스스로 설계하고, 구현하고, 검증하며 진화하는 로컬 코드베이스 에이전트 엔진"**

HarnessCore AI는 단순한 코드 생성을 넘어, 고도화된 5명의 전문 에이전트가 협업하여 복잡한 소프트웨어 요구사항을 완성하는 **자가 반복형(Self-Iterative) 멀티 에이전트 플랫폼**입니다.

---

## 🌟 핵심 가치 (Core Philosophy)

- **로컬 코드베이스 우선**: 사용자 환경의 로컬 파일시스템 위에서 직접 작동하며 코드를 빌드하고 테스트합니다.
- **자율적 루프**: 요구사항이 충족될 때까지 계획(Plan) -> 생성(Generate) -> 검증(Evaluate) 루프를 스스로 반복합니다.
- **투명한 추론**: 모든 에이전트의 사고 과정(Thought), 행동(Action), 결과(Result)를 실시간으로 관찰하고 개입할 수 있습니다.
- **무한한 확장성**: MCP(Model Context Protocol)와 동적 스킬 시스템을 통해 에이전트에게 새로운 도구와 지식을 즉시 부여할 수 있습니다.

---

## 🏗️ 멀티 에이전트 팀 (The Team)

HarnessCore는 각 분야의 전문가들로 구성된 팀처럼 동작합니다:

1. 👨‍✈️ **Product Owner (PO)**: 요구사항 분석, 태스크 정의 및 팀 조율.
2. 🏗️ **System Architect (SA)**: 전체 아키텍처 설계, 파일 구조 및 인터페이스 정의.
3. 💻 **Core Developer (CD)**: 설계에 기반한 실제 코드 구현 및 리팩토링.
4. 🧪 **QA Evaluator (QA)**: 단위 테스트 작성 및 코드 안정성 검증.
5. 🎨 **UI Engineer (UI)**: 고도화된 프론트엔드 컴포넌트 및 심미적 디자인 구현.

---

## 🚀 시작하기 (Getting Started)

### 1. 설치
```bash
git clone https://github.com/sunwonl/haco.git
cd haco
./deploy.sh
```

### 2. 프로젝트 초기화
```bash
harness init
```
`.env` 파일에 `GEMINI_API_KEY`를 설정하세요.

### 3. 실행 (Web Dashboard)
```bash
# 백엔드 서버 실행
python -m harnesscore.web
```
브라우저에서 `http://localhost:8000`에 접속하여 화려한 대시보드를 만나보세요.

---

## 🛠️ 주요 기능 가이드

### 1. 웹 대시보드 (Web UI)
- **Workspace**: 에이전트의 활동 내역을 타임라인 뷰로 실시간 모니터링합니다.
- **Console**: 에이전트의 내부 사고 과정(Thinking)과 실행 로그를 필터링하여 확인합니다.
- **Memory**: 세션 간에 공유되는 지식 베이스를 확인하고 관리합니다.

### 2. 설정 및 확장 (Configuration)
우측 상단의 **[Settings]** 메뉴를 통해 시스템을 튜닝할 수 있습니다.
- **General**: LLM 모델 선택 및 프로젝트 설정.
- **MCP Servers**: 외부 도구(GitHub, Slack 등) 연동을 위한 MCP 서버 등록.
- **Skills**: 에이전트에게 주입할 특수한 업무 규칙 및 가이드라인 편집.

---

## 📚 상세 문서 (Documentation)

더 깊이 있는 정보는 다음 문서들을 참고하세요:

- 📖 [사용자 가이드 (User Guide)](./docs/user_guide.md)
- 🖥️ [UI 상세 매뉴얼 (UI Manual)](./docs/UI_MANUAL.md)
- 🛠️ [에이전트 확장 가이드 (MCP & Skills)](./docs/EXTENDING_AGENTS.md)
- 🏗️ [시스템 아키텍처 설계](./docs/SYSTEM_ARCHITECTURE.md)
- 📋 [프로젝트 로드맵](./docs/roadmap.md)

---

## 🛡️ 라이선스 (License)

HarnessCore AI는 **MIT License**를 따릅니다. 누구나 자유롭게 기여하고 확장할 수 있습니다.

---

> **"Build the Future of Coding with HarnessCore AI."**
