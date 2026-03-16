import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createInputPanel({
  title = "1. 원문 입력",
  description = "사내 메모, 계약서 초안, 고객 대응 문구 등 민감정보가 포함될 수 있는 원문을 붙여넣거나 텍스트 파일로 업로드합니다.",
  value,
  inputMode,
  onModeChange,
  onSubmit,
  onFileSubmit,
  onAudioSubmit,
  policy,
  policySummary,
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
  allowAudioUpload = false,
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
      <span>텍스트 파일 업로드</span>
    </label>
    ${
      allowAudioUpload
        ? `
    <label class="input-panel__mode-option${inputMode === "audio" ? " input-panel__mode-option--active" : ""}">
      <input type="radio" name="input-mode" value="audio" data-testid="input-mode-audio" />
      <span>음성 업로드</span>
    </label>
    `
        : ""
    }
  `;

  const modeHint = document.createElement("p");
  modeHint.className = "input-panel__mode-hint";
  modeHint.textContent =
    inputMode === "audio"
      ? "🎙️ 음성을 전사한 뒤 민감 정보를 가립니다"
      : inputMode === "file"
      ? "📁 파일을 올리면 민감 정보가 가려져요"
      : "✏️ 글을 바로 붙여넣으면 민감 정보가 가려져요";

  const policyRow = document.createElement("div");
  policyRow.className = "input-panel__policy-row";
  policyRow.innerHTML = `
    <label class="input-panel__policy-label">
      <span>Policy</span>
      <select class="input-panel__policy-select" data-testid="policy-select">
        <option value="default">default · 읽기 쉬운 기본 보호</option>
        <option value="strict_token">strict_token · 더 보수적 비식별화</option>
      </select>
    </label>
    <p class="input-panel__policy-hint">현재 manual-preview는 default와 strict_token 두 가지 공식 preset만 지원합니다.</p>
    <div class="input-panel__policy-summary">
      <strong class="input-panel__policy-summary-title">${escapeHtml(policySummary?.title || "")}</strong>
      <p class="input-panel__policy-summary-body">${escapeHtml(policySummary?.description || "")}</p>
      <p class="input-panel__policy-summary-meta">${escapeHtml(policySummary?.examples || "")}</p>
    </div>
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
  fileArea.style.display = inputMode === "text" ? "none" : "block";
  fileArea.innerHTML = `
    <div class="input-panel__section-header">
      <strong>${inputMode === "audio" ? "🎙️ 음성 파일 올리기" : "📁 파일로 올리기"}</strong>
      <span>${
        inputMode === "audio"
          ? "짧은 음성 파일을 올리면 전사 후 민감정보를 가립니다"
          : "컴퓨터에 있는 .txt, .md, .csv, .pdf, .docx, .hwpx 파일을 올리면 편해요"
      }</span>
    </div>
    <div class="input-panel__file-area${isDragActive ? " input-panel__file-area--drag-active" : ""}">
    <label class="input-panel__file-label">
      <span>${inputMode === "audio" ? "🎧 .wav / .mp3 / .m4a / .mp4 / .webm 지원" : "📄 .txt / .md / .csv / .pdf / .docx / .hwpx 지원"}</span>
      <div class="input-panel__file-picker-row">
        <span class="button button--ghost input-panel__file-trigger">파일 선택</span>
        <span class="input-panel__file-name-inline" data-testid="selected-file-inline">
          ${selectedFileName || "선택된 파일 없음"}
        </span>
      </div>
      <input class="input-panel__file-input" type="file" accept="${inputMode === "audio" ? ".wav,.mp3,.m4a,.mp4,.webm,audio/wav,audio/mpeg,audio/mp4,audio/webm,video/mp4" : ".txt,.md,.csv,.pdf,.docx,.hwpx,.hwp,text/plain,text/markdown,text/csv,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/haansofthwpx,application/x-hwp"}" data-testid="file-input" />
    </label>
    <div class="input-panel__dropzone" data-testid="file-dropzone">
      <strong>${inputMode === "audio" ? "🎙️ 음성 파일을 여기에 끌어다 놓거나" : "📁 파일을 여기에 끌어다 놓거나"}</strong>
      <span>버튼으로 선택해도 돼요</span>
    </div>
    ${
      selectedFileName && inputMode !== "audio"
        ? `
    <details class="input-panel__file-preview">
      <summary>파일 내용 보기</summary>
      <div class="input-panel__file-preview-box">${escapeHtml(selectedFileContent || "파일 내용을 불러오는 중이거나 표시할 수 없습니다.")}</div>
    </details>
    `
        : ""
    }
    <p class="input-panel__file-hint">${inputMode === "audio" ? "현재는 .wav, .mp3, .m4a, .mp4, .webm 음성 파일을 고려합니다. 일반인/전문가 모드 모두에서 노출하며 backend live 응답만 사용합니다. 긴 음성은 분할 후 업로드를 권장합니다." : "현재는 .txt, .md, .csv, .pdf, .docx, .hwpx 파일을 지원합니다. 바이너리 .hwp 는 먼저 .hwpx, .pdf, .docx, .txt 중 하나로 변환해야 합니다."}</p>
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
    if (inputMode === "audio") {
      onAudioSubmit(null, policySelect.value);
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
