import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createTemplateFormPanel({
  template,
  values,
  onFieldChange,
  onFillSample,
  onReset,
}) {
  const requiredCount = template.fields.filter((field) => field.required).length;
  const panel = createPanelFrame({
    title: "1. 템플릿 입력 폼",
    description: "저장된 템플릿 JSON의 field 정의를 읽어 입력 UI를 자동으로 구성합니다.",
    badge: `${template.fields.length} fields`,
  });

  const intro = document.createElement("div");
  intro.className = "template-form__intro";
  intro.innerHTML = `
    <div>
      <p class="template-form__eyebrow">Template JSON Demo</p>
      <strong>${escapeHtml(template.title)}</strong>
      <p>${escapeHtml(template.description)}</p>
    </div>
    <div class="template-form__summary">
      <span>필수 ${requiredCount}개</span>
      <span>실시간 초안 반영</span>
    </div>
  `;

  const form = document.createElement("div");
  form.className = "template-form";

  template.fields.forEach((field) => {
    const row = document.createElement("label");
    row.className = "template-form__field";

    const header = document.createElement("div");
    header.className = "template-form__field-header";
    header.innerHTML = `
      <span>${escapeHtml(field.label)}</span>
      <span class="template-form__field-type">${escapeHtml(field.type)}</span>
    `;

    const hint = document.createElement("p");
    hint.className = "template-form__hint";
    hint.textContent = field.helpText ?? "";

    const input = createInputByType(field, values[field.name] ?? "");
    input.addEventListener("input", () => {
      onFieldChange(field.name, normalizeFieldValue(field.type, input.value));
    });

    row.append(header, input);
    if (field.helpText) {
      row.append(hint);
    }
    form.append(row);
  });

  const actions = document.createElement("div");
  actions.className = "template-form__actions";
  actions.innerHTML = `
    <button type="button" class="button" data-action="fill-sample">샘플 값 채우기</button>
    <button type="button" class="button button--ghost" data-action="reset">입력 초기화</button>
  `;

  actions.querySelector("[data-action='fill-sample']").addEventListener("click", () => {
    onFillSample();
  });
  actions.querySelector("[data-action='reset']").addEventListener("click", () => {
    onReset();
  });

  panel.body.append(intro, form, actions);
  return panel.element;
}

function createInputByType(field, value) {
  if (field.type === "textarea") {
    const input = document.createElement("textarea");
    input.className = "template-form__textarea";
    input.placeholder = field.placeholder ?? "";
    input.value = value;
    return input;
  }

  const input = document.createElement("input");
  input.className = "template-form__input";
  input.placeholder = field.placeholder ?? "";
  input.value = value;

  switch (field.type) {
    case "date":
      input.type = "date";
      break;
    case "email":
      input.type = "email";
      input.inputMode = "email";
      break;
    case "phone":
      input.type = "tel";
      input.inputMode = "tel";
      break;
    case "amount":
      input.type = "text";
      input.inputMode = "numeric";
      break;
    default:
      input.type = "text";
      break;
  }

  return input;
}

function normalizeFieldValue(type, value) {
  if (type === "amount") {
    const digits = value.replaceAll(/[^0-9]/g, "");
    if (!digits) {
      return "";
    }
    return `${Number(digits).toLocaleString("ko-KR")}원`;
  }

  if (type === "phone") {
    const digits = value.replaceAll(/[^0-9]/g, "").slice(0, 11);

    if (digits.length <= 3) {
      return digits;
    }
    if (digits.length <= 7) {
      return `${digits.slice(0, 3)}-${digits.slice(3)}`;
    }
    return `${digits.slice(0, 3)}-${digits.slice(3, digits.length === 10 ? 6 : 7)}-${digits.slice(digits.length === 10 ? 6 : 7)}`;
  }

  return value;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
