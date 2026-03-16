# 18. Audio Intake Placeholder

## 목적

이 문서는 실제 STT 구현 전에 `manual-preview` 음성 입력 경로를 어디에 붙일지 고정한다.

## 현재 상태

- backend route:
  - `POST /api/v1/mode/manual-preview/audio`
- service:
  - `ManualPreviewService.build_audio_preview()`
- transcriber contract:
  - `backend/app/services/audio_transcriber.py`

초기에는 이 경로를 placeholder로 열었지만, 현재는 로컬 Whisper transcriber 를 연결한 상태다.
현재 제품 노출은 일반인/전문가 모드 모두 열려 있고, 검증은 기본 smoke와 opt-in real smoke를 분리해 운영한다.

## 현재 구조 의미

- 음성 파일 업로드 API 경로를 먼저 고정한다.
- 파일 파서와 별도로 STT 계층을 분리한다.
- 이후 로컬 STT 엔진 연결 시 route/service 계약을 다시 흔들지 않게 한다.

## transcriber contract

- 입력: `UploadFile`
- 출력: `TranscribedAudio`
  - `text`
  - `content_type`
  - `filename`
  - `engine_name`

즉 오디오 입력도 결국 `text -> manual-preview engine` 흐름으로 수렴한다.

## 현재 지원 포맷

현재 음성 경로가 고려하는 확장자는 아래다.

- `.wav`
- `.mp3`
- `.m4a`
- `.mp4`
- `.webm`

최대 크기 기준은 현재 파일 업로드와 같은 `100MB` 로 둔다.

## 현재 노출 기준

- backend route 는 실제로 연결돼 있다.
- frontend 는 일반인/전문가 모드 모두에서 음성 업로드를 노출한다.
- 일반인 모드에서는 결과 중심으로, 전문가 모드에서는 session/source 포함 내부 상태까지 보여준다.
- 기본 frontend smoke 는 mock route interception 으로 UI 상태만 확인한다.
- real whisper 검증은 별도 opt-in smoke 로 분리한다.

## 현재 후속 검토 항목

1. 긴 음성 전용 검증선 분리 여부 검토
2. 필요 시 debug-only segment 응답 실험
3. 필요 시 debug-only diarization 후보 검토

## 현재 결론

음성 업로드는 이제 backend 와 frontend 일반/전문가 모드까지 연결됐다.  
다만 운영 검증선은 아직 보수적으로 유지하고, real whisper 실측은 opt-in smoke로 분리하는 단계다.
긴 음성 기준은 [`25-long-audio-handling-policy.md`](./25-long-audio-handling-policy.md) 를 따른다.
segment / timestamp 기준은 [`26-audio-segment-and-timestamp-policy.md`](./26-audio-segment-and-timestamp-policy.md) 를 따른다.
다화자 / 회의 녹음 기준은 [`27-multi-speaker-and-meeting-audio-policy.md`](./27-multi-speaker-and-meeting-audio-policy.md) 를 따른다.
debug-only diarization 후보 기준은 [`29-debug-diarization-candidates.md`](./29-debug-diarization-candidates.md) 를 따른다.
