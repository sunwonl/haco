# HarnessCore AI User Guide

HarnessCore AI는 스스로 코드를 설계, 구현, 검증하는 자가 반복형 멀티 에이전트 코딩 엔진입니다. 👨‍✈️ **PO**, 🏗️ **System Architect**, 💻 **Core Developer**, 🎨 **UI Engineer**, 🧪 **QA Evaluator**가 협업하여 사용자의 요구사항을 완성합니다.

## 🚀 빠른 시작 (Quick Start)

### 1. 설치
HarnessCore 레포지토리 루트에서 다음 명령어를 실행하여 로컬 환경에 설치합니다.
```bash
./deploy.sh
```

### 2. 프로젝트 초기화
새 프로젝트 디렉토리에서 HarnessCore를 사용하기 위해 환경을 초기화합니다.
```bash
uv run harness init
```
이 명령어는 `.harness/` 설정 디렉토리와 `.env` 템플릿 파일을 생성합니다.

### 3. API 키 설정
`.env` 파일을 열어 본인의 Google Gemini API 키를 입력합니다.
```text
GEMINI_API_KEY=your_real_api_key_here
```

### 4. 에이전트 실행
사용자 프롬프트와 함께 에이전트 파이프라인을 구동합니다.
```bash
uv run harness cli "간단한 계산기 앱을 Python으로 만들어줘"
```

---

## 🛠️ 주요 명령어 (Commands)

| 명령어 | 설명 |
| :--- | :--- |
| `harness init` | 프로젝트 초기 설정 및 `.harness/` 디렉토리 생성 |
| `harness cli "<prompt>"` | 멀티 에이전트 파이프라인 실행 (TUI 모드) |
| `harness --help` | 도움말 및 옵션 확인 |

---

## 📚 상세 가이드 (Advanced Guides)

시스템의 심층적인 이해와 확장을 위해 다음 문서들을 참고하세요.

- [에이전트 확장 가이드 (MCP & Skills)](./EXTENDING_AGENTS.md): 새로운 도구와 전문 지식을 추가하는 방법
- [UI 상세 매뉴얼 (UI Manual)](./UI_MANUAL.md): 웹 인터페이스 기능 및 조작법
- [프로젝트 관리 및 워크플로우](./WORKFLOW_DESIGN.md): 하네스코어의 협업 모델과 태스크 관리
- [시스템 아키텍처](./SYSTEM_ARCHITECTURE.md): 내부 엔진 및 설계 구조

---

## 🔍 활동 모니터링 (Observability)

에이전트가 어떤 작업을 수행하고 있는지 실시간으로 확인하려면 다음 파일을 모니터링하세요.

- **`.harness/journals.md`**: 에이전트별 활동 로그, 작업 근거(Reasoning), 토큰 사용량 등이 아이콘과 함께 인간이 읽기 쉬운 마크다운 형식으로 기록됩니다.
- **`.harness/state.json`**: 시스템의 현재 전체 상태(태스크 목록, 완료 여부, 전체 토큰 등)가 저장되는 기술적인 체크포인트 파일입니다.

---

## 💡 팁과 요령

- **Git 활용**: 하네스코어는 Git 리포지토리에서 가장 강력하게 동작합니다. 성공 시 자동 커밋을 수행하며, 실패 시 `git reset`을 고려한 작업을 진행합니다.
- **설계 검토**: 에이전트가 생성한 `.harness/arch_notes.md`를 통해 아키텍트가 어떤 설계를 했는지 직접 검토할 수 있습니다.
