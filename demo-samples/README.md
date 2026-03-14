# Demo Samples

업로드 테스트와 데모용으로 바로 사용할 수 있는 `.txt` 샘플 모음이다.

권장 사용:

- frontend에서 `.txt 파일 업로드` 모드 선택
- `strict_token` policy 선택
- 아래 샘플 파일을 하나씩 올려 결과 확인

---

## 기본 샘플 (짧은 문서)

| 파일명 | 설명 |
|--------|------|
| `sample-contract-review.txt` | 계약 검토 문맥 (짧은 버전) |
| `sample-customer-inquiry.txt` | 고객 문의 문맥 (짧은 버전) |
| `sample-internal-report.txt` | 내부 보고 문맥 (짧은 버전) |
| `sample-empty.txt` | 빈 파일 에러 상태 확인용 |

---

## 긴 데모용 샘플 (고객 데모 추천)

| 파일명 | 데모 포인트 | 주요 포함 정보 |
|--------|-------------|----------------|
| `sample-long-contract-review.txt` | 다중 민감정보 + 계약 문맥 | 회사명 3개, 금액 5종, 이메일/전화, 지적재산권/책임한계/해지 조항 |
| `sample-long-customer-inquiry.txt` | 장문의 고객 대응 + 내부 논의 | VIP 고객, 분쟁 가능성, 금액 협상, 후속 조치 |
| `sample-long-internal-report.txt` | 주간 업무 보고 + 경영진 보고 | 인력 현황, 예산, 기술 이슈, 재무 현황, 경쟁사 동향 |
| `sample-long-vendor-coordination.txt` | 협력사 관리 + 다단계 협상 | 다중 계약, 비용 협상, 기술/법무 의견, 일정 관리 |
| `sample-long-security-incident-note.txt` | 보안 사고 대응 + 법적 대응 | Incident 대응 프로세스, 비용 추정, 외부 컨택, stakeholders 통보 |

---

### 긴 샘플 사용 시 확인 포인트

1. **다중 치환 확인**: 각 파일마다 10개 이상의 민감정보가 포함되어 있어 여러 token 치환 확인 가능
2. **문맥 다양성**: 계약/법무/재무/기술/보안 등 다양한 업무 영역 포함
3. **길이 확인**: 1,000자 이상 구성되어 긴 텍스트 처리 확인 가능
