# [IR-025] PO 노드 UnboundLocalError 수정

**날짜**: 2026-04-13  
**유형**: 버그 수정 (Reliability)

---

## 현상

사용자 질문 시 `Error: cannot access local variable 'harness_dir' where it is not associated with a value` 에러가 발생하며 PO의 분석 단계에서 중단됨.

## 원인

*   `src/harnesscore/agents/po.py`의 `po_node` 함수 내에서 `harness_dir` 변수가 정의되기 전(함수 하단)에 상단(컨텍스트 로딩 로직)에서 먼저 참조됨.
*   지능형 컨텍스트 로더가 추가되면서 발생한 변수 범위(Scope) 선언 순서 문제임.

## 수정 내용

*   `harness_dir = project_root / ".harness"` 선언 로직을 `po_node` 함수의 최상단(툴 초기화 직후)으로 이동함.
*   이제 컨텍스트 로더가 안전하게 `harness_dir`를 참조하여 설계 및 구현 노트를 읽어올 수 있음.

---

## 검증 결과
*   `harness chat` 재실행 시 에러 없이 "현재 개발 중인 앱 내용"에 대해 정상적으로 답변하는 것 확인.
