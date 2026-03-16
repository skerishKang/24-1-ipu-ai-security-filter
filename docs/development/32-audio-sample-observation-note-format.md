# 32. Audio Sample Observation Note Format

## 목적

이 문서는 회의 녹음 / 다화자 음성 샘플을 실제로 전사해 본 뒤, 어떤 형식으로 관찰 메모를 남길지 표준 포맷을 정의한다.

## 왜 필요한가

샘플 메타는 샘플의 성격을 기록한다.  
하지만 실제 전사 결과와 품질 판단은 별도 관찰 메모로 남겨야 비교와 재검토가 가능하다.

즉 메타는 "샘플이 무엇인가"를 기록하고, 관찰 메모는 "돌려보니 어땠는가"를 기록한다.

## 현재 결론

관찰 메모는 아래 항목을 기본으로 사용한다.  
형식은 markdown 문서로 두고, 샘플 ID와 관찰 일시, 사용 모델, 실제 결과, 판정을 반드시 남긴다.

## 필수 항목

- `sample_id`
  - 어떤 샘플을 관찰했는지
- `observed_at`
  - 관찰 일시
- `environment`
  - `dev-local`, `demo-stack` 등
- `model`
  - 예: `whisper:small`
- `input_path`
  - 실제 입력 파일 경로
- `duration_seconds`
  - 실제 관찰 대상 길이
- `result_text`
  - 실제 전사 결과
- `judgement`
  - `usable-for-demo` | `observe-only`
- `notes`
  - 핵심 해석 메모

## 권장 항목

- `observation_note_path`
  - 메타 YAML에서 이 관찰 노트를 가리킬 때 쓰는 경로
- `detected_language`
  - 모델이 감지한 언어가 있으면 기록
- `expected_vs_actual`
  - 예상과 실제 차이
- `sensitive_content_check`
  - 민감정보가 있다면 어떤 부분이 문제였는지
- `diarization_relevance`
  - diarization 필요성이 드러났는지
- `next_action`
  - 다음 검토 포인트

## 예시 포맷

```md
# Observation Note

- sample_id: meeting-audio-sample-001
- observed_at: 2026-03-16
- environment: dev-local
- model: whisper:small
- input_path: /mnt/g/.../seg0000.wav
- duration_seconds: 5
- result_text: imps 그렇다면
- judgement: observe-only

## Notes

- 짧은 감탄/도입 구간에서 앞부분이 영어 비슷한 토큰으로 깨졌다.
- 한국어가 일부 보이지만 데모용 받아쓰기 품질로 말하긴 어렵다.

## Next Action

- 같은 화자의 다른 구간도 추가 관찰
- 2명 대화 샘플 확보 후 비교
```

## 운영 원칙

- 결과를 좋게 보정하지 않고 실제 출력을 그대로 적는다.
- `judgement` 는 반드시 `usable-for-demo` 또는 `observe-only` 중 하나로만 적는다.
- 메타 YAML과 관찰 메모는 서로 연결돼야 한다.
- 샘플이 `observed` 상태가 되면 관찰 메모 경로도 함께 남기는 것이 좋다.
- 권장 연결 필드 이름은 `observation_note_path` 다.

## 현재 결론

샘플 메타와 별도로 관찰 메모 포맷을 고정해야 이후 회의 녹음 / 다화자 평가가 비교 가능해진다.  
현재는 markdown 관찰 노트 형식이 가장 단순하고 실용적이다.
