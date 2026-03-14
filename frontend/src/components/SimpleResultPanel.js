import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createSimpleResultPanel({
  originalText,
  replacedText,
  protectedCount,
  previewLabel = "최근 미리보기 결과",
}) {
  const panel = createPanelFrame({
    title: "결과 확인",
    description: "🔒 가려진 내용을 확인하고 복사하세요",
    badge: `${protectedCount}개 보호`,
  });

  const summary = document.createElement("div");
  summary.className = "simple-result__summary";
  summary.innerHTML = `
    <strong class="simple-result__count">🔒 ${protectedCount}개 민감 정보를 가렸어요</strong>
    <p class="simple-result__label">${escapeHtml(previewLabel)}</p>
    <p class="simple-result__hint">💡 이제 이걸 복사해서 AI에 붙여넣으세요!</p>
  `;

  const safeCard = document.createElement("div");
  safeCard.className = "text-card";
  safeCard.innerHTML = `
    <p class="text-card__label">🔒 가려진 결과</p>
    <p class="text-card__content" data-testid="simple-replaced-text">${escapeHtml(replacedText)}</p>
  `;

  const originalDetails = document.createElement("details");
  originalDetails.className = "simple-result__details";
  originalDetails.innerHTML = `
    <summary>👀 원문 보기</summary>
    <div class="text-card">
      <p class="text-card__content">${escapeHtml(originalText)}</p>
    </div>
  `;

  const actions = document.createElement("div");
  actions.className = "simple-result__actions";
  actions.innerHTML = `
    <span class="simple-result__status">이거 복사하면 끝!</span>
    <button type="button" class="button button--ghost">결과 복사</button>
  `;

  const status = actions.querySelector(".simple-result__status");
  actions.querySelector("button").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(replacedText);
      status.textContent = "✅ 복사 완료! 이제 AI에 붙여넣으세요";
    } catch (error) {
      status.textContent = "❌ 복사에 실패했어요. 직접 ctrl+C 하세요";
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
