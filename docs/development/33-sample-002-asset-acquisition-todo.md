# 33. Sample-002 Asset Acquisition TODO

## 목적

이 문서는 `meeting-audio-sample-002` 를 planned 상태에서 observed 상태로 올리기 위해 필요한 실제 자산 확보 작업을 정리한다.

## 대상 샘플

- 메타 파일:
  - [`samples/meeting-audio-sample-002.yaml`](./samples/meeting-audio-sample-002.yaml)
- 목표 유형:
  - `two_speaker`
  - `30초` 안팎
  - `office`
  - `light overlap`
  - `internal_only`

## 현재 상태

- `sample_status`: `planned`
- `storage_path`: `TBD`
- `whisper_observation_status`: `untested`
- `observation_note_path`: `""`

즉 메타는 잡혀 있지만 실제 파일과 관찰 노트는 아직 없다.

## 확보 조건

실제 자산은 아래 조건을 가능한 한 만족해야 한다.

1. 화자 수
   - 2명 대화가 분명해야 한다
2. 길이
   - `20초 ~ 40초` 범위가 우선
3. 환경
   - 일반 사무실 또는 비슷한 업무 대화 환경
4. 언어
   - 한국어 위주
5. 발화 구조
   - 화자 교대가 어느 정도 드러나야 한다
   - 겹침 발화는 있어도 `light` 수준이 적합하다
6. 개인정보
   - 공개 사용 가능하거나 익명화 가능한 자산이어야 한다

## 확보 후 해야 할 일

1. 실제 파일을 확보한다
2. [`samples/meeting-audio-sample-002.yaml`](./samples/meeting-audio-sample-002.yaml) 의 `storage_path` 를 채운다
3. 필요하면 길이, 환경, overlap 수준을 실제 자산에 맞게 조정한다
4. Whisper 전사를 한 번 돌린다
5. 관찰 노트를 새로 만든다
6. `sample_status` 를 `observed` 로 바꾼다
7. `whisper_observation_status` 와 `observation_note_path` 를 채운다

## 관찰 노트 생성 경로

관찰 노트는 아래 형식을 따른다.

- 기준 문서:
  - [`32-audio-sample-observation-note-format.md`](./32-audio-sample-observation-note-format.md)
- 권장 파일명:
  - `samples/meeting-audio-sample-002.observation.md`

## 현재 결론

sample-002는 지금 당장 구현 문제가 아니라 자산 확보 문제다.  
실제 2명 대화 파일만 확보되면 같은 문서 체계 안에서 바로 observed 샘플로 승격할 수 있다.

공통 절차는 [`35-audio-asset-acquisition-checklist.md`](./35-audio-asset-acquisition-checklist.md) 를 따른다.
후보 소스 조사 메모는 [`37-sample-002-source-investigation-note.md`](./37-sample-002-source-investigation-note.md) 를 따른다.
