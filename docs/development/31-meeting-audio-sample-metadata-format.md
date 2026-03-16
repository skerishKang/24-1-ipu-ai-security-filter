# 31. Meeting Audio Sample Metadata Format

## 목적

이 문서는 회의 녹음 / 다화자 음성 샘플 1건을 어떤 필드로 기록할지 표준 메타 포맷을 정의한다.

## 왜 필요한가

샘플셋 확보 기준은 이미 정했지만, 샘플마다 같은 형식으로 메타를 남기지 않으면 이후 비교와 재검토가 어렵다.

즉 이 문서의 목적은 "샘플을 모으는 기준"이 아니라 "샘플 1건을 어떻게 기록할 것인가"를 고정하는 것이다.

## 현재 결론

회의 녹음 샘플 메타는 아래 공통 필드를 기본으로 사용한다.  
형식은 우선 `yaml` 또는 `markdown bullet`로 관리해도 되지만, 의미상 필드는 아래 이름을 유지한다.

바로 복사해 쓸 수 있는 템플릿 파일은 [`templates/meeting-audio-sample.template.yaml`](./templates/meeting-audio-sample.template.yaml) 에 둔다.
실제 seed sample 예시는 [`samples/meeting-audio-sample-001.yaml`](./samples/meeting-audio-sample-001.yaml) 에 둔다.
실제 전사 결과를 남기는 관찰 메모 형식은 [`32-audio-sample-observation-note-format.md`](./32-audio-sample-observation-note-format.md) 를 따른다.

## 필수 필드

- `sample_id`
  - 샘플 고유 ID
  - 예: `meeting-2speaker-001`
- `title`
  - 사람이 읽기 쉬운 짧은 이름
- `sample_status`
  - `planned` | `seed` | `observed`
- `source_type`
  - `single_speaker` | `two_speaker` | `multi_speaker_meeting`
- `duration_seconds`
  - 길이(초)
- `speaker_count`
  - 추정 화자 수
- `language_profile`
  - `ko` | `ko_en_mixed` 등
- `environment_profile`
  - `quiet_room` | `office` | `online_meeting_compressed` | `noisy`
- `overlap_level`
  - `none` | `light` | `moderate` | `heavy`
- `sensitive_content_profile`
  - `none` | `light` | `moderate` | `high`
- `demo_suitability`
  - `demo_ok` | `internal_only` | `not_for_demo`
- `diarization_interest`
  - `low` | `medium` | `high`
- `storage_path`
  - 실제 샘플 파일 경로 또는 관리 경로

## 권장 필드

- `notes`
  - 샘플 특이사항 메모
- `expected_risks`
  - 현재 샘플에서 예상되는 실패 포인트
- `whisper_observation_status`
  - `untested` | `usable-for-demo` | `observe-only`
- `privacy_status`
  - `public_ok` | `anonymized` | `restricted`
- `segment_ready`
  - `yes` | `no`
- `benchmark_ready`
  - `yes` | `no`
- `observation_note_path`
  - 실제 관찰 메모 문서 경로

## 분류 기준 해설

### `demo_suitability`

- `demo_ok`
  - 짧고 비교적 단순해서 데모에 써도 되는 샘플
- `internal_only`
  - 내부 검토에는 쓰지만 데모에는 과장 위험이 있는 샘플
- `not_for_demo`
  - 회의 전체본, noisy 샘플, 다화자 장시간 샘플 등

### `diarization_interest`

- `low`
  - diarization 없이도 충분히 해석 가능한 샘플
- `medium`
  - 화자 구분이 있으면 더 좋지만 필수는 아닌 샘플
- `high`
  - diarization 없이는 해석 가치가 크게 떨어지는 샘플

### `whisper_observation_status`

- `untested`
  - 아직 전사 관찰을 안 한 샘플
- `usable-for-demo`
  - plain-text 전사 품질이 현재 데모 기준에서 쓸 만한 샘플
- `observe-only`
  - 전사 결과는 기록하되 데모나 품질 주장에는 쓰지 않는 샘플

### `sample_status`

- `planned`
  - 메타만 먼저 잡혀 있고 실제 자산 또는 관찰값은 아직 없는 샘플
- `seed`
  - 샘플셋 구조를 여는 기준선 예시용 샘플
- `observed`
  - 실제 자산 경로와 관찰값까지 채워진 샘플

## 예시 포맷

```yaml
sample_id: meeting-2speaker-001
title: 두 명 대화 짧은 업무 조율
sample_status: planned
source_type: two_speaker
duration_seconds: 28
speaker_count: 2
language_profile: ko
environment_profile: office
overlap_level: light
sensitive_content_profile: moderate
demo_suitability: internal_only
diarization_interest: medium
storage_path: data/audio_samples/meeting-2speaker-001.wav
notes: 발화 교대는 비교적 분명하지만 중간에 겹침이 조금 있다.
expected_risks:
  - 고유명사 흔들림
  - 짧은 겹침 발화
whisper_observation_status: untested
privacy_status: anonymized
segment_ready: yes
benchmark_ready: no
observation_note_path: ""
```

## 운영 원칙

- 필드 이름은 고정하고, 값 집합은 가능한 한 제한한다.
- 자유서술은 `notes`, `expected_risks` 정도로만 둔다.
- 샘플을 더 모으기 전에도 메타 포맷부터 먼저 고정한다.
- `sample_status` 로 현재 단계가 `planned / seed / observed` 중 어디인지 항상 드러나게 한다.

## 현재 결론

회의 녹음 샘플 메타는 위 필드 기준으로 기록한다.  
다음 단계는 실제 샘플 3~6개에 이 포맷을 적용해 보는 것이다.
