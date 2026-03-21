import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createReportPanel({ detections, report, policySummary, selectedPolicy }) {
  const panel = createPanelFrame({
    title: "3. 정책 판정",
    description: "탐지 건수, 적용 정책, 검토 상태를 확인합니다.",
    badge: formatRiskLevel(report.risk_level),
    badgeVariant: "warning",
  });

  panel.element.classList.add("panel--review-surface");
  if (report.review_status === "review-required") {
    panel.element.classList.add("panel--review-required");
  }

  const displayStrategy = selectedPolicy || report.strategy || "alias";
  const displayDetections = detections.map((item) => ({
    ...item,
    note: buildDetectionNote(item, selectedPolicy),
  }));

  const summary = document.createElement("div");
  summary.className = "report-summary";
  const nextStepText = report.review_status === "clean"
    ? "검토 상태가 정리됨입니다. 필요하면 오른쪽 패널에서 외부 전달용 텍스트를 복사하세요."
    : "검토 필요 항목이 있습니다. 치환 결과와 전송 가능 여부를 먼저 확인하세요.";
  summary.innerHTML = `
    <div class="metric">
      <span class="metric__label">탐지 건수</span>
      <strong class="metric__value">${report.total_detections}</strong>
    </div>
    <div class="metric">
      <span class="metric__label">치환 전략</span>
      <strong class="metric__value">${escapeHtml(displayStrategy)}</strong>
    </div>
    <div class="metric">
      <span class="metric__label">검토 상태</span>
      <strong class="metric__value">${formatReviewStatus(report.review_status)}</strong>
    </div>
    <p class="report-summary__hint" style="color: ${report.review_status === "clean" ? "#0f766e" : "#92400e"};">
      ${nextStepText}
    </p>
  `;

  const reviewBox = document.createElement("div");
  reviewBox.className = `report-review-box ${report.review_status === "review-required" ? "report-review-box--warning" : "report-review-box--clean"}`;
  reviewBox.innerHTML = `
    <strong class="report-review-box__title">${report.review_status === "review-required" ? "검토 필요" : "전송 준비 가능"}</strong>
    <p class="report-review-box__body">위험도는 <strong>${formatRiskLevel(report.risk_level)}</strong>이며 현재 전략은 <strong>${escapeHtml(displayStrategy)}</strong> 입니다.</p>
  `;

  const policyBox = document.createElement("div");
  policyBox.className = "report-policy-box";
  policyBox.innerHTML = `
    <strong class="report-policy-box__title">${escapeHtml(policySummary?.title || displayStrategy)}</strong>
    <p class="report-policy-box__body">${escapeHtml(policySummary?.description || "")}</p>
    <p class="report-policy-box__meta">${escapeHtml(policySummary?.examples || "")}</p>
  `;

  const list = document.createElement("div");
  list.className = "detection-list";
  list.innerHTML = displayDetections
    .map(
      (item) => `
        <article class="list-item ${isReviewCritical(item, report) ? "list-item--critical" : ""}">
          <div class="list-item__row">
            <span class="list-item__key">${escapeHtml(item.label)}</span>
            <span class="list-item__value">${escapeHtml(item.type)}</span>
          </div>
          <div class="list-item__meta">위치 ${item.start}-${item.end} · score ${item.score} · ${escapeHtml(item.note)}</div>
        </article>
      `,
    )
    .join("");

  panel.body.append(summary, reviewBox, policyBox, list);
  return panel.element;
}

function buildDetectionNote(item, selectedPolicy) {
  const base = String(item.note || "");
  if (selectedPolicy === "local_rewrite") {
    return `${base.split(" · ")[0]} · detection=local_rewrite review`;
  }
  return base;
}

function isReviewCritical(item, report) {
  if (report.review_status === "review-required" && report.risk_level === "high-risk") {
    return true;
  }

  return item.type === "AMOUNT" || item.type === "ORG";
}

function formatReviewStatus(value) {
  if (value === "review-required") return "검토 필요";
  if (value === "clean") return "정리됨";
  return value;
}

function formatRiskLevel(value) {
  if (value === "high-risk") return "높음";
  if (value === "moderate-risk") return "중간";
  if (value === "low-risk") return "낮음";
  return value;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
