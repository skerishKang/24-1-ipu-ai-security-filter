import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createCopyPromptPanel({
  copyReadyPrompt,
  readiness,
  onRestore,
  restoredText = "",
  restoreStatus = "복원 테스트를 아직 실행하지 않았습니다.",
  isRestoring = false,
  aiResponseText = "",
  onAiResponseChange = () => {},
  onRestoreAiResponse = () => {},
  aiRestoreStatus = "외부 AI 응답을 붙여넣은 뒤 복원할 수 있습니다.",
  aiRestoredText = "",
  isAiRestoring = false,
}) {
  const panel = createPanelFrame({
    title: "4. 외부 전달 보조",
    description: "필요한 경우 외부 AI에 전달할 안전 텍스트를 복사하고, 응답 복원도 확인합니다.",
    badge: "optional",
  });

  const prompt = document.createElement("pre");
  prompt.className = "copy-panel__prompt";
  prompt.textContent = copyReadyPrompt;

  const readinessSection = document.createElement("div");
  readinessSection.className = "copy-panel__readiness";
  if (readiness) {
    const isReady = readiness.ready_to_send;
    const statusColor = isReady ? "#0f766e" : "#92400e";
    const statusText = isReady ? "전달 가능" : "검토 필요";
    const nextActionText = isReady
      ? "필요하면 아래 텍스트를 복사해 외부 도구에 전달하세요."
      : "탐지 결과를 먼저 확인한 뒤 외부 전달 여부를 결정하세요.";
    readinessSection.innerHTML = `
      <div class="copy-panel__readiness-badge" style="background: ${statusColor}; color: white; padding: 8px 12px; border-radius: 4px; font-weight: bold; margin-bottom: 8px;">
        ${statusText}
      </div>
      <p class="copy-panel__readiness-reason" style="font-size: 14px; color: #666; margin: 0 0 8px 0;">
        ${escapeHtml(readiness.reason)}
      </p>
      <p class="copy-panel__next-action" style="font-size: 13px; color: ${statusColor}; margin: 0; font-weight: 600;">
        ${nextActionText}
      </p>
    `;
  }

  const isReadyToCopy = !readiness || readiness.ready_to_send !== false;
  const copyButtonLabel = isReadyToCopy ? "전달 텍스트 복사" : "검토 후 진행";
  const statusText = isReadyToCopy
    ? "필요할 때만 복사해서 외부 도구에 전달하세요."
    : "현재 상태에서는 바로 전달하지 않는 것이 좋습니다.";

  const actions = document.createElement("div");
  actions.className = "copy-panel__actions";
  actions.innerHTML = `
    <span class="copy-panel__status">${statusText}</span>
    <button type="button" class="button button--ghost" data-testid="copy-prompt" ${!isReadyToCopy ? "disabled" : ""}>${copyButtonLabel}</button>
  `;

  const status = actions.querySelector(".copy-panel__status");
  const copyButton = actions.querySelector("[data-testid='copy-prompt']");

  if (isReadyToCopy) {
    copyButton.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(copyReadyPrompt);
        status.textContent = "복사 완료";
      } catch (error) {
        status.textContent = "복사 실패. 직접 선택 후 복사하세요.";
      }
    });
  }

  const restoreSection = document.createElement("div");
  restoreSection.className = "copy-panel__restore";
  restoreSection.innerHTML = `
    <div class="copy-panel__restore-header">
      <strong>복원 테스트</strong>
      <button type="button" class="button button--ghost" data-testid="restore-preview">${isRestoring ? "복원 중..." : "현재 결과 복원"}</button>
    </div>
    <p class="copy-panel__restore-status" data-testid="restore-status" style="font-size: 13px; color: #666; margin: 8px 0;">
      ${escapeHtml(restoreStatus)}
    </p>
    <div class="text-card">
      <p class="text-card__label">복원 결과</p>
      <p class="text-card__content" data-testid="restored-text">${escapeHtml(restoredText || "복원 결과 없음")}</p>
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
      <strong>외부 응답 복원</strong>
      <p class="copy-panel__ai-response-desc" style="font-size: 13px; color: #666; margin: 4px 0;">
        외부 도구가 반환한 응답에 토큰이 남아 있으면 복원할 수 있습니다.
      </p>
    </div>
    <textarea
      class="copy-panel__ai-response-input"
      placeholder="외부 응답을 붙여넣으세요"
      data-testid="ai-response-input"
    >${escapeHtml(aiResponseText)}</textarea>
    <div class="copy-panel__ai-response-actions">
      <button type="button" class="button button--primary" data-testid="restore-ai-response">
        ${isAiRestoring ? "복원 중..." : "응답 복원"}
      </button>
    </div>
    <p class="copy-panel__ai-response-status" data-testid="ai-restore-status" style="font-size: 13px; color: #666; margin: 8px 0 0 0;">
      ${escapeHtml(aiRestoreStatus)}
    </p>
    <div class="text-card">
      <p class="text-card__label">복원된 응답</p>
      <p class="text-card__content" data-testid="ai-restored-text">${escapeHtml(aiRestoredText || "복원된 응답 없음")}</p>
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
