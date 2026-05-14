# 🛠️ 에이전트 확장 가이드: MCP & Skills

HarnessCore AI는 사용자가 직접 에이전트의 능력을 확장할 수 있도록 설계되었습니다. 이 문서는 새로운 **MCP(Model Context Protocol) 도구**와 **스킬(Custom Instructions)**을 에이전트에게 부여하는 방법을 설명합니다.

---

## 1. MCP 서버 등록 (External Tools)

MCP를 사용하면 외부 시스템(GitHub, Slack, Database, Search Engine 등)의 도구를 에이전트에게 실시간으로 제공할 수 있습니다.

### UI를 통한 등록 방법
1. 웹 인터페이스 우측 상단의 **[설정(Settings)]** 아이콘을 클릭합니다.
2. **[MCP SERVERS]** 탭으로 이동합니다.
3. 다음 정보를 입력하고 **[Register Server]**를 클릭합니다.
   - **Assign To**: 도구를 사용할 에이전트 (예: `Core Developer`, `Product Owner` 또는 전역용 `Global`).
   - **Server Name**: 서버의 이름 (예: `memory-server`).
   - **Command**: 실행 명령어 (대부분 `npx`를 사용합니다).
   - **Args**: 실행 인자 (예: `-y @modelcontextprotocol/server-memory`).
4. 하단의 **[Persist MCP Connections]**를 눌러 설정을 저장합니다.

### 주요 MCP 서버 예시
- **메모리(Memory)**: `npx -y @modelcontextprotocol/server-memory`
- **파일 탐색(Filesystem)**: `npx -y @modelcontextprotocol/server-filesystem /path/to/project`
- **GitHub**: `npx -y @modelcontextprotocol/server-github` (API 토큰 설정 필요)

---

## 2. 에이전트 스킬 관리 (Custom Instructions)

스킬은 에이전트가 특정 작업을 수행할 때 따르는 **마크다운 기반의 지침(System Instructions)**입니다.

### UI를 통한 관리 방법
1. **[설정]** 모달의 **[SKILLS]** 탭으로 이동합니다.
2. 좌측 **Library**에서 수정할 스킬을 선택하거나 `+` 버튼을 눌러 새 스킬을 만듭니다.
3. 에디터에서 마크다운 형식으로 지침을 작성합니다.
4. **[Save Skill]**을 클릭하면 즉시 반영됩니다.

### 스킬 매핑 규칙
HarnessCore는 파일명을 기준으로 에이전트에게 스킬을 주입합니다.
- **`global.md`**: 모든 에이전트에게 공통으로 주입되는 규칙입니다. (예: 코딩 스타일 가이드)
- **`core_developer.md`**: Core Developer 에이전트에게만 주입됩니다.
- **`system_architect.md`**: System Architect 에이전트에게만 주입됩니다.
- (기타 에이전트 이름의 소문자/언더바 형식 파일명 사용)

### 스킬 작성 팁
- **명확한 역할 정의**: "당신은 TDD를 신봉하는 개발자입니다."
- **제약 사항 명시**: "모든 함수는 20라인을 넘지 않아야 합니다."
- **체크리스트 포함**: "배포 전 반드시 `npm run test`를 확인하세요."

---

## 3. 파일 기반 고급 설정

UI가 아닌 설정 파일을 직접 수정하여 관리할 수도 있습니다.

### MCP 설정 (`.harness/harness.json`)
```json
{
    "mcp_servers": {
        "Core Developer": [
            {
                "name": "github",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"]
            }
        ],
        "global": [
            {
                "name": "memory",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"]
            }
        ]
    }
}
```

### 스킬 파일 (`.harness/skills/*.md`)
`.harness/skills/` 디렉토리에 원하는 이름으로 마크다운 파일을 생성하면 시스템이 자동으로 인식하여 에이전트에게 지식을 전달합니다.

---

> [!TIP]
> 새로운 MCP 서버를 추가한 후 에이전트에게 "사용 가능한 MCP 도구 목록을 확인해줘"라고 요청하면 정상 연동 여부를 확인할 수 있습니다.
