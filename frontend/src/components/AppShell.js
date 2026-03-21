export function createAppShell({ hero, modeToggle, layoutMode = "expert", showSession = true }) {
  const shell = document.createElement("main");
  shell.className = "app-shell";
  shell.innerHTML = `
    <section class="hero hero--compact">
      <div class="hero__topline">
        <div class="hero__identity">
          <span class="hero__eyebrow">${hero.eyebrow}</span>
          <h1>${hero.title}</h1>
        </div>
        <div data-slot="mode-toggle"></div>
      </div>
      <div class="hero__body hero__body--compact">
        <p>${hero.description}</p>
        ${
          showSession
            ? `
        <aside class="hero__session">
          <span class="hero__session-label">Session</span>
          <strong class="hero__session-value" data-testid="session-source">${hero.sessionId}</strong>
        </aside>
        `
            : ""
        }
      </div>
    </section>
    <section class="workspace workspace--${layoutMode}">
      <div class="column">
        <div data-slot="input"></div>
        <div data-slot="result"></div>
      </div>
      <div class="column">
        <div data-slot="report"></div>
        <div data-slot="copy"></div>
      </div>
    </section>
  `;

  if (modeToggle) {
    shell.querySelector("[data-slot='mode-toggle']").append(modeToggle);
  }
  return shell;
}
