# 02. System Architecture

## 아키텍처 원칙

- 웹 기반 워크벤치를 중심으로 설계한다.
- 보안 엔진은 백엔드와 분리 가능한 독립 모듈로 둔다.
- 수동 모드가 기본이며, 자동 모드는 동일한 치환 파이프라인 위에 얹는다.
- 외부 모델 커넥터는 확장 포인트로만 정의한다.

## 상위 구성

```text
[Frontend Workbench]
        |
        v
[Backend API / Session / Upload Orchestration]
        |
        v
[Security Engine]
        |
        +--> [Detection]
        +--> [Redaction / Alias Replacement]
        +--> [Session Mapping Vault]
        +--> [Restoration]
        |
        +--> [Future: External Model Connector]
```

## 컴포넌트 역할

### Frontend

- 텍스트 입력, 파일 업로드, 음성 업로드 UI
- 치환 결과 확인 화면
- 탐지 리포트와 복사 가능한 프롬프트 제공
- 이후 자동 모드 전환과 응답 비교 UI 확장

### Backend

- 요청 검증과 세션 관리
- 파일 업로드 및 파서 오케스트레이션
- 엔진 호출과 결과 조합
- 자동 모드용 외부 모델 커넥터 인터페이스 보유

### Engine

- 민감정보 탐지
- 세션별 동적 치환
- 치환 매핑 저장
- 응답 역치환
- 정책 기반 필터링과 리포트 생성

## 처리 흐름

### 수동 모드

1. 사용자가 입력 또는 파일을 업로드한다.
2. 백엔드가 원문을 엔진에 전달한다.
3. 엔진이 민감정보 탐지와 치환을 수행한다.
4. 백엔드가 치환본, 탐지 리포트, 세션 식별자를 프론트엔드에 반환한다.
5. 사용자는 치환본을 검토하고 외부 AI에 직접 붙여넣는다.

### 자동 모드

1. 수동 모드와 동일하게 치환을 먼저 수행한다.
2. 백엔드가 치환본만 외부 모델 커넥터에 전달한다.
3. 응답을 수신한 뒤 엔진이 세션 매핑으로 역치환한다.
4. 프론트엔드에 복원된 응답과 보안 리포트를 함께 보여준다.

## 초기 인터페이스 초안

### Backend API

- `POST /api/v1/workbench/text`
- `POST /api/v1/workbench/file`
- `POST /api/v1/workbench/audio`
- `GET /api/v1/sessions/{session_id}`
- `POST /api/v1/mode/manual-preview`
- `POST /api/v1/mode/automatic-dispatch` (향후)

### Engine Service Contract

- `detect(content, content_type, policy)`
- `replace(detections, strategy, session_id)`
- `restore(content, session_id)`
- `build_report(detections, replacements)`

## 기존 secure-bridge에서 참고할 요소

- 수동 모드와 자동 모드를 분리한 처리 흐름
- 민감정보 탐지와 역치환을 분리한 엔진 개념
- 파일 처리, 음성 처리, 외부 모델 라우터를 별도 모듈로 떼는 방향

## 그대로 가져오지 않을 요소

- Electron 중심 UI 구조
- 기존 프로젝트의 파일 배치와 실행 방식
- 특정 외부 모델 종속 설계
