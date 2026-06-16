import { escapeHtml } from "../utils/resultRendering.js";

export function createAppShell({ hero, modeToggle, layoutMode = "expert", showSession = true }) {
  const shell = document.createElement("main");
  shell.className = "app-shell";
  // ``hero`` fields can carry backend-controlled text (e.g. ``hero.sessionId``
  // is a server-issued identifier; a hostile backend could otherwise inject
  // HTML/script). Escape all of them.
  shell.innerHTML = `
    <section class="hero hero--compact">
      <div class="hero__topline">
        <div class="hero__identity">
          <span class="hero__eyebrow">${escapeHtml(hero.eyebrow)}</span>
          <h1>${escapeHtml(hero.title)}</h1>
        </div>
        <div data-slot="mode-toggle"></div>
      </div>
      <div class="hero__body hero__body--compact">
        <p>${escapeHtml(hero.description)}</p>
        ${
          showSession
            ? `
        <aside class="hero__session">
          <span class="hero__session-label">세션</span>
          <strong class="hero__session-value" data-testid="session-source">${escapeHtml(hero.sessionId)}</strong>
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
