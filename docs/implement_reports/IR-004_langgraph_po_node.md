# [IR-004] LangGraph 통합 및 PO 에이전트(Supervisor) 구현

**날짜**: 2026-04-11  
**단계**: Phase 2 — 기본 오케스트레이션 엔진 구축

---

## 구현 내용

### 1. LLM 팩토리 (`src/harnesscore/llm.py`)
`HarnessConfig` 설정을 기반으로 에이전트별로 알맞은 LLM 객체를 동적 생성하는 팩토리 함수 `get_llm()`을 구현했습니다.
- 기본적으로 `langchain-google-genai`의 `ChatGoogleGenerativeAI`를 반환합니다.
- 추후 OpenAI 등 타사 모델 확장을 염두에 둔 분기문을 제공합니다.
- `api_key`가 설정되어 있지 않을 경우 명확하게 에러를 던지도록 보호되어 있습니다.

### 2. PO 에이전트 노드 (`src/harnesscore/agents/po.py`)
HarnessCore의 두뇌 역할을 하는 PO(Product Owner) 노드를 정의했습니다.
- **프롬프트 전략**: 사용자 요구사항 분석, 작업(Task) 분할, 다음 실행 에이전트(`next_agent`) 라우팅 결정.
- **구조화된 출력 (Structured Output)**: LangChain의 `with_structured_output`과 Pydantic 스키마(`PORoutingDecision`)를 사용하여 파싱 오류 없이 의사결정을 추출합니다.
- `SystemState`에 `tasks`, `history_logs`, `next_agent` 속성을 업데이트하여 다음 단계로 상태를 이관합니다.

### 3. 메인 LangGraph 구성 (`src/harnesscore/graph.py`)
전역 상태를 순환시키는 중심 LangGraph (`StateGraph`)를 빌드합니다.
- `SystemState` Pydantic 모델을 Graph State로 사용합니다.
- `PO` 노드 등록 및 진입점(Entry Point) 설정.
- 미구현된 에이전트(`System Architect`, `Design Reviewer` 등)는 동작 확인을 위해 임시 `dummy_node` 형태로 그래프에 등록했습니다.
- `add_conditional_edges`를 사용해 PO가 응답한 `next_agent` 이름에 맞추어 분기하도록 설정했습니다.
- 작업자(Worker) 노드들은 실행 후 항상 다시 `PO`로 돌아오도록 `add_edge` 하방 라우팅을 구성했습니다.

### 4. CLI 연동 고도화 (`src/harnesscore/cli.py`)
`harness cli "..."` 명령에 실제 LangGraph 엔진을 연결했습니다.
- **루핑(Looping) 방지**: `.harness/settings.json`의 `max_iterations` 값을 읽어와 LangGraph의 `recursion_limit`에 주입 (무한 루프 방지).
- **.env 로드**: `python-dotenv` 의존성을 추가하고 `load_dotenv()`를 호출하여 `GEMINI_API_KEY` 등을 쉘 외부 파일에서 읽어올 수 있도록 처리.
- 실시간 터미널 출력(Streaming output)을 통해 각 에이전트의 실행 상황과 로그를 출력합니다.

---

## 검증 내역
- ✅ 환경 변수 `.env` 로딩 및 API 인증 과정 정상 동작 확인.
- ✅ 사용자 프롬프트 기반으로 PO의 의사 결정 및 하위 Dummy Node 로의 라우팅 정상 확인.
- ✅ Dummy Node를 통해 미수행 작업이 피드백될 때, PO가 지속적으로 작업을 요청하는 현상(State Machine 기반 에이전트 루핑 특성)을 확인하였으며, `recursion_limit`를 통해 제한됨(정상 동작 방어선 작동).

---

## 다음 단계
- **IR-005**: System Architect 에이전트 구현
  - Dummy Node 상태인 시스템 아키텍트를 실제 코드로 대체.
  - FileIOTool의 검색(`search_files`) 기능을 연결해 코드 문맥 파악 구조화 적용.
