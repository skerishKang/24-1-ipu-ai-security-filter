# 20. Real Whisper Smoke

## 목적

이 문서는 IPU의 로컬 Whisper 연결이 실제 음성 샘플에서 도는지 빠르게 확인하는 최소 smoke 기준을 정리한다.

## 왜 자동 테스트에 넣지 않는가

- Whisper 모델 로드는 무겁다.
- 샘플 음성 파일은 로컬 자산 경로에 의존한다.
- dev-local에서는 괜찮지만 CI나 일반 backend unit test에는 너무 비싸다.

따라서 real whisper smoke는 `opt-in manual verification` 으로 둔다.

## 기본 샘플

현재 기본 샘플은 아래 5초 세그먼트다.

- `/mnt/g/Ddrive/BatangD/task/workdiary/49-1-padiem-rnd/data/datasets/rvc_speaker_001/speaker_001/..._seg0000.wav`

환경변수 `IPU_REAL_WHISPER_SMOKE_SAMPLE` 로 다른 샘플을 지정할 수 있다.

## 실행

```bash
cd /mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-security-filter
python3 scripts/run_real_whisper_smoke.py
```

## 성공 기준

- Whisper 모델이 로드된다.
- 샘플 오디오에서 빈 문자열이 아닌 전사 결과가 나온다.
- 결과 텍스트 길이와 대략적인 언어가 사람이 보기에도 말이 된다.

## 현재 결론

real whisper smoke는 API 전체 검증이 아니라, 로컬 STT 자산과 모델 경로가 실제로 살아 있는지 확인하는 운영용 체크다.

실측 기준선 정리는 [`22-audio-quality-and-speed-baseline.md`](./22-audio-quality-and-speed-baseline.md) 를 따른다.
