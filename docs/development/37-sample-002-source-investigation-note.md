# 37. Sample-002 Source Investigation Note

## 목적

이 문서는 `meeting-audio-sample-002` 에 넣을 실제 2명 대화 자산을 어디서 찾을지 조사 방향을 정리한다.

## 대상 샘플

- 메타:
  - [`samples/meeting-audio-sample-002.yaml`](./samples/meeting-audio-sample-002.yaml)
- 관련 TODO:
  - [`33-sample-002-asset-acquisition-todo.md`](./33-sample-002-asset-acquisition-todo.md)

## 현재 결론

지금 단계에서는 실제 자산이 아직 없으므로, 먼저 후보 소스 범주를 좁히는 것이 맞다.  
우선순위는 "공개 사용 가능", "2명 대화가 분명", "20초~40초 발췌 가능" 순이다.

## 우선 조사 범주

### 1. 공개 인터뷰 / 대담 클립

- 장점:
  - 권한 이슈가 상대적으로 단순하다
  - 2명 대화 구조가 분명한 경우가 많다
- 조건:
  - 진행자 + 출연자 구조가 분명한 짧은 구간
  - 과한 음악/효과음 없는 구간

현재 판단:
- 가장 현실적인 1순위 후보

### 2. 팟캐스트 / 대화형 방송 발췌

- 장점:
  - 2명 이상 대화 자료가 많다
- 단점:
  - 배경음, 겹침 발화, 길이 문제 가능성

현재 판단:
- 2순위 후보

### 3. 사내/개인 업무 대화 녹음

- 장점:
  - 실제 업무 맥락과 가장 가깝다
- 단점:
  - 개인정보와 권한 이슈가 크다

현재 판단:
- 익명화와 권한 기준이 명확할 때만 고려
- 지금은 공개 자산보다 후순위

## 후보 소스 체크 기준

- 2명 대화가 분명한가
- `20초 ~ 40초` 발췌가 가능한가
- 한국어 위주인가
- 일반 사무실/업무 대화 느낌이 있는가
- 공개 사용 또는 익명화 가능 여부가 명확한가

## 확보 후 바로 할 일

1. 발췌 구간 확보
2. [`meeting-audio-sample-002.yaml`](./samples/meeting-audio-sample-002.yaml) `storage_path` 갱신
3. Whisper 1회 관찰
4. `meeting-audio-sample-002.observation.md` 작성

## 현재 결론

sample-002는 새 기능 구현보다 적절한 2명 대화 공개 자산을 고르는 일이 먼저다.  
현재 기준으로는 공개 인터뷰/대담 클립에서 짧은 2인 대화 구간을 찾는 것이 가장 현실적이다.

1차 shortlist는 [`39-sample-002-shortlist-note.md`](./39-sample-002-shortlist-note.md) 를 따른다.
