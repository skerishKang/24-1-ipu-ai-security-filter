import { createPanelFrame } from "../ui/createPanelFrame.js";

export function createInputPanel({
  title = "1. 문서 입력",
  description = "검토할 텍스트를 붙여넣거나 문서·음성 파일을 업로드합니다.",
  value,
  inputMode,
  onModeChange,
  onSubmit,
  onFileSubmit,
  onAudioSubmit,
  policy,
  policySummary,
  onPolicyChange,
  onTaskTypeChange,
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
  metaText = "텍스트는 즉시 실행하고, 파일과 음성은 백엔드 처리 결과를 사용합니다.",
}) {
  const panel = createPanelFrame({
    title,
    description,
    badge: "입력 점검",
  });

  const modeSwitch = document.createElement("div");
  modeSwitch.className = "input-panel__mode-switch";
  modeSwitch.innerHTML = `
    <label class="input-panel__mode-option${inputMode === "text" ? " input-panel__mode-option--active" : ""}">
      <input type="radio" name="input-mode" value="text" data-testid="input-mode-text" />
      <span>텍스트</span>
    </label>
    <label class="input-panel__mode-option${inputMode === "file" ? " input-panel__mode-option--active" : ""}">
      <input type="radio" name="input-mode" value="file" data-testid="input-mode-file" />
      <span>문서 파일</span>
    </label>
    ${
      allowAudioUpload
        ? `
    <label class="input-panel__mode-option${inputMode === "audio" ? " input-panel__mode-option--active" : ""}">
      <input type="radio" name="input-mode" value="audio" data-testid="input-mode-audio" />
      <span>음성 파일</span>
    </label>
    `
        : ""
    }
  `;

  const modeHint = document.createElement("p");
  modeHint.className = "input-panel__mode-hint";
  modeHint.textContent =
    inputMode === "audio"
      ? "음성 파일을 업로드하면 전사 후 민감정보 검토를 진행합니다."
      : inputMode === "file"
        ? "문서 파일을 업로드하면 텍스트를 추출한 뒤 민감정보 검토를 진행합니다."
        : "검사할 텍스트를 직접 붙여넣어 결과를 확인합니다.";

  const policyRow = document.createElement("div");
  policyRow.className = "input-panel__policy-row";
  policyRow.innerHTML = `
    <label class="input-panel__policy-label">
      <span>정책</span>
      <select class="input-panel__policy-select" data-testid="policy-select">
        <option value="default">default · 읽기 쉬운 기본 보호</option>
        <option value="strict_token">strict_token · 보수적 비식별화</option>
        <option value="local_rewrite">local_rewrite · 로컬 모델 보조 치환</option>
      </select>
    </label>
    <p class="input-panel__policy-hint">현재 manual preview는 default, strict_token, local_rewrite 세 가지 preset을 지원합니다.</p>
    <div class="input-panel__policy-summary">
      <strong class="input-panel__policy-summary-title">${escapeHtml(policySummary?.title || "")}</strong>
      <p class="input-panel__policy-summary-body">${escapeHtml(policySummary?.description || "")}</p>
      <p class="input-panel__policy-summary-meta">${escapeHtml(policySummary?.examples || "")}</p>
    </div>
    <label class="input-panel__policy-label" style="margin-top: 12px;">
      <span>작업 유형</span>
      <select class="input-panel__policy-select" data-testid="task-type-select">
        <option value="">없음</option>
        <option value="summarize">요약</option>
        <option value="risk_review">리스크 검토</option>
        <option value="action_items">액션 아이템</option>
      </select>
    </label>
    <p class="input-panel__policy-hint">필요할 때만 외부 전달용 작업 유형을 지정합니다.</p>
  `;
  const policySelect = policyRow.querySelector("select[data-testid='policy-select']");
  const taskTypeSelect = policyRow.querySelector("select[data-testid='task-type-select']");
  policySelect.value = policy;
  policySelect.disabled = isLoading;
  taskTypeSelect.disabled = isLoading;
  policySelect.addEventListener("change", () => {
    onPolicyChange(policySelect.value);
  });
  if (onTaskTypeChange) {
    taskTypeSelect.addEventListener("change", () => {
      onTaskTypeChange(taskTypeSelect.value);
    });
  }

  const textarea = document.createElement("textarea");
  textarea.className = "input-panel__textarea";
  textarea.dataset.testid = "text-input";
  textarea.value = value;
  textarea.placeholder = "검사할 텍스트를 입력하세요.";
  textarea.disabled = isLoading;

  const textSection = document.createElement("div");
  textSection.className = "input-panel__section";
  textSection.style.display = inputMode === "text" ? "block" : "none";
  textSection.innerHTML = `
    <div class="input-panel__section-header">
      <strong>직접 입력</strong>
      <span>메모, 계약 초안, 고객 문구 등을 그대로 붙여넣을 수 있습니다.</span>
    </div>
  `;
  textSection.append(textarea);

  const fileArea = document.createElement("div");
  fileArea.className = "input-panel__section";
  fileArea.style.display = inputMode === "text" ? "none" : "block";
  fileArea.innerHTML = `
    <div class="input-panel__section-header">
      <strong>${inputMode === "audio" ? "음성 파일 업로드" : "문서 파일 업로드"}</strong>
      <span>${
        inputMode === "audio"
          ? "업로드한 음성 파일을 전사한 뒤 검토합니다."
          : "업로드한 문서에서 텍스트를 추출한 뒤 검토합니다."
      }</span>
    </div>
    <div class="input-panel__file-area${isDragActive ? " input-panel__file-area--drag-active" : ""}">
      <label class="input-panel__file-label">
        <span>${inputMode === "audio" ? "지원 형식: .wav, .mp3, .m4a, .mp4, .webm" : "지원 형식: .txt, .md, .csv, .pdf, .docx, .hwpx"}</span>
        <div class="input-panel__file-picker-row">
          <span class="button button--ghost input-panel__file-trigger">파일 선택</span>
          <span class="input-panel__file-name-inline" data-testid="selected-file-inline">
            ${selectedFileName || "선택된 파일 없음"}
          </span>
        </div>
        <input class="input-panel__file-input" type="file" accept="${inputMode === "audio" ? ".wav,.mp3,.m4a,.mp4,.webm,audio/wav,audio/mpeg,audio/mp4,audio/webm,video/mp4" : ".txt,.md,.csv,.pdf,.docx,.hwpx,.hwp,text/plain,text/markdown,text/csv,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/haansofthwpx,application/x-hwp"}" data-testid="file-input" />
      </label>
      <div class="input-panel__dropzone" data-testid="file-dropzone">
        <strong>${inputMode === "audio" ? "여기로 음성 파일을 끌어다 놓으세요" : "여기로 문서 파일을 끌어다 놓으세요"}</strong>
        <span>버튼으로 선택해도 됩니다.</span>
      </div>
      ${
        selectedFileName && inputMode !== "audio"
          ? `
      <details class="input-panel__file-preview">
        <summary>추출 텍스트 미리보기</summary>
        <div class="input-panel__file-preview-box">${escapeHtml(selectedFileContent || "파일 내용을 불러오는 중이거나 미리보기가 없습니다.")}</div>
      </details>
      `
          : ""
      }
      <p class="input-panel__file-hint">${inputMode === "audio" ? "긴 음성은 분할 업로드를 권장합니다." : "바이너리 .hwp는 직접 지원하지 않습니다. 먼저 .hwpx, .pdf, .docx, .txt로 변환하세요."}</p>
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
    <button type="button" class="button" data-testid="submit-preview">${isLoading ? "처리 중..." : "검사 실행"}</button>
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
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
