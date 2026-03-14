export const templateCatalog = [
  {
    key: "contract-review-request",
    path: "../templates/approved/contract_review_request/v1.1.0.template.json",
    label: "계약 검토 의뢰서 v1.1.0",
    documentType: "contract_review_request",
    description: "외부 자문 또는 내부 결재용 계약 검토 요청 템플릿의 최신 승인 버전",
  },
  {
    key: "customer-inquiry-intake",
    path: "../templates/approved/customer_inquiry_intake/v1.1.0.template.json",
    label: "고객 문의 접수서 v1.1.0",
    documentType: "customer_inquiry",
    description: "고객 문의 접수와 후속 조치 정리를 위한 최신 승인 템플릿",
  },
  {
    key: "internal-report-weekly",
    path: "../templates/approved/internal_report_weekly/v1.1.0.template.json",
    label: "주간 내부 보고서 v1.1.0",
    documentType: "internal_report",
    description: "주간 내부 운영 및 사업 보고 작성을 위한 최신 승인 템플릿",
  },
];

export const defaultTemplateCatalogKey = templateCatalog[0].key;
