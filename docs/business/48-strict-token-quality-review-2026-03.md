# IPU AI 방화벽 strict_token Quality Review 2026-03

## 목적

이 문서는 `strict_token` 정책의 현재 엔진 품질 상태를 실제 검증 결과 기준으로 정리한 첫 품질 리뷰 문서다.  
목표는 현재 수준에서 어디까지 PoC에 사용할 수 있고, 어떤 한계를 아직 안고 있는지 기준선을 남기는 것이다.

## 리뷰 기본 정보

- 리뷰 날짜: 2026-03-14
- 리뷰 대상: `strict_token` policy
- 리뷰 범위:
  - 텍스트 입력
  - `.txt` 파일 preview와 동일한 엔진 경로
  - 탐지 / 치환 / 리포트
- 리뷰 입력 세트:
  - internal sample set
- quality harness baseline + observe-only samples
  - OCR-like baseline + OCR-like observe-only samples

## 현재 정책 정의

`strict_token`은 현재 기준으로 IPU AI 방화벽의 `초기 고객 PoC용 기준 정책`이다.

현재 의미:

- 탐지 범위:
  - EMAIL
  - PHONE
  - PERSON
  - ORG
  - AMOUNT
- 치환 방식:
  - `[EMAIL_01]`
  - `[PHONE_01]`
  - `[PERSON_01]`
  - `[ORG_01]`
  - `[AMOUNT_01]`
- 의도:
  - preview 가독성보다 보수적 비노출화와 설명 가능한 탐지를 우선

## 검증 결과 요약

### 테스트 결과

- `python3 -m unittest engine.tests.test_manual_preview_engine engine.tests.test_quality_harness`
  - `Ran 16 tests ... OK`
- `python3 engine/scripts/run_quality_harness.py`
  - 정상 실행

### baseline 판단

- strict_token 기준으로 현재 baseline 샘플은 전부 `baseline-pass`
- OCR-like baseline 샘플도 현재 strict_token 기준으로 `baseline-pass`
- backend PDF 품질 샘플도 현재 기준선에서 통과한다
- observe-only 샘플은 의도대로 현재 한계를 드러내는 용도로 유지

## 샘플 기준 품질 평가

## A. 탐지 품질

현재 strict_token은 다음 유형에 대해 기본적인 PoC 설명이 가능한 수준이다.

- 이메일
- 전화번호
- 금액
- 직함 포함 이름
- 일부 직함 없는 이름 문맥
- 조직명

특히 이번 개선으로 아래가 좋아졌다.

- `security at ipu dot co kr` 같은 변형 이메일 탐지
- `02 3456 7890`, `010.2222.3333` 같은 비정형 전화번호 탐지
- `3억 2천만원` 같은 한국어 혼합 금액 탐지
- `박지은에게 공유`, `김민수에게 전달` 같은 제한된 직함 없는 이름 문맥 탐지

## B. 치환 품질

현재 strict_token 치환은 PoC와 데모 기준으로는 충분히 설명 가능하다.

예:

- `[ORG_01]`
- `[PERSON_01]`
- `[EMAIL_01]`
- `[PHONE_01]`
- `[AMOUNT_01]`

장점:

- 어떤 타입이 가려졌는지 직관적으로 설명 가능하다
- 데모에서 결과를 보여주기 쉽다
- 보안팀과 현업 모두에게 동작 원리를 설명하기 좋다

한계:

- 자연스러운 alias 기반 문맥 유지보다는 타입 명시형 토큰에 가깝다
- 실제 자동 모드 고도화 단계에서는 더 섬세한 치환 전략이 필요할 수 있다

## C. 리포트 품질

현재 strict_token 기준 리포트는 다음 점에서 설명 가능하다.

- 탐지 수
- risk level
- strategy
- review status

특히 `report.strategy = strict_token` 이 실제로 현재 정책과 일치하므로, 프론트와 백엔드, 엔진 설명이 어긋나지 않는다.

현재 리포트 표준값은 `low-risk / moderate-risk / high-risk`, `alias / strict_token`, `clean / review-required` 로 고정한다.

## D. false positive / false negative 상태

### 줄어든 false negative

- 변형 이메일
- 비정형 전화번호
- 한국어 혼합 금액 표현
- 제한된 직함 없는 이름 문맥
- OCR 추출본처럼 줄바꿈과 공백이 흔들린 연락처/금액 문맥

### 줄어든 false positive

- `브랜드 대표` 문맥 PERSON 과탐 완화

### 아직 남겨둔 OCR 한계

- `O1O` 같은 숫자/문자 혼동 전화번호
- `security @ ipu . co.kr` 같은 공백 분리 이메일
- 텍스트 레이어 PDF 생성기에서 한글 금액 문자열 인코딩이 깨지는 합성 테스트 한계
- `협력기업`, `외부회사`, `중견기업` 같은 generic suffix ORG 과탐 완화
- `외부 담당에게` 같은 일반 명사 PERSON 과탐 완화

## 현재 강점

- 텍스트와 `.txt` 기반 수동 모드 데모에 반복 사용 가능
- 계약 검토, 내부 보고, 고객 문의 같은 전형적 업무 문맥을 설명 가능
- strict_token 기준으로는 baseline 품질이 안정적으로 유지됨
- quality harness가 있어 이후 회귀를 바로 확인할 수 있음

## 현재 약점

- 더 심하게 깨진 변형 이메일 표기에는 아직 약함
- 직함 없는 이름은 일부 업무 문맥에만 제한적으로 대응
- 조직명/사람명 경계가 매우 애매한 문장에서는 여전히 오탐/미탐 가능
- 문맥 이해형 NER가 아니라 규칙 기반 엔진이므로 별칭/은유/우회 표현엔 약함

## PoC 적합성 판단

### 판단

`Conditional Yes`

### 이유

- strict_token은 현재 기준으로 초기 고객 PoC와 데모에는 사용할 수 있다
- 다만 사용 범위는 `전형적인 한국어 업무 문맥`과 `설명 가능한 샘플`로 제한하는 것이 안전하다
- 보수적 정책 기준으로는 default 가 아니라 strict_token만 쓰는 것이 맞다

## 지금 바로 써도 되는 범위

- 내부 데모
- 초기 고객 미팅
- 제한된 부서 PoC
- 텍스트 중심 업무 문맥
- `.txt` 기반 간단 문서 preview

## 아직 조심해야 하는 범위

- 자유도가 높은 자연어 문장 전체에서 실명 탐지에 크게 의존하는 경우
- 매우 비정형적인 이메일/전화/금액 표기
- 프로젝트명, 별칭, 은유 표현이 많은 문장
- 정밀한 보안 정책 엔진이 필요한 환경

## 다음 개선 우선순위

### 1. 사람명/조직명 경계 충돌 보강

- 샘플 확대
- validator / 우선순위 규칙 조정

### 2. 변형 이메일 정규화 범위 확대

- 과탐을 늘리지 않는 선에서 추가 보강

### 3. 직함 없는 이름 탐지의 제한적 확장

- `전달`, `공유`, `회신`, `승인` 같은 업무 문맥 중심으로만 보수적으로 확대

## 결론

현재 `strict_token`은 `초기 고객 PoC에서 설명 가능한 baseline 정책`까지는 올라왔다고 볼 수 있다.  
아직 정밀한 정책 엔진이나 문맥 이해형 NER 수준은 아니지만, 전형적인 한국어 업무 문맥에서는 수동 모드 PoC와 데모에 사용할 수 있는 기준선이 형성되었다.
