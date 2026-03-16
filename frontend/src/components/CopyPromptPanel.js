import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createCopyPromptPanel({
  copyReadyPrompt,
  readiness,
  onRestore,
  restoredText = "",
  restoreStatus = "아직 복원 테스트를 실행하지 않았습니다.",
  isRestoring = false,
  aiResponseText = "",
  onAiResponseChange = () => {},
  onRestoreAiResponse = () => {},
  aiRestoreStatus = "외부 AI 응답을 복원하려면 먼저 응답을 붙여넣고 버튼을 누르세요.",
  aiRestoredText = "",
  isAiRestoring = false,
}) {
  const panel = createPanelFrame({
    title: "4. 외부 AI용 복사 프롬프트",
    description:
      "수동 모드에서는 아래 치환 프롬프트를 검토 후 외부 SOTA 모델에 직접 붙여넣고, 현재 세션 매핑으로 복원 테스트도 확인할 수 있습니다.",
    badge: "Copy Ready",
  });

  const prompt = document.createElement("pre");
  prompt.className = "copy-panel__prompt";
  prompt.textContent = copyReadyPrompt;

  const readinessSection = document.createElement("div");
  readinessSection.className = "copy-panel__readiness";
  if (readiness) {
    const isReady = readiness.ready_to_send;
    const statusColor = isReady ? "#22c55e" : "#ef4444";
    const statusText = isReady ? "✅ 외부 전송 가능" : "⚠️ 재검토 필요";
    readinessSection.innerHTML = `
      <div class="copy-panel__readiness-badge" style="background: ${statusColor}; color: white; padding: 8px 12px; border-radius: 4px; font-weight: bold; margin-bottom: 8px;">
        ${statusText}
      </div>
      <p class="copy-panel__readiness-reason" style="font-size: 14px; color: #666; margin: 0;">
        ${escapeHtml(readiness.reason)}
      </p>
    `;
  }

  const actions = document.createElement("div");
  actions.className = "copy-panel__actions";
  actions.innerHTML = `
    <span class="copy-panel__status">복사 후 외부 AI에 직접 붙여넣는 수동 모드 전용 흐름입니다.</span>
    <button type="button" class="button button--ghost">프롬프트 복사</button>
  `;

  const status = actions.querySelector(".copy-panel__status");
  actions.querySelector("button").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(copyReadyPrompt);
      status.textContent = "클립보드에 치환 프롬프트를 복사했습니다.";
    } catch (error) {
      status.textContent = "브라우저 권한 문제로 복사에 실패했습니다.";
    }
  });

  const restoreSection = document.createElement("div");
  restoreSection.className = "copy-panel__restore";
  restoreSection.innerHTML = `
    <div class="copy-panel__restore-header">
      <strong>복원 테스트</strong>
      <button type="button" class="button button--ghost" data-testid="restore-preview">${isRestoring ? "복원 중..." : "현재 치환본 복원"}</button>
    </div>
    <p class="copy-panel__restore-status" data-testid="restore-status">${escapeHtml(restoreStatus)}</p>
    <div class="text-card">
      <p class="text-card__label">복원 결과</p>
      <p class="text-card__content" data-testid="restored-text">${escapeHtml(restoredText || "복원 전")}</p>
    </div>
  `;

  const restoreButton = restoreSection.querySelector("[data-testid='restore-preview']");
  restoreButton.disabled = isRestoring;
  restoreButton.addEventListener("click", () => {
    onRestore?.();
  });

  const aiResponseSection = document.createElement("div");
  aiResponseSection.className = "copy-panel__ai-response";
  aiResponseSection.innerHTML = `
    <div class="copy-panel__ai-response-header">
      <strong>5. 외부 AI 응답 복원</strong>
      <p class="copy-panel__ai-response-desc">
        외부 AI 모델이 반환한 응답(치환된 토큰 포함)을 붙여넣으면 원문으로 복원합니다.
      </p>
    </div>
    <textarea 
      class="copy-panel__ai-response-input" 
      placeholder="여기에 외부 AI 응답을 붙여넣으세요..."
      data-testid="ai-response-input"
    >${escapeHtml(aiResponseText)}</textarea>
    <div class="copy-panel__ai-response-actions">
      <button type="button" class="button button--primary" data-testid="restore-ai-response">
        ${isAiRestoring ? "복원 중..." : "AI 응답 복원"}
      </button>
    </div>
    <p class="copy-panel__ai-response-status" data-testid="ai-restore-status">${escapeHtml(aiRestoreStatus)}</p>
    <div class="text-card">
      <p class="text-card__label">복원된 응답</p>
      <p class="text-card__content" data-testid="ai-restored-text">${escapeHtml(aiRestoredText || "복원 전")}</p>
    </div>
  `;

  const aiInput = aiResponseSection.querySelector("[data-testid='ai-response-input']");
  aiInput.addEventListener("input", () => {
    onAiResponseChange(aiInput.value);
  });

  const aiRestoreButton = aiResponseSection.querySelector("[data-testid='restore-ai-response']");
  aiRestoreButton.disabled = isAiRestoring || !aiResponseText;
  aiRestoreButton.addEventListener("click", () => {
    onRestoreAiResponse?.();
  });

  panel.body.append(readinessSection, prompt, actions, restoreSection, aiResponseSection);
  return panel.element;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
