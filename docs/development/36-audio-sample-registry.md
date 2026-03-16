# 36. Audio Sample Registry

## 목적

이 문서는 현재 IPU 음성 샘플 자산을 한눈에 보는 레지스트리다.

## 사용 원칙

- 샘플 메타의 원본은 각 `samples/*.yaml` 이다.
- 이 문서는 현재 상태와 다음 액션을 빠르게 보는 운영 보드 역할을 한다.
- 상태가 바뀌면 먼저 메타 YAML을 갱신하고, 그 다음 이 레지스트리를 맞춘다.
- `priority` 는 현재 확보/관찰 우선순위를 뜻한다.

## 현재 레지스트리

| sample_id | title | source_type | priority | sample_status | whisper_observation_status | storage_path | next_action |
|---|---|---|---|---|---|---|
| `meeting-audio-sample-001` | 카리나 인터뷰 단일 화자 짧은 샘플 | `single_speaker` | `P3` | `observed` | `observe-only` | 있음 | 다른 단일 화자 구간 추가 관찰 |
| `meeting-audio-sample-002` | 2명 대화 업무 조율 샘플 후보 | `two_speaker` | `P1` | `planned` | `untested` | `TBD` | 실제 2명 대화 자산 확보 |
| `meeting-audio-sample-003` | 3명 이상 회의 녹음 샘플 후보 | `multi_speaker_meeting` | `P2` | `planned` | `untested` | `TBD` | 실제 3명 이상 회의 발췌 구간 확보 |

## priority 기준

- `P1`
  - 지금 가장 먼저 실제 자산을 확보해야 하는 샘플
- `P2`
  - 다음 순서로 확보할 샘플
- `P3`
  - 이미 관찰은 끝났고, 필요 시 보강 관찰만 하면 되는 샘플

## 상세 링크

### sample-001

- 메타:
  - [`samples/meeting-audio-sample-001.yaml`](./samples/meeting-audio-sample-001.yaml)
- 관찰 노트:
  - [`samples/meeting-audio-sample-001.observation.md`](./samples/meeting-audio-sample-001.observation.md)

### sample-002

- 메타:
  - [`samples/meeting-audio-sample-002.yaml`](./samples/meeting-audio-sample-002.yaml)
- 자산 확보 TODO:
  - [`33-sample-002-asset-acquisition-todo.md`](./33-sample-002-asset-acquisition-todo.md)
- 후보 소스 조사:
  - [`37-sample-002-source-investigation-note.md`](./37-sample-002-source-investigation-note.md)
- 1차 shortlist:
  - [`39-sample-002-shortlist-note.md`](./39-sample-002-shortlist-note.md)

### sample-003

- 메타:
  - [`samples/meeting-audio-sample-003.yaml`](./samples/meeting-audio-sample-003.yaml)
- 자산 확보 TODO:
  - [`34-sample-003-asset-acquisition-todo.md`](./34-sample-003-asset-acquisition-todo.md)
- 후보 소스 조사:
  - [`38-sample-003-source-investigation-note.md`](./38-sample-003-source-investigation-note.md)

## 현재 해석

- `sample-001` 은 이미 실제 관찰까지 끝난 기준선 샘플이다.
- `sample-002` 는 2명 대화 기준선이 비어 있어 현재 `P1` 이다.
- `sample-003` 은 회의성 다화자 샘플로 중요하지만, `sample-002` 다음 순서인 `P2` 다.
- `sample-001` 은 이미 observed 상태라 유지 관찰용 `P3` 로 둔다.

## 다음 운영 액션

1. `sample-002` 실제 자산 1건 확보
2. `sample-003` 실제 자산 1건 확보
3. 확보 후 observation note 작성
4. `planned -> observed` 승격

## 현재 결론

지금 audio sample 세트는 구조는 잡혔고, 실제 observed 샘플은 하나다.  
다음 병목은 문서가 아니라 `sample-002`, `sample-003` 의 실제 자산 확보다.
