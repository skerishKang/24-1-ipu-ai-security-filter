# 34. Sample-003 Asset Acquisition TODO

## 목적

이 문서는 `meeting-audio-sample-003` 을 planned 상태에서 observed 상태로 올리기 위해 필요한 실제 자산 확보 작업을 정리한다.

## 대상 샘플

- 메타 파일:
  - [`samples/meeting-audio-sample-003.yaml`](./samples/meeting-audio-sample-003.yaml)
- 목표 유형:
  - `multi_speaker_meeting`
  - `3명 이상`
  - `180초` 안팎
  - `online_meeting_compressed`
  - `moderate overlap`
  - `not_for_demo`

## 현재 상태

- `sample_status`: `planned`
- `storage_path`: `TBD`
- `whisper_observation_status`: `untested`
- `observation_note_path`: `""`

즉 메타는 잡혀 있지만 실제 파일과 관찰 노트는 아직 없다.

## 확보 조건

실제 자산은 아래 조건을 가능한 한 만족해야 한다.

1. 화자 수
   - `3명 이상` 발화가 확인되는 회의성 녹음이어야 한다
2. 길이
   - 우선은 `90초 ~ 180초` 범위의 발췌 구간이 적합하다
   - 전체 회의 원본보다 발췌 구간을 먼저 확보한다
3. 환경
   - 온라인 회의 녹음 또는 유사한 압축 음성 환경이 우선
4. 언어
   - 한국어 위주, 필요하면 일부 영어 혼합 허용
5. 발화 구조
   - 화자 교대가 분명한 구간
   - 겹침 발화가 약간 포함돼도 좋지만, 너무 심한 구간은 첫 샘플로는 피한다
6. 민감정보
   - 이름, 직함, 연락처, 금액 같은 업무형 민감정보가 일부 들어 있는 편이 좋다
7. 개인정보/권한
   - 공개 사용 가능하거나 익명화 가능한 자산이어야 한다

## 확보 시 피해야 할 것

- 회의 전체 원본을 바로 샘플로 넣는 것
- 화자가 너무 많아 발화 구조조차 읽기 어려운 구간
- 잡음이 지나치게 심한 구간
- 개인정보 처리 기준이 불명확한 사내 실제 회의 원본

## 확보 후 해야 할 일

1. 실제 파일 또는 발췌 구간을 확보한다
2. [`samples/meeting-audio-sample-003.yaml`](./samples/meeting-audio-sample-003.yaml) 의 `storage_path` 를 채운다
3. 길이, 화자 수, 환경, overlap 수준을 실제 자산에 맞게 보정한다
4. Whisper plain-text 전사를 한 번 돌린다
5. 관찰 노트를 새로 만든다
6. `sample_status` 를 `observed` 로 바꾼다
7. `whisper_observation_status` 와 `observation_note_path` 를 채운다
8. 필요하면 `diarization_interest` 를 다시 조정한다

## 관찰 노트 생성 경로

관찰 노트는 아래 형식을 따른다.

- 기준 문서:
  - [`32-audio-sample-observation-note-format.md`](./32-audio-sample-observation-note-format.md)
- 권장 파일명:
  - `samples/meeting-audio-sample-003.observation.md`

## 현재 결론

sample-003는 다화자 회의 녹음 검토의 핵심 샘플이지만, 바로 구현보다 자산 확보와 발췌 구간 선정이 먼저다.  
우선은 `3명 이상`, `90초 ~ 180초`, `online meeting compressed`, `moderate overlap` 정도의 발췌 구간을 확보하는 것이 맞다.

공통 절차는 [`35-audio-asset-acquisition-checklist.md`](./35-audio-asset-acquisition-checklist.md) 를 따른다.
후보 소스 조사 메모는 [`38-sample-003-source-investigation-note.md`](./38-sample-003-source-investigation-note.md) 를 따른다.
