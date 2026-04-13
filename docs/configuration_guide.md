# Configuration Guide (settings.json)

HarnessCore의 동작 방식은 `.harness/settings.json` 파일을 통해 세밀하게 조정할 수 있습니다.

## 📂 설정 파일 구조

기본적으로 `harness init` 실행 시 생성되는 `settings.json`의 구조는 다음과 같습니다.

```json
{
  "llm": {
    "provider": "google-genai",
    "default_model": "gemini-2.5-flash",
    "agent_models": {}
  },
  "credentials": {
    "api_key_env": "GEMINI_API_KEY"
  },
  "git": {
    "base_branch": "main",
    "auto_commit": true
  },
  "max_iterations": 15,
  "ignore_patterns": [".git", "node_modules", ".harness"]
}
```

---

## ⚙️ 상세 필드 설명

### 1. LLM 설정 (`llm`)
- **`provider`**: 사용할 LLM 서비스 제공자 (현재 `google-genai` 지원).
- **`default_model`**: 모든 에이전트가 기본적으로 사용할 모델 (예: `gemini-2.5-flash`, `gemini-1.5-pro-002`).
- **`agent_models`**: 특정 에이전트에게 더 강력한 모델을 부여하고 싶을 때 사용합니다.
  - 예: `{"SA": "gemini-1.5-pro", "PO": "gemini-1.5-pro"}`

### 2. 인증 설정 (`credentials`)
- **`api_key_env`**: LLM API 키를 가져올 환경 변수 이름입니다. 기본값은 `GEMINI_API_KEY`입니다.

### 3. Git 설정 (`git`)
- **`base_branch`**: 에이전트가 작업을 시작할 기준 브랜치입니다.
- **`auto_commit`**: `true`일 경우, 에이전트가 작업을 성공적으로 마치면 자동으로 Git 커밋을 수행합니다.

### 4. 실행 제한 (`max_iterations`)
- 에이전트 루프가 무한 반복되는 것을 방지하기 위한 최대 QA 재시도 횟수입니다. 복잡한 프로젝트일수록 이 값을 높게 설정하는 것이 권장됩니다 (기본 15회).

### 5. 무시 패턴 (`ignore_patterns`)
- 에이전트가 코드 분석이나 파일 조작 시 접근하지 말아야 할 경로 목록입니다. `.git`, `node_modules` 등 대규모 디렉토리를 포함시켜 성능을 높일 수 있습니다.

---

## 🔐 환경 변수 (.env)

인공지능 모델 호출을 위해 프로젝트 루트에 `.env` 파일을 만들고 아래 내용을 포함해야 합니다.

```bash
GEMINI_API_KEY=your_key_here
```

---

## 🎨 대시보드 및 가독성 설정
- 하네스코어는 터미널 가독성을 위해 `Rich` 라이브러리를 사용합니다. 폰트나 색상 설정은 시스템 터미널 설정을 따릅니다.
- 저널 아이콘과 구조는 `src/harnesscore/utils/journaler.py`의 `icons` 맵을 수정하여 커스터마이징할 수 있습니다.
