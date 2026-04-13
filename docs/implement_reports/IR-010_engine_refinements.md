# IR-010: Engine Refinements (Token Tracking & Journaling)

## 1. 개요 (Overview)
멀티 에이전트 엔진의 실질적인 운영 비용(Cost)을 모니터링하고, 에이전트 활동의 투명성(Observability) 및 출처(Provenance)를 보장하기 위해 코어 엔진을 고도화했습니다.

## 2. 주요 구현 내용 (Implementation Details)

### 2.1 토큰 사용량 추적 (Token Usage Tracking)
- **Schema Update**: `SystemState`에 `total_tokens` 필드를 추가하고, 각 에이전트의 개별 호출 결과를 담는 `TaskLog`에도 `tokens` 정보를 동기화하도록 스키마를 확장했습니다.
- **Extraction Logic**: LangChain의 `invoke(include_raw=True)` 옵션을 활용하여 LLM 응답 메타데이터에서 `input_tokens`, `output_tokens`, `thinking_tokens`를 추출하는 `extract_token_usage` 유틸리티를 구현했습니다.
- **Aggregation**: 모든 에이전트 노드 실행 후 토큰 사용량을 누적하여 전체 프로젝트 비용을 계산할 수 있는 기반을 마련했습니다.

### 2.2 명시적 저널링 시스템 (Explicit Journaling)
자동화된 상태 저장 로그의 한계를 극복하기 위해 에이전트가 직접 자신의 활동을 기록하는 방식을 도입했습니다.
- **Journaler Utility**: [journaler.py](file:///home/sunwonl/haco/src/harnesscore/utils/journaler.py)를 신설하여 일관된 마크다운 포맷팅을 제공합니다.
- **Agent Integration**: `PO`, `SA`, `CD`, `UI`, `QA` 모든 노드에서 작업 완료 직전 자신의 아이콘, 액션명, 상세 근거(Reasoning), 영향받은 파일 목록을 저널에 기록합니다.
- **Observability**: `journals.md`를 통해 에이전트 간의 소통 과정과 실패 시의 피드백 루프를 인간이 읽기 쉬운 형태로 실시간 모니터링할 수 있습니다.

## 3. 검증 결과 (Verification Results)
- **정확한 출처 기록**: 로그 주체가 `loop` 대신 `System Architect`, `Core Developer` 등 실제 에이전트 이름으로 정확히 기록됨을 확인.
- **비용 통계**: 각 단계별 토큰 소모량이 상세히 표기되어 프로젝트 운영 비용 예측이 가능해짐.
- **가독성**: 아이콘과 구조화된 리스트를 통해 복잡한 멀티 에이전트 협업 과정을 한눈에 파악 가능.

## 4. 관련 파일 (Related Files)
- `src/harnesscore/utils/journaler.py`
- `src/harnesscore/llm.py`
- `src/harnesscore/schema.py`
- `.harness/journals.md`
