# Engine

민감정보 탐지, 치환, 세션 매핑, 역치환을 담당하는 핵심 보안 엔진 영역이다. 현재는 수동 모드 `manual-preview` 흐름에 맞춘 최소 인터페이스와 placeholder 구현까지 들어간 상태다.

## 현재 구현 범위

- `detect(content, content_type="text", policy="default")`
- `replace(content, detections, session_id, strategy="strict_token")`
- `replace_with_local_rewrite(content, detections, session_id)` (Ollama 기반)
- `restore(content, session_id)`
- `build_report(detections, replacements, strategy="strict_token")`
- TTL이 적용된 세션 매핑 저장소
- 수동 모드 결과를 한 번에 조합하는 `ManualPreviewEngine`
- `unittest` 기반 최소 테스트

## 구조

```text
engine/
├── README.md
├── src/
│   ├── __init__.py
│   ├── contracts.py
│   ├── detector.py
│   ├── manual_preview_engine.py
│   ├── replacer.py
│   ├── report_builder.py
│   ├── restorer.py
│   └── session_store.py
└── tests/
    ├── quality_samples.py
    ├── test_manual_preview_engine.py
    └── test_quality_harness.py
```

## 모듈 역할

- `contracts.py`: detection, replacement, report, session mapping 데이터 계약
- `session_store.py`: 메모리/SQLite 기반 세션 매핑 저장소와 TTL 만료 관리
- `detector.py`: 정규식 기반 최소 민감정보 탐지
- `replacer.py`: 토큰 치환과 세션 매핑 저장
- `restorer.py`: 세션 매핑으로 역치환
- `report_builder.py`: 리포트 생성
- `manual_preview_engine.py`: 백엔드가 붙이기 쉬운 상위 엔진 인터페이스

## 테스트 실행

```bash
cd /mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-firewall
python3 -m unittest engine.tests.test_manual_preview_engine
python3 -m unittest engine.tests.test_quality_harness
```

## 품질 검증 실행

정규식 기반 placeholder 엔진이 현재 어떤 업무 문맥까지 잡는지 빠르게 확인하려면 아래 스크립트를 실행하면 된다.

```bash
cd /mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-firewall
python3 engine/scripts/run_quality_harness.py
```

현재 샘플 검증 범위:

- 이메일
- 전화번호
- 금액
- 직함 포함 이름
- 조직명
- 부서 업무 메모
- 계약 검토 문맥
- 고객 문의 문맥
- 내부 보고 문맥
- false positive 가능 문맥
- false negative 가능 문맥
- 복합 업무 문맥 1종
- OCR 유사 줄바꿈/공백 노이즈 문맥
- OCR 숫자/문자 혼동 관찰 문맥

샘플은 두 그룹으로 나뉜다.

- `baseline`: 현재 PoC 기준으로 최소한 안정적으로 잡혀야 하는 문맥
- `observe-only`: false positive / false negative 가능성을 일부러 드러내는 관찰용 문맥
- `ocr-baseline`: OCR 추출본처럼 줄바꿈과 공백이 흔들려도 현재 엔진이 잡아야 하는 문맥
- `ocr-observe`: OCR 숫자/문자 혼동 같은 아직 남겨둔 한계를 드러내는 관찰용 문맥

스크립트는 각 샘플에 대해 `default` 와 `strict_token` 을 모두 돌리고, 탐지 수, 치환 토큰, `report.strategy`, 치환 결과, `baseline_status` 를 사람이 읽기 쉽게 출력한다. 현재 `baseline` 통과 여부는 보수적 정책인 `strict_token` 기준으로 해석하는 것이 맞고, `default` 는 일부 타입만 alias 중심으로 보여주는 비교용 출력에 가깝다.

## 현재 한계

- 고품질 NER가 아니라 정규식 기반 placeholder 탐지다.
- 품질 harness는 "현재 어디까지 탐지되는지"를 반복 점검하는 기준선이며, 실제 정답 데이터셋 기반 평가까지는 아직 아니다.
- false positive / false negative 샘플은 현재 한계를 숨기지 않고 드러내기 위한 관찰용 기준선이다.
- 기본 세션 저장소는 메모리 기반이라 재시작 시 사라진다.
- SQLite 저장소를 쓰면 TTL 범위 내에서 프로세스 재시작 후에도 restore 를 이어갈 수 있다.
- 기본 TTL은 900초이며 backend 의 `IPU_SESSION_TTL_SECONDS` 설정으로 바꿀 수 있다.
- `local_rewrite`는 모델 품질에 따라 결과가 달라질 수 있어 universal default로 확정하기엔 아직 평가가 필요하다.
- 중복 표현, 문맥 기반 별칭, 문서/음성 처리 로직은 아직 비어 있다.

