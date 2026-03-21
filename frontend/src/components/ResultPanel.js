import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createResultPanel({ originalText, replacedText, replacements, detections, report, selectedPolicy }) {
  const panel = createPanelFrame({
    title: "2. 비식별 결과",
    description: "원문과 처리 결과를 나란히 확인하고, 어떤 항목이 어떤 정책으로 치환됐는지 검토합니다.",
    badge: `${report.total_detections} detections`,
  });

  panel.element.classList.add("panel--review-surface");
  if (report.review_status === "review-required") {
    panel.element.classList.add("panel--review-required");
  }

  const summary = document.createElement("div");
  summary.className = "result-summary";
  summary.append(
    createModeBadge(selectedPolicy, report.strategy),
    createStatusBadge(report),
    ...buildDetectionChips(detections),
  );

  const grid = document.createElement("div");
  grid.className = "result-grid";
  grid.innerHTML = `
    <article class="text-card">
      <p class="text-card__label">원문</p>
      <p class="text-card__content" data-testid="original-text">${highlightText(originalText, replacements.map((item) => item.original), "text-original-hit")}</p>
    </article>
    <article class="text-card">
      <p class="text-card__label">처리 결과</p>
      <p class="text-card__content" data-testid="replaced-text">${highlightText(replacedText, replacements.map((item) => item.replaced), "text-replaced")}</p>
    </article>
  `;

  const list = document.createElement("div");
  list.className = "replacement-list";
  list.innerHTML = replacements
    .map(
      (item) => `
        <article class="list-item">
          <div class="list-item__row">
            <span class="list-item__key">${escapeHtml(item.original)}</span>
            <span class="list-item__value">${escapeHtml(item.replaced)}</span>
          </div>
          <div class="list-item__meta">${escapeHtml(item.type)} · ${escapeHtml(item.reason || "")}</div>
        </article>
      `,
    )
    .join("");

  panel.body.append(summary, grid, list);
  return panel.element;
}

function buildDetectionChips(detections) {
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

function createModeBadge(selectedPolicy, strategy) {
  const badge = document.createElement("span");
  const mode = selectedPolicy || strategy || "default";
  const variant = mode === "local_rewrite" ? "rewrite" : mode === "strict_token" ? "strict" : "default";
  badge.className = `policy-badge policy-badge--${variant}`;
  badge.textContent = `policy ${mode}`;
  return badge;
}

function createStatusBadge(report) {
  const badge = document.createElement("span");
  const variant = report.review_status === "review-required" ? "warning" : "clean";
  badge.className = `review-badge review-badge--${variant}`;
  badge.textContent = `${report.review_status} · ${report.risk_level}`;
  return badge;
}

function highlightText(text, values, className) {
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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
