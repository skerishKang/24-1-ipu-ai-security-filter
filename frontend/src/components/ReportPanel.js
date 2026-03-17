import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createReportPanel({ detections, report, policySummary }) {
  const panel = createPanelFrame({
    title: "📋 3단계: 탐지 리포트",
    description:
      "탐지 결과를 확인하고 외부 전송 가능 여부를 판단하세요.",
    badge: report.risk_level,
    badgeVariant: "warning",
  });

  const summary = document.createElement("div");
  summary.className = "report-summary";
  const nextStepText = report.review_status === "clean"
    ? "✅ 탐지 사항 없음 - 오른쪽 '4단계'로 이동하여 프롬프트를 복사하세요."
    : "⚠️ 탐지됨 - 오른쪽 '4단계'에서 보안 검토 후 진행하세요.";
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
    <p style="font-size: 13px; font-weight: 600; color: ${report.review_status === 'clean' ? '#22c55e' : '#ef4444'}; margin-top: 12px;">
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
