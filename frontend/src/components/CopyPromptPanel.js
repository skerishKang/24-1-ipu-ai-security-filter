import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createCopyPromptPanel({
  copyReadyPrompt,
  onRestore,
  restoredText = "",
  restoreStatus = "아직 복원 테스트를 실행하지 않았습니다.",
  isRestoring = false,
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

  panel.body.append(prompt, actions, restoreSection);
  return panel.element;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
