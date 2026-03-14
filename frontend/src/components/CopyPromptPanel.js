import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createCopyPromptPanel({ copyReadyPrompt }) {
  const panel = createPanelFrame({
    title: "4. 외부 AI용 복사 프롬프트",
    description:
      "수동 모드에서는 아래 치환 프롬프트를 검토 후 외부 SOTA 모델에 직접 붙여넣습니다.",
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

  panel.body.append(prompt, actions);
  return panel.element;
}
