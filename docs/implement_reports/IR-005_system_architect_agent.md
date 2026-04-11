# [IR-005] System Architect 에이전트 구현

**날짜**: 2026-04-11  
**단계**: Phase 2 — 에이전트 구현 (첫 번째 실제 작동 에이전트)

---

## 구현 내용

### 1. System Architect 노드 (`agents/sa.py`)

#### 구성 요소

| 항목 | 설명 |
|---|---|
| `SA_SYSTEM_PROMPT` | 코드베이스 분석, 아키텍처 문서 작성, task 완료 처리 역할 지시 |
| `SADecision` (Pydantic) | `reasoning`, `architecture_note`, `affected_files`, `resolved_task_ids` 추출 |
| `_gather_codebase_context()` | `FileIOTool.search_files`로 `.py` / `.md` 파일에서 관련 스니펫 수집 |
| `sa_node()` | LangGraph 노드 실행 함수 |

#### 실행 흐름

```
1. user_prompt 키워드로 코드베이스 검색 (FileIOTool)
2. 미완료 open_tasks 목록 구성
3. LLM 호출 (with_structured_output → SADecision)
4. 아키텍처 노트를 .harness/arch_notes.md 에 추가 저장
5. resolved_task_ids 를 completed_tasks 에 반영
6. next_agent = "PO" 로 제어 반환
```

### 2. 그래프 업데이트 (`graph.py`)
- `dummy_node("System Architect")` → `wrapped_sa` (실제 `sa_node`)로 교체.
- 다른 더미 노드들은 최소한 open task 하나를 `completed_tasks`에 추가하여 PO의 무한 루프 방지.

---

## 검증 결과

```
[PO] Analyzing project state and determining routing...
▶ Node Finished: PO
  Routing To: System Architect

[System Architect] Researching codebase and designing architecture...
[System Architect] Design complete. Resolved tasks: ['T1', 'T2', 'T3', 'T4', 'T5']
▶ Node Finished: System Architect
  Action: Architecture note written. Affected files: ['backend/calculator.py', 'backend/tests/test_calculator.py']
  Routing To: PO

[PO] Analyzing project state and determining routing...
▶ Node Finished: PO
  Action: Routed to FINISH. Reasoning: All listed tasks (T1~T5) are marked as completed.
  Routing To: FINISH

✓ Workflow Finished.
```

- ✅ PO → SA → PO → FINISH 전체 파이프라인 정상 동작 확인
- ✅ `.harness/arch_notes.md` 아키텍처 노트 자동 저장 확인
- ✅ 모든 태스크 완료 시 PO가 `FINISH`로 올바르게 라우팅되는 것 확인

---

## 다음 단계
- **IR-006**: Core Developer 에이전트 구현 (실제 파일 생성/수정 코드 작성)
