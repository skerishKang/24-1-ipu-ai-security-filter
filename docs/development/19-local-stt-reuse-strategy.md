# 19. Local STT Reuse Strategy

## 목적

이 문서는 IPU에서 로컬 STT를 새로 찾기보다, `workdiary` 안의 기존 Whisper 자산을 어떻게 재사용할지 정리한다.

## 결론

현재 1순위 로컬 STT 후보는 새 엔진이 아니라 기존 Whisper 자산 재사용이다.

- 실행 자산:
  - `49-1-padiem-rnd/modules/stt_whisper/run.py`
- 기존 설정:
  - `49-1-padiem-rnd/modules/stt_whisper/config/settings.yaml`
- 기존 모델 경로:
  - `G:/Ddrive/BatangD/task/workdiary/48. 2024_성장지원/New_dev/models/whisper`

## 왜 이 경로가 맞는가

- 현재 환경에 `whisper` CLI와 Python 모듈이 이미 있다.
- `ffmpeg` 도 이미 있다.
- `faster-whisper`, `vosk` 는 현재 설치돼 있지 않다.
- 따라서 추가 설치보다 기존 Whisper 자산 재사용이 가장 빠르다.

## IPU 연결 방식

- backend `audio_transcriber.py` 에 `WhisperAudioTranscriber` 를 둔다.
- 기본 transcriber 는 `IPU_AUDIO_TRANSCRIBER=whisper` 로 동작한다.
- 테스트나 비활성화 시에는 `IPU_AUDIO_TRANSCRIBER=placeholder` 로 강제한다.
- Whisper 모델 이름과 경로는 환경변수로 override 가능하되, 기본값은 기존 자산을 따른다.

## 현재 판단

### 바로 써도 되는 것

- 로컬 음성 -> 텍스트 전사 후 manual-preview 엔진 연결
- WSL/dev-local 환경에서의 기초 검증

### 아직 안 한 것

- 실제 음성 샘플 품질 벤치마크
- 긴 음성 파일 처리 정책
- segment / word timestamp 활용
- faster-whisper 전환 비교

현재 이 중 `긴 음성 파일 처리 정책` 과 `segment / word timestamp 활용` 은 별도 문서로 기준을 고정했다.
- 긴 음성: [`25-long-audio-handling-policy.md`](./25-long-audio-handling-policy.md)
- segment/timestamp: [`26-audio-segment-and-timestamp-policy.md`](./26-audio-segment-and-timestamp-policy.md)
- diarization 후보: [`29-debug-diarization-candidates.md`](./29-debug-diarization-candidates.md)

## 다음 순서

1. 실제 Whisper transcriber 경로 연결
2. 짧은 샘플 wav 기준 smoke 추가
3. STT 품질/속도 문서화

## 현재 결론

로컬 STT는 음성 입력이 필요할 때만 붙이면 된다. 붙일 경우에는 새 스택보다 기존 `49-1` Whisper 자산 재사용이 가장 현실적이다.
