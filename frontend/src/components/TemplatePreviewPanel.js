import { createPanelFrame } from "../ui/createPanelFrame.js";
import { escapeHtml } from "../utils/resultRendering.js";

export function createTemplatePreviewPanel({
  template,
  values,
  generatedText,
  missingFields,
}) {
  const panel = createPanelFrame({
    title: "2. 문서 초안 미리보기",
    description: "입력값을 template_text 에 주입해 바로 문서 초안을 재구성합니다.",
    badge: missingFields.length === 0 ? "Ready" : `${missingFields.length} missing`,
    badgeVariant: missingFields.length === 0 ? undefined : "warning",
  });

  const status = document.createElement("div");
  status.className = `template-preview__status${missingFields.length === 0 ? "" : " template-preview__status--warning"}`;
  status.innerHTML =
    missingFields.length === 0
      ? "<strong>초안이 모두 채워졌습니다.</strong><span>이 상태로 복사해서 문서 초안 데모에 사용할 수 있습니다.</span>"
      : `<strong>아직 비어 있는 필드가 있습니다.</strong><span>${escapeHtml(missingFields.map((field) => field.label).join(", "))} 입력이 필요합니다.</span>`;

  const documentCard = document.createElement("article");
  documentCard.className = "template-preview__document";
  documentCard.innerHTML = `
    <div class="template-preview__document-header">
      <span>Generated Draft</span>
      <strong>${escapeHtml(template.title)}</strong>
    </div>
    <pre class="template-preview__document-body">${escapeHtml(generatedText)}</pre>
  `;

  const valuesList = document.createElement("div");
  valuesList.className = "template-preview__values";
  valuesList.innerHTML = template.fields
    .map((field) => {
      const value = values[field.name] ?? "";
      return `
        <article class="template-preview__value-item">
          <div class="template-preview__value-top">
            <span>${escapeHtml(field.label)}</span>
            <span>${field.required ? "required" : "optional"}</span>
          </div>
          <div class="template-preview__value-body">${escapeHtml(value || "입력 대기 중")}</div>
        </article>
      `;
    })
    .join("");

  panel.body.append(status, documentCard, valuesList);
  return panel.element;
}
