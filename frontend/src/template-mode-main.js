import { createTemplateFormPanel } from "./components/TemplateFormPanel.js";
import { createTemplatePreviewPanel } from "./components/TemplatePreviewPanel.js";
import { defaultTemplateCatalogKey, templateCatalog } from "./data/templateCatalog.js";

const app = document.querySelector("#app");

const state = {
  template: null,
  values: {},
  selectedTemplateKey: defaultTemplateCatalogKey,
  status: "loading",
  errorMessage: "",
};

function render() {
  app.innerHTML = "";

  if (state.status === "loading") {
    app.append(createStatusShell({
      title: "템플릿을 불러오는 중입니다.",
      description: "승인된 템플릿 JSON을 읽어 폼을 구성하고 있습니다.",
    }));
    return;
  }

  if (state.status === "error") {
    app.append(createStatusShell({
      title: "템플릿 JSON을 불러오지 못했습니다.",
      description: state.errorMessage,
      variant: "error",
    }));
    return;
  }

  const generatedText = buildDraft(state.template, state.values);
  const missingFields = state.template.fields.filter(
    (field) => field.required && !String(state.values[field.name] ?? "").trim(),
  );

  const shell = document.createElement("main");
  const selectedTemplateSource = getSelectedTemplateSource();
  shell.className = "app-shell";
  shell.innerHTML = `
    <section class="hero">
      <div class="hero__topline">
        <span class="hero__eyebrow">IPU Template Mode</span>
        <div class="template-mode__links">
          <a class="button button--ghost template-mode__link" href="./index.html">기존 manual-preview로 돌아가기</a>
        </div>
      </div>
      <div class="hero__body">
        <div>
          <h1>템플릿 기반 입력 폼 실험</h1>
          <p>승인된 템플릿 JSON 목록에서 하나를 선택해 입력 폼을 만들고, 사용자가 값을 넣으면 문서 초안을 실시간으로 재구성하는 프론트엔드 데모입니다.</p>
        </div>
        <aside class="hero__session">
          <span class="hero__session-label">Current Template</span>
          <strong class="hero__session-value">${state.template.id}</strong>
          <span class="hero__session-label">Document Type</span>
          <strong class="hero__session-value">${escapeHtml(state.template.meta.documentType)}</strong>
        </aside>
      </div>
    </section>
  `;

  shell.append(createTemplateSelector(selectedTemplateSource));

  const workspace = document.createElement("section");
  workspace.className = "template-workspace";

  const formPanel = createTemplateFormPanel({
    template: state.template,
    values: state.values,
    onFieldChange: updateField,
    onFillSample: fillSampleValues,
    onReset: resetValues,
  });
  const previewPanel = createTemplatePreviewPanel({
    template: state.template,
    values: state.values,
    generatedText,
    missingFields,
  });

  workspace.append(formPanel, previewPanel);
  shell.append(workspace);
  app.append(shell);
}

function createStatusShell({ title, description, variant = "info" }) {
  const selectedTemplateSource = getSelectedTemplateSource();
  const shell = document.createElement("main");
  shell.className = "app-shell";
  shell.innerHTML = `
    <section class="hero">
      <div class="hero__topline">
        <span class="hero__eyebrow">IPU Template Mode</span>
        <div class="template-mode__links">
          <a class="button button--ghost template-mode__link" href="./index.html">기존 manual-preview로 돌아가기</a>
        </div>
      </div>
      <div class="hero__body">
        <div>
          <h1>${escapeHtml(title)}</h1>
          <p>${escapeHtml(description)}</p>
        </div>
        <aside class="hero__session">
          <span class="hero__session-label">Template Source</span>
          <strong class="hero__session-value">${escapeHtml(selectedTemplateSource.label)}</strong>
        </aside>
      </div>
    </section>
    <section class="panel-frame">
      <div class="panel-frame__body">
        <div class="template-preview__status${variant === "error" ? " template-preview__status--warning" : ""}">
          <strong>${escapeHtml(title)}</strong>
          <span>${escapeHtml(description)}</span>
        </div>
      </div>
    </section>
  `;
  return shell;
}

function createTemplateSelector(selectedTemplateSource) {
  const wrapper = document.createElement("section");
  wrapper.className = "template-selector";
  wrapper.innerHTML = `
    <div class="template-selector__summary">
      <p class="template-form__eyebrow">Approved Template Catalog</p>
      <strong>${escapeHtml(selectedTemplateSource.label)}</strong>
      <p>${escapeHtml(selectedTemplateSource.description)}</p>
    </div>
    <label class="template-selector__control">
      <span>템플릿 선택</span>
      <select class="template-selector__select" data-role="template-selector"></select>
      <small class="template-selector__meta">${escapeHtml(selectedTemplateSource.documentType)}</small>
    </label>
  `;

  const select = wrapper.querySelector("[data-role='template-selector']");
  select.innerHTML = templateCatalog
    .map((item) => (
      `<option value="${escapeHtml(item.key)}"${item.key === state.selectedTemplateKey ? " selected" : ""}>` +
      `${escapeHtml(item.label)} · ${escapeHtml(item.documentType)}</option>`
    ))
    .join("");

  select.addEventListener("change", async (event) => {
    const nextKey = event.target.value;
    if (nextKey === state.selectedTemplateKey) {
      return;
    }

    state.selectedTemplateKey = nextKey;
    state.values = {};
    await loadSelectedTemplate();
  });

  return wrapper;
}

