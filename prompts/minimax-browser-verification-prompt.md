# Minimax Browser Verification Prompt

프로젝트 경로:
`G:\Ddrive\BatangD\task\workdiary\24-1-ipu-ai-security-filter`

## 역할

Windows 브라우저 검증 담당 모델

## 목표

실제 Windows 환경에서 frontend/backend가 함께 뜬 상태를 기준으로 브라우저 레벨 동작을 검증한다.

## 준비

1. `run_demo_stack.bat` 또는 수동 실행으로 backend/frontend를 띄운다.
2. backend:
   - `http://127.0.0.1:8241/health`
3. frontend:
   - `http://127.0.0.1:4241`

## 해야 할 일

1. 브라우저에서 frontend 첫 로드 확인
2. 텍스트 입력으로 preview 확인
3. `.txt` 파일 업로드로 preview 확인
4. `strict_token` policy 선택 후 결과 확인
5. 상태 메시지와 session/source 표시 확인
6. 가능하면 아래 자동화도 실행
   - `node tests\runSmokeTests.js`
   - `node tests\runLiveIntegrationTests.js`

## 꼭 확인할 항목

- 첫 로드 시 4영역 워크벤치 보이는지
- backend 연결 시 `backend` 또는 `backend-file` 표기
- backend 실패 시 `mock-fallback` 표기
- unsupported 파일 선택 시 에러 문구
- 빈 `.txt` 파일 선택 시 에러 문구
- `.txt` 업로드 성공 시 치환본 갱신

## 출력 형식

1. 수동 검증 결과
2. 자동화 검증 결과
3. 실제 화면 기준으로 이상했던 점
4. 재현 가능한 이슈
5. 다음 수정 우선순위
