# 21. Real Audio API Smoke

## 목적

이 문서는 실제 Whisper 전사를 거쳐 `/api/v1/mode/manual-preview/audio` 성공 경로를 확인하는 opt-in smoke 기준을 정리한다.

## 왜 별도 테스트인가

- Whisper 모델 로드와 전사는 무겁다.
- 샘플 음성 파일과 모델 경로가 로컬 자산에 의존한다.
- 따라서 기본 `unittest` 세트에는 넣지 않고, 환경변수로만 켜지는 smoke로 분리한다.

## 실행

```bash
cd /mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-firewall
python3 scripts/run_real_whisper_api_smoke.py
```

내부적으로는 아래를 수행한다.

- `IPU_RUN_REAL_AUDIO_SMOKE=1`
- `python -m unittest tests.test_manual_preview_audio_real`

## 성공 기준

- `/api/v1/mode/manual-preview/audio` 가 `200`을 반환한다.
- `original_text` 가 비어 있지 않다.
- `report`, `copy_ready_prompt` 를 포함한 manual-preview 응답 형태가 유지된다.

## 현재 결론

이 smoke는 로컬 Whisper가 실제 API orchestration까지 통과하는지 확인하는 운영용 검증선이다.

실제 데모 가능 범위와 속도 해석은 [`22-audio-quality-and-speed-baseline.md`](./22-audio-quality-and-speed-baseline.md) 를 따른다.
