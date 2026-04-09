# HarnessCore AI - Workflow Design

본 문서는 HarnessCore 멀티 에이전트 시스템의 **거시적 전체 워크플로(Macro Workflow)**와 각 에이전트의 **미시적 내부 워크플로(Micro Workflow)** 설계 명세입니다.

## 1. 매크로 워크플로 (Overall LangGraph Engine)
LangGraph의 StateGraph 기반으로 구동되는 최상위 오케스트레이션 구조입니다. **수퍼바이저 융합형 그래프(Supervisor Pattern)** 를 채택하여, 엔진 자체는 상태 전달과 라우팅, 예외 처리 인프라만을 직접적으로 관장합니다.

### 1.1 메인 그래프 로직 
1. **Entry Point**: 사용자의 프롬프트가 포함된 초기 State 객체 생성.
2. **[Node] PO (Supervisor)**: 전체 State를 분석해 다음에 이동할 노드를 결정(`next_agent`).
3. **[Conditional Edge]**: PO가 반환한 `next_agent` 패스에 따라 개별 에이전트 노드로 라우팅.
4. **[Node] Sub-Agents**: 설계자, 백엔드, 프론트엔드 등의 에이전트가 본인의 작업을 수행 후 완료되면 그래프 통제권을 라우터로 돌려보냄.
5. **[Evaluate Loop]**: 개발 노드(Generate) 완료 시 PO를 거쳐 Design Reviewer 또는 QA Evaluator 노드로 라우팅되어 검증 수행. 검증 피드백은 다시 개발 노드로 돌아가는 피드백 순환 (Feedback Loop) 엣지 형성.
6. **End Point**: PO가 더 이상 진행할 태스크가 없다고 판단(`next_agent == "FINISH"`)하면 작업을 확정 짓고 최종(End) 상태로 전이.

---

## 2. 미시적 내부 워크플로 (Micro Agent Workflow)

각 에이전트는 노드로 들어왔을 때, 본인만의 내부 LLM 추론 알고리즘(ReAct/Tool Calling)을 통해 작업을 수행합니다.

### 2.1 오케스트레이터(PO) 내부 워크플로
PO 노드가 호출되었을 때 내부에서 일어나는 능동적 판단 과정입니다.
1. **Context Reading**: `SystemState`에서 사용자의 원본 일감, 최근 에러 상태, 커밋 기록 등을 읽음.
2. **Task Evaluation (Planning)**: 
   - 현재 상황 평가.
   - 정보 불충분 시 `Ask_Human_Clarification` 도구 호출로 HITL(Human-In-The-Loop) 유저는 대기.
   - 남은 태스크 분할 및 보드 상태 갱신(`Update_Task_Board`).
3. **Routing Decision**: 구체적인 다음 작업자를 판단하여 메인 LangGraph 엔진으로 `{"next": "System Architect", ...}`의 데이터 딕셔너리 반환 및 에이전트 수행 종료.

### 2.2 생성/평가 에이전트 (Sub-Agent) 내부 워크플로
Core Developer (백엔드 에이전트)를 예시로 한 개별 작업 로직입니다.
1. **Understand Task**: PO가 넘겨준 태스크 프롬프트 파악.
2. **Action (Local Execution)**:
   - `Search_Codebase` 나 `View_File`로 기존 코드를 분석.
   - 로컬 툴(`Run_Bash_Command`, `Replace_Content`)을 연이어 호출하며 백엔드 코드(`main.py` 등) 수정 및 로컬 스크립트 기반 테스트 동작 검토.
3. **Observation & Self-Correction**:
   - `pytest` 등의 반환 로그를 분석. 만약 문법 에러나 테스트 실패 시 스스로 판단(Agent LLM 추론)하여 2번 단계로 돌아가 코드를 리팩터링 (Self-Correction 루프).
4. **Conclusion**:
   - 스스로 판단하기에 태스크가 완료되었다고 판단되면, 본인의 수행 로그(`TaskLog`)를 갱신하고, 메인 그래프로 진척 상태 리포트 반환.

---

## 3. 예외 및 시스템 복원 파이프라인 방침
*   **Structured Output (Pydantic) 파싱 실패**: 에이전트 LLM 응답이 특정 노드에서 Pydantic 스키마를 준수하지 못한 경우, 파서가 던진 Validation Error 로그를 시스템 프롬프트에 담아 즉시 동일 에이전트에게 재시도(Retry) 요청.
*   **무한 루프 제동 장치 (Max Limits)**: LangGraph 그래프의 `recursion_limit`을 엄격히 설정하여 에이전트 간 핑퐁 무한루프(예: 개발자가 계속 터지고 QA가 계속 빠꾸먹이는 현상) 발생 시 작업을 강제 인터럽트하고 유저에게 알람 전송.
