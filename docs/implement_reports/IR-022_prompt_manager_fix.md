# [IR-022] PromptManager 암시적 None 반환 버그 수정

**날짜**: 2026-04-13  
**유형**: 버그 수정 (Reliability)

---

## 현상

에이전트(PO, SA 등) 실행 시 `can only concatenate str (not "NoneType") to str` 에러와 함께 프로세스가 중단되는 문제 발생.

## 원인

*   `src/harnesscore/utils/prompt_manager.py`의 `load_custom_instructions` 함수에서 대상을 찾지 못하거나 내용이 없을 경우 명시적인 반환값이 없어 파이썬 기본값인 `None`을 반환함.
*   에이전트 노드에서 시스템 프롬프트(str)와 해당 함수의 결과값(None)을 더하기 연산(+)하려 할 때 `TypeError`가 발생함.

## 수정 내용

*   `PromptManager.load_custom_instructions` 함수 끝에 `return ""`을 추가하여, 어떤 경우에도 문자열을 반환하도록 보장함.
*   이제 커스텀 지침 파일이 없더라도 에러 없이 기본 프롬프트로 정상 동작함.

---

## 검증 결과
*   `harness chat` 재실행 시 에러 없이 에이전트 분석 단계로 진입하는 것 확인.
