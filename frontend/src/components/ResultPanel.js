import { createPanelFrame } from "../ui/createPanelFrame.js";
import {
  buildDetectionChips,
  createModeBadge,
  createStatusBadge,
  escapeHtml,
  formatReviewStatus,
  formatRiskLevel,
  highlightText,
} from "../utils/resultRendering.js";

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
  const totalDetections = Number.isFinite(report.total_detections)
    ? report.total_detections
    : 0;
  const panel = createPanelFrame({
    title: "2. 비식별 결과",
    description: "원문과 처리 결과를 나란히 확인하고, 어떤 항목이 어떤 정책으로 치환됐는지 검토합니다.",
    badge: `${totalDetections}건 탐지`,
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

  const originalCard = document.createElement("article");
  originalCard.className = "text-card";
  const originalLabel = document.createElement("p");
  originalLabel.className = "text-card__label";
  originalLabel.textContent = "원문";
  const originalContent = document.createElement("p");
  originalContent.className = "text-card__content";
  originalContent.dataset.testid = "original-text";
  originalContent.append(highlightText(originalText, replacements.map((item) => item.original), "text-original-hit"));
  originalCard.append(originalLabel, originalContent);

  const replacedCard = document.createElement("article");
  replacedCard.className = "text-card";
  const replacedLabel = document.createElement("p");
  replacedLabel.className = "text-card__label";
  replacedLabel.textContent = "처리 결과";
  const replacedContent = document.createElement("p");
  replacedContent.className = "text-card__content";
  replacedContent.dataset.testid = "replaced-text";
  replacedContent.append(highlightText(replacedText, replacements.map((item) => item.replaced), "text-replaced"));
  replacedCard.append(replacedLabel, replacedContent);

  grid.append(originalCard, replacedCard);

  const list = document.createElement("div");
  list.className = "replacement-list";
  for (const item of replacements) {
    const listItem = document.createElement("article");
    listItem.className = "list-item";

    const row = document.createElement("div");
    row.className = "list-item__row";

    const key = document.createElement("span");
    key.className = "list-item__key";
    key.textContent = item.original ?? "";

    const value = document.createElement("span");
    value.className = "list-item__value";
    value.textContent = item.replaced ?? "";

    row.append(key, value);

    const meta = document.createElement("div");
    meta.className = "list-item__meta";
    meta.textContent = `${item.type ?? ""} · ${item.reason || ""}`;

    listItem.append(row, meta);
    list.append(listItem);
  }

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

  const titleBlock = document.createElement("div");
  const title = document.createElement("strong");
  title.className = "compare-panel__title";
  title.textContent = "strict_token / local_rewrite 비교";
  const description = document.createElement("p");
  description.className = "compare-panel__description";
  description.textContent = "보수적 토큰 치환과 자연어 리라이트 결과를 같은 원문 기준으로 비교합니다.";
  titleBlock.append(title, description);

  header.append(titleBlock);

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
    hint.textContent = "현재 정책 결과를 검토한 뒤 필요하면 비교 버튼으로 두 결과를 나란히 확인하세요.";
    section.append(hint);
    return section;
  }

  const insight = document.createElement("p");
  insight.className = "compare-panel__hint";
  insight.textContent = "strict_token은 더 보수적이고, local_rewrite는 더 읽기 쉬운 결과를 목표로 합니다.";
  section.append(insight);

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

  const topLine = document.createElement("div");
  topLine.className = "compare-card__topline";

  const badge = document.createElement("span");
  badge.className = `policy-badge policy-badge--${policy === "local_rewrite" ? "rewrite" : "strict"}`;
  badge.textContent = `정책 ${policy}`;

  const statusBadge = document.createElement("span");
  statusBadge.className = `review-badge review-badge--${preview.report.review_status === "review-required" ? "warning" : "clean"}`;
  statusBadge.textContent = `${formatReviewStatus(preview.report.review_status)} · ${formatRiskLevel(preview.report.risk_level)}`;

  topLine.append(badge, statusBadge);

  const title = document.createElement("strong");
  title.className = "compare-card__title";
  title.textContent = summary?.title || policy;

  const description = document.createElement("p");
  description.className = "compare-card__description";
  description.textContent = summary?.description || "";

  const content = document.createElement("p");
  content.className = "compare-card__content";
  content.append(highlightText(preview.replaced_text, preview.replacements.map((item) => item.replaced), "text-replaced"));

  card.append(topLine, title, description, content);
  return card;
}
