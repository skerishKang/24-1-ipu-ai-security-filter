import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createInputPanel({
  title = "1. 원문 입력",
  description = "사내 메모, 계약서 초안, 고객 대응 문구 등 민감정보가 포함될 수 있는 원문을 붙여넣거나 .txt 파일로 업로드합니다.",
  value,
  inputMode,
  onModeChange,
  onSubmit,
  onFileSubmit,
  policy,
  onPolicyChange,
  selectedFileName,
  selectedFileContent,
  isDragActive,
  onFileChange,
  onFileDrop,
  isLoading,
  statusMessage,
  statusTone,
  showPolicy = true,
  metaText = "텍스트 입력은 fallback을 유지하고, 파일 업로드는 backend live 응답만 사용합니다.",
}) {
  const panel = createPanelFrame({
    title,
    description,
    badge: "Manual Preview",
  });

  const modeSwitch = document.createElement("div");
  modeSwitch.className = "input-panel__mode-switch";
  modeSwitch.innerHTML = `
    <label class="input-panel__mode-option${inputMode === "text" ? " input-panel__mode-option--active" : ""}">
      <input type="radio" name="input-mode" value="text" data-testid="input-mode-text" />
      <span>텍스트 입력</span>
    </label>
    <label class="input-panel__mode-option${inputMode === "file" ? " input-panel__mode-option--active" : ""}">
      <input type="radio" name="input-mode" value="file" data-testid="input-mode-file" />
      <span>.txt 파일 업로드</span>
    </label>
  `;

  const modeHint = document.createElement("p");
  modeHint.className = "input-panel__mode-hint";
  modeHint.textContent =
    inputMode === "file"
      ? "📁 파일을 올리면 민감 정보가 가려져요"
      : "✏️ 글을 바로 붙여넣으면 민감 정보가 가려져요";

  const policyRow = document.createElement("div");
  policyRow.className = "input-panel__policy-row";
  policyRow.innerHTML = `
    <label class="input-panel__policy-label">
      <span>Policy</span>
      <select class="input-panel__policy-select" data-testid="policy-select">
        <option value="default">default</option>
        <option value="strict_token">strict_token</option>
      </select>
    </label>
    <p class="input-panel__policy-hint">현재 policy 선택은 준비 단계이며, 기본값 실험용 설정으로 요청에 함께 전달됩니다.</p>
  `;
  const policySelect = policyRow.querySelector("select");
  policySelect.value = policy;
  policySelect.disabled = isLoading;
  policySelect.addEventListener("change", () => {
    onPolicyChange(policySelect.value);
  });

  const textarea = document.createElement("textarea");
  textarea.className = "input-panel__textarea";
  textarea.dataset.testid = "text-input";
  textarea.value = value;
  textarea.placeholder = "분석할 원문을 입력하세요.";
  textarea.disabled = isLoading;

  const textSection = document.createElement("div");
  textSection.className = "input-panel__section";
  textSection.style.display = inputMode === "text" ? "block" : "none";
  textSection.innerHTML = `
    <div class="input-panel__section-header">
      <strong>✏️ 글 직접 입력</strong>
      <span>편지, 메모, 채팅 내용을 그대로 붙여넣으세요</span>
    </div>
  `;
  textSection.append(textarea);

  const fileArea = document.createElement("div");
  fileArea.className = "input-panel__section";
  fileArea.style.display = inputMode === "file" ? "block" : "none";
  fileArea.innerHTML = `
    <div class="input-panel__section-header">
      <strong>📁 파일로 올리기</strong>
      <span>컴퓨터에 있는 .txt 파일을 올리면 편해요</span>
    </div>
    <div class="input-panel__file-area${isDragActive ? " input-panel__file-area--drag-active" : ""}">
    <label class="input-panel__file-label">
      <span>📄 .txt 파일만 지원</span>
      <div class="input-panel__file-picker-row">
        <span class="button button--ghost input-panel__file-trigger">파일 선택</span>
        <span class="input-panel__file-name-inline" data-testid="selected-file-inline">
          ${selectedFileName || "선택된 파일 없음"}
        </span>
      </div>
      <input class="input-panel__file-input" type="file" accept=".txt,text/plain" data-testid="file-input" />
    </label>
    <div class="input-panel__dropzone" data-testid="file-dropzone">
      <strong>📁 파일을 여기에 끌어다 놓거나</strong>
      <span>버튼으로 선택해도 돼요</span>
    </div>
    ${
      selectedFileName
        ? `
    <details class="input-panel__file-preview">
      <summary>파일 내용 보기</summary>
      <div class="input-panel__file-preview-box">${escapeHtml(selectedFileContent || "파일 내용을 불러오는 중이거나 표시할 수 없습니다.")}</div>
    </details>
    `
        : ""
    }
    <p class="input-panel__file-hint">현재는 .txt 파일만 지원하며, PDF/DOCX/HWP는 아직 연결되지 않았습니다.</p>
    </div>
  `;
  const fileInput = fileArea.querySelector("input");
  const dropzone = fileArea.querySelector("[data-testid='file-dropzone']");
  fileInput.disabled = isLoading;
  fileInput.addEventListener("change", () => {
    onFileChange(fileInput.files?.[0] ?? null);
  });

  const status = document.createElement("div");
  status.className = `input-panel__status input-panel__status--${statusTone ?? "info"}`;
  status.dataset.testid = "status-message";
  status.setAttribute("aria-live", "polite");
  status.textContent = statusMessage;

  const toolbar = document.createElement("div");
  toolbar.className = "input-panel__toolbar";
  toolbar.innerHTML = `
    <span class="input-panel__meta">${metaText}</span>
    <button type="button" class="button" data-testid="submit-preview">${isLoading ? "불러오는 중..." : "치환 미리보기 생성"}</button>
  `;

  const submitButton = toolbar.querySelector("button");
  submitButton.disabled = isLoading;

  submitButton.addEventListener("click", () => {
    if (inputMode === "file") {
      onFileSubmit(null, policySelect.value);
      return;
    }
    onSubmit(textarea.value, policySelect.value);
  });

  textarea.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      onSubmit(textarea.value, policySelect.value);
    }
  });

  modeSwitch
    .querySelector(`input[name='input-mode'][value='${inputMode}']`)
    ?.setAttribute("checked", "checked");

  modeSwitch.addEventListener("change", () => {
    const mode = getSelectedMode(modeSwitch);
    onModeChange(mode);
  });

  dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("input-panel__dropzone--drag-over");
  });
  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("input-panel__dropzone--drag-over");
  });
  dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("input-panel__dropzone--drag-over");
    onFileDrop(event.dataTransfer?.files?.[0] ?? null);
  });

  panel.body.append(modeSwitch, modeHint);
  if (showPolicy) {
    panel.body.append(policyRow);
  }
  panel.body.append(textSection, fileArea, status, toolbar);
  return panel.element;
}

function getSelectedMode(container) {
  return container.querySelector("input[name='input-mode']:checked")?.value ?? "text";
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
