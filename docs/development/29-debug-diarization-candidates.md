# 29. Debug Diarization Candidates

## 목적

이 문서는 IPU에서 다화자 음성의 debug-only diarization 후보를 검토하고, 지금 바로 도입할지 보류할지 기준을 남긴다.

## 현재 결론

현재 diarization은 제품 기본 기능이 아니라 `debug-only 후보 검토` 단계로 유지한다.

즉 지금은 아래처럼 본다.

- 기본 제품 경로: 미도입
- 공식 API 계약: 미도입
- UI 노출: 미도입
- 내부 조사: 가능

## 현재 환경 확인 결과

프로브 기준:

- 스크립트:
  - `python3 scripts/probe_diarization_tools.py`

현재 확인된 상태:

- CLI
  - `ffmpeg`: 있음
  - `python3`: 있음
- Python diarization 후보
  - `pyannote.audio`: 없음
  - `whisperx`: 없음
  - `speechbrain`: 없음
  - `resemblyzer`: 없음
  - `vosk`: 없음

또한 현재 `workdiary` 안에서 diarization 재사용 자산은 사실상 찾지 못했다.  
`49-1`에는 Whisper/STT 자산은 있지만, 화자 분리 파이프라인 자산은 없다.

## 후보별 판단

### 1. `pyannote.audio`

- 장점:
  - diarization 쪽 대표 후보
  - 화자 분리 실험에 가장 직접적
- 단점:
  - 추가 설치 부담이 크다
  - 모델/토큰/환경 의존성이 생길 수 있다
  - 지금 IPU 기본 경로엔 과하다

현재 판단:
- `가장 유력한 debug-only 후보`
- 하지만 `지금 바로 도입`은 아님

### 2. `whisperx`

- 장점:
  - Whisper 기반 확장이라 현재 맥락과 맞닿아 있다
  - timestamp/align/diarization 실험과 연결되기 쉽다
- 단점:
  - 역시 추가 설치와 의존성이 크다
  - 지금 plain text 전사 중심 구조를 빠르게 무겁게 만든다

현재 판단:
- `차선 debug-only 후보`
- timestamp/align을 같이 보고 싶을 때 재검토

### 3. `speechbrain` / `resemblyzer`

- 장점:
  - speaker embedding 실험에 쓸 수 있다
- 단점:
  - 지금 manual-preview 제품 목표와 직접 거리가 있다
  - 단독 도입 가치가 낮다

현재 판단:
- `지금은 후순위`

### 4. `vosk`

- 장점:
  - 가벼운 로컬 후보로 자주 거론된다
- 단점:
  - 현재 diarization 핵심 후보로 보기엔 약하다
  - 기존 Whisper 경로와도 바로 이어지지 않는다

현재 판단:
- `현재 diarization 후보로는 비우선`

## 현재 운영 기준

- diarization은 제품 기본 기능으로 말하지 않는다.
- debug-only 조사도 별도 브랜치/스크립트 수준으로 시작한다.
- 현재 backend `audio_transcriber.py` 계약은 plain text 전사만 유지한다.
- diarization 후보 조사는 `pyannote.audio -> whisperx` 순으로 보는 것이 맞다.

## 도입 전 필수 조건

1. 회의 녹음 샘플셋 확보
2. 다화자 기준 성공/실패 예시 정의
3. 설치/의존성 비용 검토
4. debug-only 출력 포맷 정의
5. 기본 API 계약과 분리 전략 확정

회의 녹음 샘플셋 기준은 [`30-meeting-audio-sample-set-policy.md`](./30-meeting-audio-sample-set-policy.md) 를 따른다.

## 현재 결론

지금 IPU에서 diarization은 "검토는 할 수 있지만 아직 붙이지 않는다"가 맞다.  
후보 우선순위는 `pyannote.audio`, 그 다음은 `whisperx`다.
