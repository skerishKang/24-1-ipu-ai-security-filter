import { escapeHtml } from "../utils/resultRendering.js";

export function createPanelFrame({ title, description, badge, badgeVariant }) {
  const element = document.createElement("section");
  element.className = "panel";
  // ``title``, ``description`` and ``badge`` can come from backend payloads
  // (e.g. ``formatReviewStatus(report.risk_level)`` or ``total_detections``).
  // Escape them so a malicious backend cannot inject script via these slots.
  element.innerHTML = `
    <div class="panel__header">
      <div>
        <h2 class="panel__title">${escapeHtml(title)}</h2>
        <p class="panel__description">${escapeHtml(description)}</p>
      </div>
      <span class="badge ${badgeVariant === "warning" ? "badge--warning" : ""}">${escapeHtml(badge)}</span>
    </div>
    <div class="panel__body"></div>
  `;

  return {
    element,
    body: element.querySelector(".panel__body"),
  };
}
