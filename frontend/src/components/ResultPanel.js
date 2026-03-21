import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createResultPanel({ originalText, replacedText, replacements }) {
  const panel = createPanelFrame({
    title: "2. 비식별 결과",
    description: "원문과 처리 결과를 나란히 확인하고, 어떤 값이 어떤 방식으로 치환됐는지 검토합니다.",
    badge: `${replacements.length} items`,
  });

  const grid = document.createElement("div");
  grid.className = "result-grid";
  grid.innerHTML = `
    <article class="text-card">
      <p class="text-card__label">원문</p>
      <p class="text-card__content" data-testid="original-text">${escapeHtml(originalText)}</p>
    </article>
    <article class="text-card">
      <p class="text-card__label">처리 결과</p>
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
