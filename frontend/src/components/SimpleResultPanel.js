import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createSimpleResultPanel({
  originalText,
  replacedText,
  protectedCount,
  previewLabel = "최근 처리 결과",
  policySummary,
}) {
  const panel = createPanelFrame({
    title: "2. 처리 결과",
    description: "비식별 결과를 빠르게 확인합니다.",
    badge: `${protectedCount} protected`,
  });

  const summary = document.createElement("div");
  summary.className = "simple-result__summary";
  const nextStepText = protectedCount > 0
    ? "처리 결과를 확인한 뒤, 필요하면 검토 패널에서 세부 항목을 점검하세요."
    : "탐지 항목이 없습니다. 바로 다음 작업으로 진행할 수 있습니다.";
  summary.innerHTML = `
    <strong class="simple-result__count">${protectedCount}개 항목 보호</strong>
    <p class="simple-result__label">${escapeHtml(previewLabel)}</p>
    <p class="simple-result__policy">${escapeHtml(policySummary?.title || "")}</p>
    <p class="simple-result__policy-meta">${escapeHtml(policySummary?.description || "")}</p>
    <p class="simple-result__hint" style="font-size: 13px; font-weight: 600; color: #0f766e; margin-top: 12px;">
      ${nextStepText}
    </p>
  `;

  const safeCard = document.createElement("div");
  safeCard.className = "text-card";
  safeCard.innerHTML = `
    <p class="text-card__label">처리 결과</p>
    <p class="text-card__content" data-testid="simple-replaced-text">${escapeHtml(replacedText)}</p>
  `;

  const originalDetails = document.createElement("details");
  originalDetails.className = "simple-result__details";
  originalDetails.innerHTML = `
    <summary>원문 보기</summary>
    <div class="text-card">
      <p class="text-card__content">${escapeHtml(originalText)}</p>
    </div>
  `;

  const actions = document.createElement("div");
  actions.className = "simple-result__actions";
  actions.innerHTML = `
    <span class="simple-result__status">처리 결과를 클립보드에 복사할 수 있습니다.</span>
    <button type="button" class="button button--ghost">결과 복사</button>
  `;

  const status = actions.querySelector(".simple-result__status");
  actions.querySelector("button").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(replacedText);
      status.textContent = "복사 완료";
    } catch (error) {
      status.textContent = "복사 실패. 직접 선택 후 복사하세요.";
    }
  });

  panel.body.append(summary, safeCard, actions, originalDetails);
  return panel.element;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
