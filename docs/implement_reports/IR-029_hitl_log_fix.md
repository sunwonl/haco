# [IR-029] HITL 로그 접근 에러 수정

**날짜**: 2026-04-13  
**유형**: 버그 수정 (Reliability)

---

## 현상

HITL(Human-In-The-Loop) 승인 단계 진입 시 `Error: 'dict' object has no attribute 'agent_name'` 에러가 발생하며 비정상 종료됨.

## 원인

*   LangGraph의 체크포인터(`FileCheckpointer`)를 통해 상태를 복원할 때, `history_logs` 리스트 내의 Pydantic 모델들이 딕셔너리(`dict`) 형태로 역직렬화됨.
*   기존 `cli.py` 코드에서 이를 객체 속성 점 표기법(`last_log.agent_name`)으로 접근하려 하여 `AttributeError`가 발생함.

## 수정 내용

*   `src/harnesscore/cli.py`의 HITL 출력 로직 수정:
    1.  `hasattr`를 사용하여 객체 속성 여부를 먼저 확인.
    2.  속성이 없을 경우 `.get()` 메서드를 사용하여 딕셔너리 방식으로 안전하게 값을 추출하도록 보완.
    3.  예외 처리 블록을 추가하여 사소한 출력 에러로 인해 프로그램이 중단되지 않도록 방어 코드 작성.

---

## 검증 결과
*   상태 복원 후 HITL 단계에서 이전 작업 내역(에이전트 이름 및 상세 내용)이 정상적으로 출력되는 것 확인.
