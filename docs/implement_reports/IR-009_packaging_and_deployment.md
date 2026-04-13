# IR-009: Packaging and Deployment

## 1. 개요 (Overview)
HarnessCore AI 엔진의 완성도를 높이고 독립적인 CLI 도구로서의 배포 가능성을 확보하기 위해 빌드 시스템(Build System)을 구축하고 설치 프로세스를 자동화했습니다.

## 2. 주요 구현 내용 (Implementation Details)

### 2.1 pyproject.toml 기반 빌드 시스템
- **Build Backend**: `hatchling`을 사용하여 표준화된 Python 패키징 구조를 적용했습니다.
- **Entry Points**: `harness = "harnesscore.cli:app"`을 통해 설치 후 터미널에서 즉시 엔진을 구동할 수 있도록 진입점을 등록했습니다.
- **Package Discovery**: `src-layout` 규칙에 따라 `harnesscore` 패키지가 올바르게 Wheel 파일에 포함되도록 설정을 최적화했습니다.

### 2.2 CLI 초기화 로직 보강 (harness init)
사용자 온보딩 경험을 개선하기 위해 `cli.py` 내의 `init` 명령어를 보강했습니다.
- **Git Check**: 프로젝트가 Git 리포지토리인지 확인하여 자동 커밋/롤백 기능의 가용성을 사전에 안내합니다.
- **Environment Template**: `.env` 파일이 없을 경우 LLM API 키 설정을 위한 템플릿을 자동 생성합니다.
- **Instruction**: 초기화 후 바로 실행할 수 있는 예시 명령어를 출력합니다.

### 2.3 자동화된 배포 스크립트 (deploy.sh)
개발 및 설치의 번거로움을 줄이기 위해 다음 과정을 자동화하는 쉘 스크립트를 작성했습니다.
1. 기존 빌드 결과물 정리 (`dist/`, `build/`)
2. `uv build`를 통한 최신 Wheel 및 sdist 파일 생성
3. `uv pip install`을 이용한 로컬 환경 강제 재설치
4. `harness --help`를 통한 설치 무결성 검증

## 3. 검증 결과 (Verification Results)
- **빌드 성공**: `dist/harnesscore-0.1.0-py3-none-any.whl` 생성 확인.
- **설치 성공**: 가상환경 내에서 `uv pip`를 통해 안정적으로 설치됨을 확인.
- **독립 실행**: `uv run harness cli "<prompt>"` 명령어로 멀티 에이전트 루프가 정상 작동함을 확인.

## 4. 향후 계획 (Next Steps)
- CI/CD 파이프라인(GitHub Actions) 연동을 통한 자동 릴리즈 구축.
- `harness web` 모드 구현을 위한 FastAPI + 프론트엔드 대시보드 통합.
