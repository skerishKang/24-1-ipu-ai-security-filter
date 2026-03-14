export function createPanelFrame({ title, description, badge, badgeVariant }) {
  const element = document.createElement("section");
  element.className = "panel";
  element.innerHTML = `
    <div class="panel__header">
      <div>
        <h2 class="panel__title">${title}</h2>
        <p class="panel__description">${description}</p>
      </div>
      <span class="badge ${badgeVariant === "warning" ? "badge--warning" : ""}">${badge}</span>
    </div>
    <div class="panel__body"></div>
  `;

  return {
    element,
    body: element.querySelector(".panel__body"),
  };
}