function updateField(name, value) {
  state.values = {
    ...state.values,
    [name]: value,
  };
  render();
}

function fillSampleValues() {
  state.values = Object.fromEntries(
    Object.entries(state.template.sample_values).map(([key, value]) => [
      key,
      normalizeSampleValue(findFieldType(key), value),
    ]),
  );
  render();
}

function resetValues() {
  state.values = {};
  render();
}

async function initialize() {
  await loadSelectedTemplate();
}

async function loadSelectedTemplate() {
  state.status = "loading";
  render();

  try {
    const selectedTemplateSource = getSelectedTemplateSource();
    const response = await fetch(selectedTemplateSource.path, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const rawTemplate = await response.json();
    state.template = normalizeTemplate(rawTemplate, selectedTemplateSource);
    state.status = "ready";
    render();
  } catch (error) {
    state.status = "error";
    state.errorMessage =
      `현재 템플릿 모드는 프로젝트 루트에서 정적 서버를 띄워야 합니다. ` +
      `예: /24-1-ipu-ai-firewall 에서 python3 -m http.server 4241 실행 후 ` +
      `/frontend/template-mode.html 로 접속하세요. 상세 오류: ${error.message}`;
    render();
  }
}

function getSelectedTemplateSource() {
  return templateCatalog.find((item) => item.key === state.selectedTemplateKey) ?? templateCatalog[0];
}

function buildDraft(template, values) {
  return template.template_text.replaceAll(/{{\s*([a-zA-Z0-9_]+)\s*}}/g, (match, fieldName) => {
    const field = template.fields.find((item) => item.name === fieldName);
    const value = String(values[fieldName] ?? "").trim();

    if (value) {
      return value;
    }

    return `[${field?.label ?? fieldName} 입력 필요]`;
  });
}

function findFieldType(name) {
  return state.template.fields.find((field) => field.name === name)?.type ?? "text";
}

function normalizeTemplate(rawTemplate, source) {
  const normalizedFields = [...(rawTemplate.fields ?? [])]
    .sort((left, right) => {
      const leftOrder = left.ui?.order ?? 9999;
      const rightOrder = right.ui?.order ?? 9999;
      return leftOrder - rightOrder;
    })
    .map((field) => normalizeField(field));

  return {
    id: `${rawTemplate.template_id ?? rawTemplate.template_name}@${rawTemplate.version ?? "draft"}`,
    title: rawTemplate.template_name,
    description: rawTemplate.document_purpose,
    template_text: rawTemplate.template_text,
    fields: normalizedFields,
    sample_values: rawTemplate.sample_values ?? buildSampleValues(rawTemplate.fields ?? []),
    meta: {
      templateId: rawTemplate.template_id ?? rawTemplate.template_name,
      version: rawTemplate.version ?? "draft",
      status: rawTemplate.status ?? "draft",
      documentType: rawTemplate.document_type,
      sourcePath: source.path,
    },
  };
}

function normalizeField(field) {
  const fieldName = field.field_name ?? field.name;
  const widget = field.ui?.widget ?? field.type ?? "text";

  return {
    name: fieldName,
    label: field.label ?? fieldName,
    type: mapFieldType(widget, field.type),
    placeholder: field.placeholder ?? "",
    required: Boolean(field.required),
    helpText: field.description ?? "",
    originalType: field.type ?? "text",
  };
}

function mapFieldType(widget, type) {
  if (widget === "textarea") {
    return "textarea";
  }

  if (widget === "date" || type === "date") {
    return "date";
  }

  if (widget === "email" || type === "email") {
    return "email";
  }

  if (widget === "tel" || type === "phone") {
    return "phone";
  }

  if (type === "amount") {
    return "amount";
  }

  if (type === "address" || type === "list_text" || type === "free_text") {
    return "textarea";
  }

  return "text";
}

function buildSampleValues(fields) {
  return Object.fromEntries(
    fields
      .map((field) => {
        const fieldName = field.field_name ?? field.name;
        const sampleValue = field.example_value ?? field.default_value ?? field.source_examples?.[0] ?? "";
        return [fieldName, sampleValue];
      })
      .filter(([name]) => Boolean(name)),
  );
}

function normalizeSampleValue(type, value) {
  if (type === "amount") {
    const digits = String(value).replaceAll(/[^0-9]/g, "");
    return digits ? `${Number(digits).toLocaleString("ko-KR")}원` : "";
  }

  if (type === "phone") {
    const digits = String(value).replaceAll(/[^0-9]/g, "").slice(0, 11);
    if (digits.length <= 2) {
      return digits;
    }
    if (digits.startsWith("02")) {
      if (digits.length <= 5) {
        return `${digits.slice(0, 2)}-${digits.slice(2)}`;
      }
      if (digits.length <= 9) {
        return `${digits.slice(0, 2)}-${digits.slice(2, 5)}-${digits.slice(5)}`;
      }
      return `${digits.slice(0, 2)}-${digits.slice(2, 6)}-${digits.slice(6)}`;
    }
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
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

initialize();
