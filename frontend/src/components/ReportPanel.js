import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createReportPanel({ detections, report, policySummary }) {
  const panel = createPanelFrame({
    title: "3. 정책 판정",
    description: "탐지 건수, 적용 정책, 검토 상태를 확인합니다.",
    badge: report.risk_level,
    badgeVariant: "warning",
  });

  const summary = document.createElement("div");
  summary.className = "report-summary";
  const nextStepText = report.review_status === "clean"
    ? "검토가 끝났습니다. 필요하면 오른쪽 패널에서 외부 전달용 텍스트를 복사하세요."
    : "탐지 항목이 있습니다. 치환 결과와 전달 가능 여부를 먼저 검토하세요.";
  summary.innerHTML = `
    <div class="metric">
      <span class="metric__label">탐지 건수</span>
      <strong class="metric__value">${report.total_detections}</strong>
    </div>
    <div class="metric">
      <span class="metric__label">치환 전략</span>
      <strong class="metric__value">${report.strategy}</strong>
    </div>
    <div class="metric">
      <span class="metric__label">검토 상태</span>
      <strong class="metric__value">${report.review_status}</strong>
    </div>
    <p style="font-size: 13px; font-weight: 600; color: ${report.review_status === 'clean' ? '#0f766e' : '#92400e'}; margin-top: 12px;">
      ${nextStepText}
    </p>
  `;

  const policyBox = document.createElement("div");
  policyBox.className = "report-policy-box";
  policyBox.innerHTML = `
    <strong class="report-policy-box__title">${escapeHtml(policySummary?.title || report.strategy)}</strong>
    <p class="report-policy-box__body">${escapeHtml(policySummary?.description || "")}</p>
    <p class="report-policy-box__meta">${escapeHtml(policySummary?.examples || "")}</p>
  `;

  const list = document.createElement("div");
  list.className = "detection-list";
  list.innerHTML = detections
    .map(
      (item) => `
        <article class="list-item">
          <div class="list-item__row">
            <span class="list-item__key">${item.label}</span>
            <span class="list-item__value">${item.type}</span>
          </div>
          <div class="list-item__meta">위치 ${item.start}-${item.end} · score ${item.score} · ${item.note}</div>
        </article>
      `,
    )
    .join("");

  panel.body.append(summary, policyBox, list);
  return panel.element;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
