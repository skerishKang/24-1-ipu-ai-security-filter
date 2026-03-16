# 23. Audio Live Integration Policy

## 목적

이 문서는 audio live integration을 `기본 검증선`에 넣을지, `opt-in 검증선`으로 유지할지 결정한 기준을 남긴다.

## 결론

현재 audio live integration은 `기본 검증선에 넣지 않고`, `opt-in 검증선`으로 유지한다.

## 이유

### 1. 로컬 Whisper 의존성이 무겁다

- 모델 다운로드 비용이 크다.
- 실행 환경마다 `whisper`, `torch`, 모델 캐시 상태가 다를 수 있다.
- 일반 verification suite에 넣으면 검증 시간이 불필요하게 커진다.

### 2. 로컬 자산 경로에 의존한다

- 현재 real audio smoke는 `49-1` 음성 샘플과 `48` 모델 경로를 재사용한다.
- 이 자산은 dev-local에선 유효하지만, 모든 환경의 공통 전제를 만들기엔 아직 이르다.

### 3. 기본 검증선의 목적과 다르다

- 기본 검증선은 빠르게 회귀를 잡는 것이 우선이다.
- audio whisper smoke는 기능 자체보다 환경 적합성 검증 성격이 더 크다.

## 현재 운영 규칙

- 기본 verification:
  - `run_verification_suite.sh`
  - engine / backend API / frontend smoke / frontend live integration
- opt-in audio verification:
  - `python3 scripts/run_real_whisper_smoke.py`
  - `python3 scripts/run_real_whisper_api_smoke.py`
  - 긴 음성 benchmark는 [`28-long-audio-verification-policy.md`](./28-long-audio-verification-policy.md) 를 따른다.

## 스크립트 정책

- `run_verification_suite.sh` 는 기본적으로 audio live smoke를 실행하지 않는다.
- 필요할 때만 환경변수로 audio smoke를 추가 실행한다.

권장 예:

```bash
IPU_RUN_AUDIO_LIVE_SMOKE=1 ./run_verification_suite.sh
```

## 언제 기본 검증선으로 올릴 수 있나

아래 조건이 맞으면 재검토한다.

1. whisper/runtime 의존성이 더 안정적으로 고정됨
2. 샘플 음성 자산 경로를 repo 또는 표준 dev asset로 고정함
3. audio smoke가 일관된 시간 안에 끝남
4. 일반 verification 시간 증가가 감당 가능함

## 현재 결론

지금 단계에서 audio live integration은 “기능 검증은 가능하지만, 기본 회귀선에는 아직 무겁다”가 맞다.
