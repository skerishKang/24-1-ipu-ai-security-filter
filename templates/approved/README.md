# Approved Templates

이 디렉터리는 사람이 검토하고 승인한 템플릿만 저장한다.

## 원칙

- draft 템플릿은 `demo-samples/derived/` 아래에 둔다.
- approved 템플릿은 `templates/approved/<template_id>/v<version>.template.json` 경로를 사용한다.
- approved 파일은 덮어쓰지 않고 새 버전 파일을 추가한다.
- `approval` 메타데이터가 없는 파일은 approved로 간주하지 않는다.

## 최소 승격 절차

1. draft 템플릿을 검토해 필드명, placeholder, validation, sensitivity 메타를 보정한다.
2. 아래 dry-run 명령으로 승인 불가 사유를 확인한다.

```bash
python3 scripts/promote_template.py \
  --draft demo-samples/derived/sample-long-contract-review.template.json \
  --version 1.1.0 \
  --reviewer reviewer@ipu.co.kr \
  --dry-run
```

3. 에러를 해결한 뒤 실제 승격을 실행한다.

```bash
python3 scripts/promote_template.py \
  --draft demo-samples/derived/sample-long-contract-review.template.json \
  --version 1.1.0 \
  --reviewer reviewer@ipu.co.kr
```

## 승인 메타데이터 예시

```json
{
  "approval": {
    "reviewer": "reviewer@ipu.co.kr",
    "approved_by": "reviewer@ipu.co.kr",
    "approved_at": "2026-03-14T22:10:00+09:00",
    "checklist_version": "template-approval-minimum-v1"
  }
}
```

## 참고 문서

- [08-template-approval-workflow.md](/mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-security-filter/docs/development/08-template-approval-workflow.md)
- [06-template-lifecycle-note.md](/mnt/g/Ddrive/BatangD/task/workdiary/24-1-ipu-ai-security-filter/docs/development/06-template-lifecycle-note.md)
