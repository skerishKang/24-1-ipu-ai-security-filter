# 24. Audio Transcription Quality Samples

## 목적

이 문서는 현재 로컬 Whisper가 실제 짧은 한국어 음성 샘플에서 어떤 전사 결과를 내는지 관찰용 기준선을 남긴다.

## 방법

- 스크립트:
  - `python3 scripts/run_whisper_quality_samples.py`
- 엔진:
  - `whisper:small`
- 샘플:
  - `49-1-padiem-rnd`의 `*_seg0000.wav ~ *_seg0003.wav`

이 문서는 정답 대비 WER 평가가 아니라, 현재 결과를 숨기지 않고 기록하는 관찰용 baseline이다.

## 현재 관찰 결과

아래 결과는 현재 dev-local에서 얻은 실제 전사 결과를 적는다.

### sample 1

- 파일:
  - `..._seg0000.wav`
- 결과:
  - `imps 그렇다면`
- 판정:
  - `observe-only`

메모:

- 한국어가 일부 보이지만 앞부분이 영어 비슷한 토큰으로 깨진다.
- 짧은 감탄/도입 구간에서는 현재 `whisper:small` 결과가 흔들릴 수 있다.

### sample 2

- 파일:
  - `..._seg0001.wav`
- 결과:
  - `나도 presented 사는 힘든 High-stons wheat supermarket thee m s`
- 판정:
  - `observe-only`

메모:

- 한국어/영어가 섞여 나오고 의미 보존이 약하다.
- 데모에서 “정확한 받아쓰기” 용도로 과장하면 안 된다.

### sample 3

- 파일:
  - `..._seg0002.wav`
- 결과:
  - `with those guys and wife LOUPA promise I've guessed that must've been the heart變 food`
- 판정:
  - `observe-only`

메모:

- 언어 감지가 English로 기울었고, 한국어 발화를 영어 잡음처럼 처리한 것으로 보인다.
- 현재 설정에서 이런 샘플은 보안 데모용 전사로는 불안정하다.

### sample 4

- 파일:
  - `..._seg0003.wav`
- 결과:
  - `Woooowww! Aada!`
- 판정:
  - `observe-only`

메모:

- 감탄/짧은 발화 구간은 텍스트 품질이 매우 흔들린다.
- 이런 샘플은 “음성 입력도 된다” 수준 시연엔 쓸 수 있어도, 전사 품질 데모엔 부적합하다.

## 해석 기준

- 문장이 대략 맞으면 `usable-for-demo`
- 핵심 고유명사나 문장 구조가 심하게 깨지면 `observe-only`
- 이후 샘플이 늘어나면 `usable-for-demo / observe-only`를 더 명확히 분리한다.

## 현재 결론

현재 4개 짧은 샘플 기준으로는 `whisper:small` 전사 품질이 꽤 흔들린다.  
즉 “음성을 넣어 manual-preview까지 연결된다”는 데모는 가능하지만, “짧은 한국어 음성도 안정적으로 잘 받아쓴다”는 메시지는 아직 과장이다.
