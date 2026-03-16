# 35. Audio Asset Acquisition Checklist

## 목적

이 문서는 `sample-002`, `sample-003` 같은 planned 음성 샘플을 실제 자산으로 바꿀 때 공통으로 따라야 하는 체크리스트를 정리한다.

## 적용 대상

- [`33-sample-002-asset-acquisition-todo.md`](./33-sample-002-asset-acquisition-todo.md)
- [`34-sample-003-asset-acquisition-todo.md`](./34-sample-003-asset-acquisition-todo.md)

즉 개별 샘플별 조건은 각 TODO 문서를 따르고, 공통 절차는 이 문서를 따른다.

## 공통 체크리스트

### 1. 권한 / 개인정보 확인

- 공개 사용 가능 자산인지 확인
- 아니면 익명화 가능한 자산인지 확인
- 개인정보 처리 기준이 불명확하면 보류

### 2. 샘플 길이 확인

- 전체 원본을 바로 넣지 말고 발췌 구간부터 검토
- 샘플 길이가 각 메타 목표 범위와 크게 어긋나는지 확인

### 3. 화자 구조 확인

- 목표한 화자 수가 실제로 맞는지 확인
- 화자 교대가 최소한 관찰 가능한지 확인
- 겹침 발화가 지나치게 심하면 첫 관찰 샘플로는 보류

### 4. 환경 특성 기록

- `office`, `online_meeting_compressed`, `noisy` 등 환경을 메모
- 녹음 품질이 지나치게 나쁘면 별도 noisy 샘플로 분리

### 5. 메타 YAML 갱신

- `storage_path` 입력
- 실제 길이, 화자 수, 환경, overlap 수준 보정
- 필요하면 `demo_suitability`, `diarization_interest` 재조정

### 6. Whisper 전사 관찰

- plain-text 전사를 1회 수행
- 결과를 보정하지 않고 그대로 기록
- `whisper_observation_status` 를 갱신

### 7. 관찰 노트 작성

- [`32-audio-sample-observation-note-format.md`](./32-audio-sample-observation-note-format.md) 기준으로 작성
- `observation_note_path` 입력

### 8. 샘플 상태 승격

- 자산과 관찰 노트가 채워졌으면 `sample_status: observed`
- 아직 파일만 있고 관찰 노트가 없으면 `planned` 유지

## 보류 기준

아래 중 하나면 즉시 observed로 올리지 않는다.

- 개인정보 처리 기준이 불명확함
- 화자 수가 메타 목표와 크게 다름
- 샘플 길이가 지나치게 김
- 관찰 노트 없이 메타만 갱신하려는 경우
- 발화 구조가 너무 복잡해 첫 비교 샘플로 부적합함

## 현재 결론

sample-002와 sample-003의 차이는 샘플 조건에 있고, 자산 확보 절차 자체는 상당 부분 공통이다.  
따라서 앞으로 실제 파일을 구할 때는 먼저 이 체크리스트를 보고, 그 다음 개별 TODO 문서를 보는 흐름이 맞다.
