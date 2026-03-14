import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createResultPanel({ originalText, replacedText, replacements }) {
  const panel = createPanelFrame({
    title: "2. 치환 결과",
    description:
      "원문과 치환본을 나란히 보여주고, 어떤 값이 어떤 토큰으로 바뀌었는지 확인합니다.",
    badge: `${replacements.length} replacements`,
  });

  const grid = document.createElement("div");
  grid.className = "result-grid";
  grid.innerHTML = `
    <article class="text-card">
      <p class="text-card__label">원문</p>
      <p class="text-card__content" data-testid="original-text">${escapeHtml(originalText)}</p>
    </article>
    <article class="text-card">
      <p class="text-card__label">치환본</p>
      <p class="text-card__content" data-testid="replaced-text">${escapeHtml(replacedText)}</p>
    </article>
  `;

  const list = document.createElement("div");
  list.className = "replacement-list";
  list.innerHTML = replacements
    .map(
      (item) => `
        <article class="list-item">
          <div class="list-item__row">
            <span class="list-item__key">${item.original}</span>
            <span class="list-item__value">${item.replaced}</span>
          </div>
          <div class="list-item__meta">${item.type} · ${item.reason}</div>
        </article>
      `,
    )
    .join("");

  panel.body.append(grid, list);
  return panel.element;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
