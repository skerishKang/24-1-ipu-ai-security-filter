# 28. Long Audio Verification Policy

## 목적

이 문서는 긴 음성 검증선을 `기본 verification suite`에 넣을지, `opt-in 검증선`으로 분리할지 결정한 기준을 남긴다.

## 결론

현재 긴 음성 검증선은 `기본 verification suite`에 넣지 않고, `opt-in 검증선`으로 유지한다.

## 왜 기본 검증선에 넣지 않는가

### 1. 기본 verification의 목적과 다르다

기본 verification suite의 목적은 빠른 회귀 탐지다.  
긴 음성 벤치마크는 기능 회귀보다 환경 성능과 자산 상태를 보는 성격이 더 강하다.

### 2. 실행 시간이 무겁고 편차가 크다

- 현재 기준선도 `15초`, `30초` 샘플로 별도 측정했다.
- Whisper 모델 캐시, GPU/CPU, warm-state 여부에 따라 값이 크게 흔들릴 수 있다.
- 이런 검증을 매번 기본 suite에 넣으면 회귀선이 느려지고 노이즈가 커진다.

### 3. 외부 자산 경로 의존이 있다

- 현재 benchmark는 `49-1`의 음성 자산과 `48`의 Whisper 모델 경로를 재사용한다.
- dev-local에선 유효하지만, 모든 환경에서 공통 전제로 보기엔 아직 이르다.

### 4. 현재 제품 메시지도 아직 보수적이다

- 긴 음성은 아직 기본 지원이 아니다.
- 분할 후 사용 권장 단계에서, 긴 음성 검증선을 기본 CI/회귀선처럼 다루는 건 과하다.

## 현재 운영 규칙

### 기본 verification

- `run_verification_suite.sh`
- `run_verification_suite.bat`
- 포함 범위:
  - engine unit/quality
  - backend API
  - PDF quality
  - frontend smoke
  - frontend live integration

### opt-in 긴 음성 verification

- `python3 scripts/run_whisper_duration_benchmark.py`
- 필요 시 `run_verification_suite`에서 환경변수로 추가 실행

권장 예:

```bash
IPU_RUN_LONG_AUDIO_BENCHMARK=1 ./run_verification_suite.sh
```

## 현재 해석 기준

- 긴 음성 benchmark는 pass/fail 중심보다 관찰용 baseline에 가깝다.
- 값이 나빠졌다고 바로 기능 회귀라고 단정하지 않는다.
- baseline이 크게 흔들릴 때만 환경/성능 이슈로 별도 검토한다.

## 언제 기본 검증선으로 올릴 수 있나

아래 조건이 맞으면 재검토한다.

1. 긴 음성 샘플 자산을 표준 dev asset로 고정함
2. cold/warm 구분을 포함한 측정 방식이 안정화됨
3. 실행 시간 편차가 작아짐
4. 긴 음성이 실제 기본 제품 경로로 승격됨

## 현재 결론

지금 단계에서 긴 음성 검증선은 "돌릴 수는 있지만, 기본 회귀선에는 아직 무겁다"가 맞다.
