export function createViewModeToggle({ value, onChange }) {
  const container = document.createElement("div");
  container.className = "view-mode-toggle";
  container.innerHTML = `
    <button type="button" class="view-mode-toggle__button" data-mode="general">일반인 모드</button>
    <button type="button" class="view-mode-toggle__button" data-mode="expert">전문가 모드</button>
  `;

  for (const button of container.querySelectorAll("button")) {
    const isActive = button.dataset.mode === value;
    button.classList.toggle("view-mode-toggle__button--active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
    button.addEventListener("click", () => {
      onChange(button.dataset.mode);
    });
  }

  return container;
}
