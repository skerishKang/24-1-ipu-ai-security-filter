# 22. Audio Quality And Speed Baseline

## 목적

이 문서는 현재 IPU의 로컬 Whisper 음성 입력이 어느 정도 품질과 속도로 동작하는지, 아주 작은 기준선만 남기기 위한 문서다.

## 측정 환경 성격

- 환경: dev-local
- STT 엔진: `whisper:small`
- 모델 경로: `G:/Ddrive/BatangD/task/workdiary/48. 2024_성장지원/New_dev/models/whisper`
- 샘플 경로:
  - `/mnt/g/Ddrive/BatangD/task/workdiary/49-1-padiem-rnd/data/datasets/rvc_speaker_001/speaker_001/..._seg0000.wav`
- 샘플 길이:
  - `5.0초`

이 값은 운영 SLA가 아니라, 현재 로컬 환경에서 “이 정도는 된다”를 보여주는 baseline이다.

## 현재 확인된 결과

### 1. real whisper smoke

- 스크립트:
  - `python3 scripts/run_real_whisper_smoke.py`
- 결과:
  - Whisper 모델 로드 성공
  - 언어 감지: Korean
  - 전사 결과:
    - `놀라운`

해석:

- 빈 문자열은 아니므로 전사 경로 자체는 살아 있다.
- 다만 단일 5초 샘플 1개만으로 품질을 일반화할 수는 없다.

### 2. real audio API smoke

- 스크립트:
  - `python3 scripts/run_real_whisper_api_smoke.py`
- 결과:
  - `/api/v1/mode/manual-preview/audio` 성공
  - `Ran 1 test in 7.182s`

해석:

- 현재 로컬 기준으로는 “짧은 음성 샘플 -> Whisper 전사 -> manual-preview 응답”이 수 초 단위로 완료된다.
- 데모용 짧은 음성 입력에는 사용할 수 있다.

### 3. 15초 / 30초 benchmark

- 스크립트:
  - `python3 scripts/run_whisper_duration_benchmark.py`
- 입력 원본:
  - `49-1` 데이터셋의 약 `272.95초` wav
- 방식:
  - 같은 프로세스에서 `15초 -> 30초` 순서로 연속 측정
  - 즉 두 번째 값은 cold start가 아니라 warm-state 값이다

결과:

- `15초`
  - `elapsed_seconds: 9.555`
  - `text_length: 48`
  - `text_preview: 고데 forget about eh 그럼 저 물가 Remove 사는 힘드니까요 sauc!`
- `30초`
  - `elapsed_seconds: 1.043`
  - `text_length: 80`
  - `text_preview: 아 그러면 저는 음... 물가청소 아래... 산은 흔드니까요. 안녕 코스모 엠스파 카리나입니다. 지금부터 카리나의 코스모 톡톡을 시작하겠습니다.`

해석:

- `15초` 값은 모델이 이미 준비된 상태지만 첫 실제 긴 샘플 처리에 가까운 기준이다.
- `30초` 값은 같은 프로세스에서 뒤이어 돈 warm-state 값이라, `15초`와 단순 비교하면 안 된다.
- 다만 둘 다 “수십 초 음성도 현재 dev-local에선 데모 검증은 가능하다”는 근거로는 쓸 수 있다.

## 현재 품질 판단

### 바로 데모에 써도 되는 범위

- 짧은 음성 샘플
- 로컬 dev/demo 환경
- “음성을 넣으면 텍스트 전사 후 민감정보를 가린다”는 데모
- 15초 안팎 샘플

### 아직 과장하면 안 되는 범위

- 긴 회의 녹음
- 여러 화자 분리
- 정밀 자막 품질
- 단어 단위 timestamp 품질
- 노이즈 강한 음성
- cold start / warm start를 분리한 속도 보장

## 현재 속도 판단

- 첫 실행은 모델 다운로드 비용이 커서 느릴 수 있다.
- 모델이 이미 내려받아진 뒤에는 짧은 샘플 기준 수 초 단위 응답은 가능하다.
- 15초 benchmark는 약 `9.555초` 였고, 같은 프로세스에서 이어진 30초 benchmark는 약 `1.043초` 였다.
- 따라서 현재는 `짧은 음성 데모 가능`, `15초 안팎 샘플도 dev-local 검증 가능`, `장시간 음성 운영 기준 미정`으로 보는 게 맞다.

## 운영 기준 제안

- 일반 데모:
  - 5초~15초 샘플 위주
- 내부 검증:
  - 30초 미만 샘플부터 확대
- 운영 보류:
  - 1분 이상 긴 음성은 별도 정책과 속도 검토 후

## 다음 검토 항목

1. 15초 / 30초 샘플 기준 속도 비교
2. 전사 텍스트 품질 샘플 3~5개 추가
3. 긴 음성 처리 정책 분리
4. segment / timestamp 활용 여부 결정

## 현재 결론

지금 기준으로 IPU 음성 입력은 “짧은 샘플을 로컬에서 전사해 manual-preview에 태우는 데모”까지는 된다.  
하지만 아직 장시간 음성이나 정밀 STT 품질을 약속할 단계는 아니다.

audio live integration을 기본 verification에 넣을지 여부는 [`23-audio-live-integration-policy.md`](./23-audio-live-integration-policy.md) 를 따른다.
