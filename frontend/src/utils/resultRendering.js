export function buildDetectionChips(detections) {
  const counts = detections.reduce((acc, item) => {
    acc[item.type] = (acc[item.type] ?? 0) + 1;
    return acc;
  }, {});

  return Object.entries(counts).map(([type, count]) => {
    const chip = document.createElement("span");
    chip.className = "summary-chip";
    chip.textContent = `${type} ${count}`;
    return chip;
  });
}

export function createModeBadge(selectedPolicy, strategy) {
  const badge = document.createElement("span");
  const mode = selectedPolicy || strategy || "default";
  const variant = mode === "local_rewrite" ? "rewrite" : mode === "strict_token" ? "strict" : "default";
  badge.className = `policy-badge policy-badge--${variant}`;
  badge.textContent = `정책 ${mode}`;
  return badge;
}

export function createStatusBadge(report) {
  const badge = document.createElement("span");
  const variant = report.review_status === "review-required" ? "warning" : "clean";
  badge.className = `review-badge review-badge--${variant}`;
  badge.textContent = `${formatReviewStatus(report.review_status)} · ${formatRiskLevel(report.risk_level)}`;
  return badge;
}

export function formatReviewStatus(value) {
  if (value === "review-required") return "검토 필요";
  if (value === "clean") return "전송 가능";
  return value;
}

export function formatRiskLevel(value) {
  if (value === "high-risk") return "높음";
  if (value === "moderate-risk") return "중간";
  if (value === "low-risk") return "낮음";
  return value;
}

export function highlightText(text, values, className) {
  let html = escapeHtml(text);
  const uniqueValues = [...new Set(values.filter(Boolean))].sort((left, right) => right.length - left.length);

  uniqueValues.forEach((value, index) => {
    const escapedValue = escapeHtml(value);
    const startToken = `__HL_START_${index}__`;
    const endToken = `__HL_END_${index}__`;
    html = html.split(escapedValue).join(`${startToken}${escapedValue}${endToken}`);
  });

  uniqueValues.forEach((_, index) => {
    html = html
      .replaceAll(`__HL_START_${index}__`, `<mark class="${className}">`)
      .replaceAll(`__HL_END_${index}__`, "</mark>");
  });

  return html;
}

export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
