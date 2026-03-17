import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createSimpleResultPanel({
  originalText,
  replacedText,
  protectedCount,
  previewLabel = "최근 미리보기 결과",
  policySummary,
}) {
  const panel = createPanelFrame({
    title: "🔒 2단계: 치환 결과 확인",
    description: "민감정보가 가려진 결과를 확인하고 다음 단계로 진행하세요.",
    badge: `${protectedCount}개 보호`,
  });

  const summary = document.createElement("div");
  summary.className = "simple-result__summary";
  const nextStepText = protectedCount > 0 
    ? "👇 아래 '결과 복사' 버튼을 누른 뒤 오른쪽 패널에서 보안 프롬프트를 확인하세요."
    : "✅ 민감정보가 없습니다! 바로 외부 AI에 전달해도 됩니다.";
  summary.innerHTML = `
    <strong class="simple-result__count">🔒 ${protectedCount}개 민감 정보를 가렸어요</strong>
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
    <span class="simple-result__status">👇 이 버튼을 누르면 클립보드에 복사됩니다</span>
    <button type="button" class="button button--ghost">📋 결과 복사</button>
  `;

  const status = actions.querySelector(".simple-result__status");
  actions.querySelector("button").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(replacedText);
      status.textContent = "✅ 복사 완료! 👉 오른쪽 '4단계' 패널에서 보안 프롬프트를 확인하세요.";
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
