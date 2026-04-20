# [IR-032] HITL UX 개선 및 초기화 로직 점검 (HITL UX & Init Refinement)

**날짜**: 2026-04-14  
**단계**: Phase 4 보완 — 사용자 경험(UX) 고도화

---

## 구현 내용

### 1. HITL (Human-In-The-Loop) 시각적 강화
에이전트가 승인을 요청하거나 모호한 상황에서 사용자 개입이 필요할 때, 일반 로그 메시지와 확연히 구분되도록 UI를 개선했습니다.

- **Panel 적용**: `rich.Panel`을 사용하여 테두리가 있는 박스 형태로 출력.
- **색상 구분**: `orange1` (오렌지색) 테두리와 `bold yellow` 타이틀을 사용하여 시인성 확보.
- **정보 구조화**:
  - `⮑ Previous Action`: 직전 에이전트가 수행한 작업 요약.
  - `↣ Next Plan`: 다음에 진행될 노드 정보.
  - `Pending Tasks`: 아직 남은 작업 목록 (최대 3개 표시).
- **입력 프롬프트 변경**: 기존 `Approval >` 에서 `Manual Override >` 로 변경하고 `yellow italic` 스타일 적용.

### 2. 초기화 명령어(`harness init`) 점검 및 보완
사용자의 요청에 따라 에이전트별 `instruction` 초기화 로직을 재확인했습니다.

- **자동 붓스트랩**: `.harness/instructions/` 폴더가 없을 경우 `PromptManager`의 기본 템플릿을 사용하여 에이전트별(`.md`) 파일을 자동 생성함.
- **.env 지원**: 초기화 시 `.env` 템플릿을 생성하며, `cli.py` 상단에서 `python-dotenv`를 통해 이를 자동으로 로드하도록 설정됨.

---

## 검증 결과

- `harness chat` 실행 중 HITL 발생 시 오렌지색 패널이 정상적으로 노출됨.
- `harness init` 실행 시 `instructions/` 폴더 내에 `po.md`, `core_developer.md` 등이 정상적으로 생성됨을 확인함.

---

## 다음 단계
- [ ] 에이전트별 세부 Instruction 고도화
- [ ] REPL 내에서 명령어(/help, /reset 등) 시각적 가이드 추가
