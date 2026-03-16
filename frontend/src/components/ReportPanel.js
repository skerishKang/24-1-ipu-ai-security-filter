import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createReportPanel({ detections, report, policySummary }) {
  const panel = createPanelFrame({
    title: "3. 탐지 리포트",
    description:
      "탐지 개수, 위험도, 분류별 상세 정보를 보여주며 현재 세션에서 어떤 민감정보가 마스킹됐는지 검토합니다.",
    badge: report.risk_level,
    badgeVariant: "warning",
  });

  const summary = document.createElement("div");
  summary.className = "report-summary";
  summary.innerHTML = `
    <div class="metric">
      <span class="metric__label">탐지 개수</span>
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
          <div class="list-item__meta">
            위치 ${item.start}-${item.end} · 신뢰도 ${item.score} · ${item.note}
          </div>
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
