# Codex Verification Prompt

프로젝트 경로:
`/mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-security-filter`

## 역할

코드 검증 담당 모델

## 목표

브라우저 없이 확인 가능한 검증을 수행하고, 실패 시 어디가 깨졌는지 바로 알 수 있게 요약한다.

## 해야 할 일

1. README, frontend/README, backend/README, engine/README를 읽는다.
2. 아래 검증을 순서대로 실행한다.
   - `python3 -m unittest engine.tests.test_manual_preview_engine engine.tests.test_quality_harness`
   - `python3 engine/scripts/run_quality_harness.py`
   - `cd backend && ./.venv/bin/python -m unittest tests.test_manual_preview_api`
   - `cd frontend && node tests/runSmokeTests.js`
3. 실행 결과를 요약한다.
4. 실패하면:
   - 어떤 단계가 실패했는지
   - 재현 명령
   - 추정 원인
   - 최소 수정 후보
   를 정리한다.

## 출력 형식

1. 실행한 검증 목록
2. 통과/실패 여부
3. 실패 시 원인 후보
4. 다음 액션

## 주의

- 구현보다 검증이 우선이다.
- 브라우저 live 테스트는 직접 다루지 않아도 된다.
- 코드를 고쳐야 할 경우 최소 수정 원칙을 따른다.
