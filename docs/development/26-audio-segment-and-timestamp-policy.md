# 26. Audio Segment And Timestamp Policy

## 목적

이 문서는 현재 IPU manual-preview 음성 입력에서 `segment` 와 `timestamp` 를 어떻게 다룰지 결정한다.

## 현재 결론

지금 단계에서는 `segment` 와 `timestamp` 를 API 응답, UI, 리포트 표준에 올리지 않는다.

즉 현재 음성 입력은 아래까지만 책임진다.

- 음성 파일 업로드
- 로컬 Whisper 전사
- 전사 텍스트를 manual-preview 엔진에 전달
- 치환 결과와 리포트 반환

## 왜 지금 보류하는가

### 1. 현재 제품 핵심과 직접 연결되지 않는다

manual-preview의 현재 핵심은 "민감정보 탐지 / 치환 / 복원"이다.  
segment, timestamp는 도움이 될 수 있지만 지금 핵심 가치의 필수 구성요소는 아니다.

### 2. 전사 품질 자체가 아직 흔들린다

현재 짧은 한국어 샘플에서도 Whisper 결과가 흔들린다.  
이 상태에서 segment/timestamp를 노출하면 정밀도에 대한 과장이 먼저 생긴다.

### 3. 긴 음성 정책도 아직 보수적이다

현재는 `5초 ~ 15초` 데모, `30초 미만` 내부 검증, `1분 이상` 분할 권장 기준이다.  
긴 음성 정책이 안정화되기 전에는 segment/timestamp를 제품 계약으로 고정할 이유가 약하다.

### 4. UI와 스키마 복잡도를 올린다

segment/timestamp를 열면 아래가 함께 따라온다.

- API schema 변경
- frontend 결과 패널 확장
- timestamp 단위 표준 결정
- 검증선 추가
- 다화자/긴 음성 정책과 결합

지금은 이 비용보다 얻는 가치가 작다.

## 현재 운영 기준

### backend

- `TranscribedAudio` 는 현재 plain text 중심 계약으로 유지한다.
- Whisper 내부 결과에 segment 정보가 있더라도 manual-preview 기본 응답에는 올리지 않는다.
- 향후 필요 시에도 별도 opt-in field 또는 debug path로 먼저 검토한다.

### frontend

- 음성 입력 결과는 현재 텍스트 전사본과 치환 결과 중심으로 보여준다.
- 시간축 표시, 구간별 전사, subtitle UI는 열지 않는다.

### 문서/메시지

- 현재 제품 메시지는 "음성을 전사해 민감정보를 가린다"까지다.
- "구간별 자막"이나 "timestamp 기반 리뷰"를 현재 기능으로 말하지 않는다.

## 향후 승격 조건

아래가 확보되기 전에는 segment/timestamp를 기본 기능으로 승격하지 않는다.

1. 긴 음성 품질 기준선
2. 다화자 정책
3. timestamp 표준 형식 결정
4. 구간 단위 UI 설계
5. opt-in 검증선 추가

## 권장 다음 확장 순서

1. 긴 음성 전용 검증선 여부 결정
2. 다화자/회의 녹음 정책 분리
3. 필요 시 debug-only segment 응답 프로토타입
4. 그 다음에만 공식 API 계약 검토

현재 긴 음성 검증선 기준은 [`28-long-audio-verification-policy.md`](./28-long-audio-verification-policy.md) 를 따른다.

## 현재 결론

segment/timestamp는 유용할 수 있지만, 지금 IPU manual-preview의 기본 계약으로는 올리지 않는다.  
현재는 plain text 전사 후 치환 흐름에 집중하는 것이 맞다.
