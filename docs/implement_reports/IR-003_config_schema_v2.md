# [IR-003] 설정 스키마 개선 (Config Schema v2)

**날짜**: 2026-04-09  
**단계**: Phase 1 보완 — 설정 구조 고도화

---

## 배경

기존 `HarnessConfig`에 누락된 필수 설정 항목들을 식별하고 반영했습니다.

| 누락 항목 | 문제 |
|---|---|
| 에이전트별 모델 설정 | 단일 모델만 지원, 에이전트별 오버라이드 불가 |
| 인증 정보 설정 | API Key 참조 방법 미정의 |
| Git 브랜치 전략 | base_branch, auto_commit 설정 없음 |
| 에이전트별 파일 접근 경로 | Path Guard의 기준 경로 설정 없음 |

---

## 구현 내용 (`config/loader.py`)

### 신규 서브모델

#### `LLMConfig`
```json
{
  "provider": "google-genai",
  "default_model": "gemini-2.0-flash",
  "agent_models": {
    "PO": "gemini-2.5-pro"
  }
}
```
- `provider`: 멀티 프로바이더 확장 고려 (openai, anthropic, ollama 등 주석 추가)
- `default_model`: 모든 에이전트의 기본 모델
- `agent_models`: 에이전트 이름별 개별 오버라이드 (빈 dict = 전체 default 사용)
- `config.model_for_agent("PO")` 헬퍼로 라우팅 시 모델 결정 편의 제공

#### `CredentialsConfig`
```json
{
  "api_key_env": "GEMINI_API_KEY",
  "gcp_credentials_path": null
}
```
- **API Key를 파일에 직접 저장하지 않음** — 환경변수 이름만 참조 (보안)
- GCP ADC(Application Default Credentials) 경로 지정 옵션

#### `GitConfig`
```json
{
  "base_branch": "main",
  "auto_commit": true
}
```

#### `agent_paths`
```json
{
  "Core Developer": "backend/",
  "UI Engineer": "frontend/"
}
```
- FileIOTool의 Path Guard 기준 경로를 에이전트별로 제한하는 용도

---

## CLI 업데이트 (`cli.py`)

`harness init` 실행 시 인증 환경변수 자동 검증:

```
✓ Initialized .harness/settings.json
  Provider : google-genai
  Model    : gemini-2.0-flash

⚠  API key not found.
  Set the GEMINI_API_KEY environment variable before running agents.
  Example: export GEMINI_API_KEY=your-api-key
```

---

## 간과했던 가정 사항 기록

> **멀티 프로바이더 확장성**: 현재 `langchain-google-genai` 기반으로 구현하나, LangChain의 `BaseChatModel` 인터페이스를 통해 에이전트를 구현하면 OpenAI, Anthropic, Ollama 등으로의 교체가 코드 변경 없이 가능. `provider` 설정 필드를 이미 추가해 두었음.

---

## 다음 단계
- `IR-004`: LangGraph 그래프 및 PO 에이전트(Supervisor Node) 구현
