# [IR-033] 에이전트 역할 고도화 및 문서화 책임 분리 (Role Refinement & Doc Division)

**날짜**: 2026-04-14  
**단계**: Phase 9 — 에이전트 협업 체계 고도화

---

## 구현 내용

사용자의 요청에 따라 에이전트 간의 역할 경계를 명확히 하고, 특히 문서 작성 책임을 전문성 중심으로 재분배했습니다.

### 1. 에이전트별 문서 소유권(Ownership) 확립

| 에이전트 | 담당 문서 및 책임 범위 |
|---|---|
| **Product Owner (PO)** | `README.md`, `ROADMAP.md` 등 **사용자 관점**의 문서 전담. |
| **System Architect (SA)** | `.harness/arch_notes.md`, `SYSTEM_ARCHITECTURE.md`, API 명세 등 **기술 설계** 전담. |
| **Core Developer (CD)** | **소스코드(`*.py`) 및 단위 테스트** 구현 전용. 비기술 문서 작성 금지. |
| **Design Reviewer (DR)** | SA의 설계가 CD가 구현하기에 충분히 구체적인지(Actionability) 검증 추가. |

### 2. 코드 반영 사항

- **`po.py`, `sa.py`, `cd.py`, `dr.py`**: 각 에이전트의 내부 `SYSTEM_PROMPT`를 수정하여 위 boundaries를 명시적으로 지시함.
- **`cd.py`**: 구현 완료 후 `dev_notes.md`를 자동으로 작성하던 로직을 제거함 (문서 작성 최소화).
- **`PromptManager`**: `harness init` 시 사용되는 기본 지시서 템플릿(`get_default_templates`)을 새로운 역할 체계에 맞춰 업데이트함.

---

## 기대 효과

- **CD의 몰입도 향상**: 개발자가 문서 작성 부담 없이 완벽한 코드 구현에만 집중할 수 있음.
- **설계 품질 강화**: SA가 CD에게 넘기기 전 더 상세한 명세를 작성하도록 유도하며, DR이 이를 강력하게 필터링함.
- **사용성 개선**: PO가 작성하는 상위 수준 문서와 SA가 작성하는 하위 수준 문서의 톤앤매너가 분리됨.

---

## 다음 단계
- [ ] 실제 대규모 태스크를 통해 역할 분담이 의도대로 작동하는지 검증
- [ ] 에이전트 간의 '문서 참고' 지시사항 추가 보강