## TTL 동작

- 세션 매핑 저장소는 기본적으로 900초 TTL을 사용한다.
- 새 매핑이 저장되면 해당 세션의 만료 시각이 갱신된다.
- `get_mappings()` 와 `restore()` 는 만료된 세션을 자동으로 비우고 빈 결과처럼 처리한다.
- `cleanup_expired_sessions()` 를 호출하면 만료된 세션을 한 번에 정리할 수 있다.
- 현재 단계에서는 메모리 기반 기본값과 SQLite 기반 지속 저장 옵션을 함께 제공하며, backend 에서 TTL 값을 주입한다.

## backend 연동 포인트

- 백엔드 서비스 계층에서 `from engine.src.manual_preview_engine import ManualPreviewEngine` 로 import
- `manual_preview(content, session_id, content_type, policy, strategy)` 호출
- 반환값의 `detections`, `replacements`, `report` 구조는 현재 backend schema와 맞춰 둔 상태
- 이후 backend placeholder는 엔진 호출 결과를 감싸는 얇은 orchestration 계층으로 교체하면 된다

## policy 동작

- 현재 공식 preset은 `default`, `strict_token`, `local_rewrite` 세 가지다.
- `default`: 완화된 기본 정책이다. 현재는 `EMAIL`, `PHONE`, `PERSON` 만 탐지하고, 치환 토큰도 `[EMAIL_ALIAS_01]` 같은 alias 형태로 만든다.
- `strict_token`: 더 넓게 탐지하는 정책이다. 현재는 `EMAIL`, `PHONE`, `PERSON`, `ORG`, `AMOUNT` 를 모두 탐지하고, `[EMAIL_01]` 같은 타입 노출형 토큰으로 치환한다.
- `local_rewrite`: strict_token 수준의 탐지 범위를 사용하고, Ollama 로컬 모델이 생성한 문맥 기반 일반화 표현으로 치환한다. 모델 실패 시 deterministic generalized fallback을 사용한다.
- 세 정책 모두 응답 스키마는 같고, 차이는 `detections`, `replaced_text`, `replacements`, `report.total_detections`, `report.risk_level`, `report.strategy` 에 반영된다.
- preset 기준 문서는 `docs/development/17-security-policy-presets.md` 를 따른다.

현재 의도:

- `default` 는 과탐을 줄이고 사람이 읽기 쉬운 preview 를 우선한다.
- `strict_token` 은 더 많이 가리고, 토큰만 봐도 어떤 유형이 치환됐는지 드러나게 한다.

현재 `strict_token` 에서 비교적 잘 되는 범위:

- 일반 이메일과 `security at ipu dot co kr` 형태의 변형 이메일
- 휴대전화, 지역번호 전화, 공백/점 표기 전화번호
- `김민수 부장`, `본부장 김민수` 같은 직함 포함 실명
- `박지은에게 공유`, `김민수에게 전달` 같은 제한된 직함 없는 실명 전달 문맥
- `48,000,000원`, `3억 2천만원` 같은 계약/예산 금액 표현
- `(주)아이피유테크`, `주식회사 미래금융`, `미래전자` 같은 조직명

현재 한계:

- `default` 가 `ORG`, `AMOUNT` 를 놓칠 수 있으므로 보수적 비식별화가 필요한 문서에는 부족하다.
- `strict_token` 도 정규식 기반이라 별칭, 문맥형 개인정보, 더 복잡한 비정형 표기에는 여전히 약하다.
- 직함 없는 이름은 전달/공유 같은 제한된 문맥에서만 보수적으로 잡으며, 모든 실명을 일반화해서 탐지하지는 않는다.
- `sec.urity at ...` 같은 더 깨진 이메일, 일반 명사 기반 호칭, 문맥 의존적 엔터티는 여전히 미탐 가능성이 있다.
- alias 토큰은 읽기성은 좋지만 민감정보 유형을 완전히 숨기는 정책이라고 보기는 어렵다.
