import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createResultPanel({
  originalText,
  replacedText,
  replacements,
  detections,
  report,
  selectedPolicy,
  comparison,
  onLoadComparison,
  onClearComparison,
  policyLookup,
}) {
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

  const compareSection = createCompareSection({
    comparison,
    selectedPolicy,
    onLoadComparison,
    onClearComparison,
    policyLookup,
  });

  panel.body.append(summary, grid, list, compareSection);
  return panel.element;
}

function createCompareSection({ comparison, selectedPolicy, onLoadComparison, onClearComparison, policyLookup }) {
  const section = document.createElement("section");
  section.className = "compare-panel";

  const header = document.createElement("div");
  header.className = "compare-panel__header";
  header.innerHTML = `
    <div>
      <strong class="compare-panel__title">strict_token / local_rewrite 비교</strong>
      <p class="compare-panel__description">보수적 토큰 치환과 자연어 리라이트 결과를 같은 원문 기준으로 비교합니다.</p>
    </div>
  `;

  const actions = document.createElement("div");
  actions.className = "compare-panel__actions";

  if (comparison?.strictToken || comparison?.localRewrite) {
    const clearButton = document.createElement("button");
    clearButton.type = "button";
    clearButton.className = "button button--ghost";
    clearButton.textContent = "비교 닫기";
    clearButton.addEventListener("click", onClearComparison);
    actions.append(clearButton);
  } else {
    const loadButton = document.createElement("button");
    loadButton.type = "button";
    loadButton.className = "button button--ghost";
    loadButton.textContent = comparison?.loading ? "비교 불러오는 중..." : "비교 보기";
    loadButton.disabled = Boolean(comparison?.loading) || !["strict_token", "local_rewrite"].includes(selectedPolicy);
    loadButton.addEventListener("click", onLoadComparison);
    actions.append(loadButton);
  }

  header.append(actions);
  section.append(header);

  if (!["strict_token", "local_rewrite"].includes(selectedPolicy)) {
    const hint = document.createElement("p");
    hint.className = "compare-panel__hint";
    hint.textContent = "비교 뷰는 strict_token 또는 local_rewrite를 선택했을 때만 사용할 수 있습니다.";
    section.append(hint);
    return section;
  }

  if (comparison?.loading) {
    const loading = document.createElement("p");
    loading.className = "compare-panel__hint";
    loading.textContent = "비교 결과를 불러오고 있습니다.";
    section.append(loading);
    return section;
  }

  if (comparison?.error) {
    const error = document.createElement("p");
    error.className = "compare-panel__hint compare-panel__hint--error";
    error.textContent = comparison.error;
    section.append(error);
    return section;
  }

  if (!comparison?.strictToken || !comparison?.localRewrite) {
    const hint = document.createElement("p");
    hint.className = "compare-panel__hint";
    hint.textContent = "현재 정책 결과를 검토한 뒤 필요할 때 비교 버튼으로 두 결과를 나란히 확인하세요.";
    section.append(hint);
    return section;
  }

  const grid = document.createElement("div");
  grid.className = "compare-grid";
  grid.append(
    createCompareCard("strict_token", comparison.strictToken, policyLookup),
    createCompareCard("local_rewrite", comparison.localRewrite, policyLookup),
  );
  section.append(grid);
  return section;
}

function createCompareCard(policy, preview, policyLookup) {
  const card = document.createElement("article");
  card.className = "compare-card";
  const summary = policyLookup?.(policy);
  card.innerHTML = `
    <div class="compare-card__topline">
      <span class="policy-badge policy-badge--${policy === "local_rewrite" ? "rewrite" : "strict"}">policy ${policy}</span>
      <span class="review-badge review-badge--${preview.report.review_status === "review-required" ? "warning" : "clean"}">${preview.report.review_status} · ${preview.report.risk_level}</span>
    </div>
    <strong class="compare-card__title">${escapeHtml(summary?.title || policy)}</strong>
    <p class="compare-card__description">${escapeHtml(summary?.description || "")}</p>
    <p class="compare-card__content">${highlightText(preview.replaced_text, preview.replacements.map((item) => item.replaced), "text-replaced")}</p>
  `;
  return card;
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
