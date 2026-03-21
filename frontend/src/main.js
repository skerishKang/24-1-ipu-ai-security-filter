import { createAppShell } from "./components/AppShell.js";
import { createCopyPromptPanel } from "./components/CopyPromptPanel.js";
import { createInputPanel } from "./components/InputPanel.js";
import { createReportPanel } from "./components/ReportPanel.js";
import { createResultPanel } from "./components/ResultPanel.js";
import { createSimpleResultPanel } from "./components/SimpleResultPanel.js";
import { createViewModeToggle } from "./components/ViewModeToggle.js";
import {
  uploadManualPreviewAudio,
  fetchManualPreview,
  restoreManualPreview,
  uploadManualPreviewFile,
} from "./services/manualPreviewApi.js";
import { runManualPreviewMock } from "./services/manualPreviewMock.js";
import {
  classifyAudioFailure,
  classifyFileFailure,
  classifyTextFailure,
  createStatus,
  STATUS_TYPES,
} from "./statusMessages.js";

document.title = "IPU AI Firewall Console";

const app = document.querySelector("#app");
const MAX_UPLOAD_FILE_BYTES = 104_857_600;
const SUPPORTED_UPLOAD_EXTENSIONS = [".txt", ".md", ".csv", ".pdf", ".docx", ".hwpx"];
const KNOWN_BUT_UNSUPPORTED_UPLOAD_EXTENSIONS = [".hwp"];
const SUPPORTED_AUDIO_EXTENSIONS = [".wav", ".mp3", ".m4a", ".mp4", ".webm"];
const defaultText =
  "A customer inquiry has been received. Contact details are contact@ipu.co.kr and 010-1234-5678, and the contract amount is 12,500,000 KRW.";
const POLICY_PRESETS = {
  default: {
    title: "default | readable baseline",
    description:
      "Masks common items such as email, phone number, and person names with readable alias tokens.",
    examples:
      "e.g. contact@ipu.co.kr, 010-1234-5678, Hong Gil-dong director",
  },
  strict_token: {
    title: "strict_token | conservative masking",
    description:
      "Detects a wider range including organization and amount, then replaces them with explicit strict tokens.",
    examples:
      "e.g. security at ipu dot co kr, deliver to Park, 120,000,000 KRW, Mirae Electronics",
  },
  local_rewrite: {
    title: "local_rewrite | local-model rewrite",
    description:
      "Uses strict_token-level detection and rewrites the result into more readable generalized business text.",
    examples:
      "e.g. Contact 1, Company A 1, Email 1, Private amount 1",
  },
};
const state = {
  originalText: defaultText,
  preview: runManualPreviewMock(defaultText, "default"),
  isLoading: false,
  source: "mock",
  policy: "default",
  taskType: "",
  inputMode: "text",
  selectedFile: null,
  selectedFileName: "",
  selectedFileContent: "",
  isDragActive: false,
  uiMode: "general",
  lastPreviewLabel: "Default sample result",
  status: createStatus(STATUS_TYPES.INITIAL_MOCK),
  restoredText: "",
  restoreStatus: "Restore test has not been run yet.",
  isRestoring: false,
  aiResponseText: "",
  aiRestoreStatus: "Paste an AI response to restore original terms.",
  aiRestoredText: "",
  isAiRestoring: false,
  comparison: {
    loading: false,
    error: "",
    sourceText: "",
    strictToken: null,
    localRewrite: null,
  },
};

function getPolicySummary(policy) {
  return POLICY_PRESETS[policy] ?? POLICY_PRESETS.default;
}

function getSessionBadge() {
  if (!state.preview?.session_id) {
    return "";
  }
  return `${state.preview.session_id} | ${state.source}`;
}

async function updatePreview(nextText, policy = state.policy, taskType = state.taskType) {
  state.originalText = nextText;
  state.policy = policy;
  state.taskType = taskType;
  state.lastPreviewLabel = "Text preview result";
  state.restoredText = "";
  state.restoreStatus = "Restore test has not been run yet.";
  state.aiResponseText = "";
  state.aiRestoreStatus = "Paste an AI response to restore original terms.";
  state.aiRestoredText = "";
  resetComparison();
  state.isLoading = true;
  state.status = createStatus(STATUS_TYPES.BACKEND_REQUEST_LOADING, { policy });
  render();

  try {
    const preview = await fetchManualPreview(nextText, policy, taskType);
    state.preview = preview;
    state.source = "backend";
    state.status = createStatus(STATUS_TYPES.BACKEND_SUCCESS, { policy });
  } catch (error) {
    state.preview = runManualPreviewMock(nextText, policy);
    state.source = "mock-fallback";
    state.status = classifyTextFailure(error, policy);
  } finally {
    state.isLoading = false;
    render();
  }
}

async function updateFilePreview(file, policy = state.policy) {
  const targetFile = file ?? state.selectedFile;

  if (!targetFile) {
    state.status = createStatus(STATUS_TYPES.FILE_EMPTY_SELECTION);
    render();
    return;
  }

  if (isKnownButUnsupportedUploadFile(targetFile.name)) {
    state.status = createStatus(STATUS_TYPES.FILE_HWP_UNSUPPORTED);
    render();
    return;
  }

  if (!isSupportedUploadFile(targetFile.name)) {
    state.status = createStatus(STATUS_TYPES.FILE_UNSUPPORTED);
    render();
    return;
  }

  if (targetFile.size === 0) {
    state.status = createStatus(STATUS_TYPES.FILE_EMPTY);
    render();
    return;
  }

  if (targetFile.size > MAX_UPLOAD_FILE_BYTES) {
    state.status = createStatus(STATUS_TYPES.FILE_TOO_LARGE);
    render();
    return;
  }

  state.isLoading = true;
  state.policy = policy;
  state.selectedFile = targetFile;
  state.selectedFileName = targetFile.name;
  state.lastPreviewLabel = `${targetFile.name} result`;
  state.restoredText = "";
  state.restoreStatus = "Restore test has not been run yet.";
  state.isDragActive = false;
  resetComparison();
  state.status = createStatus(STATUS_TYPES.FILE_REQUEST_LOADING, { policy });
  render();

  try {
    const preview = await uploadManualPreviewFile(targetFile, policy);
    state.preview = preview;
    state.originalText = preview.original_text;
    state.source = "backend-file";
    state.status = createStatus(STATUS_TYPES.FILE_SUCCESS, { policy });
  } catch (error) {
    state.source = "file-error";
    state.status = classifyFileFailure(error);
  } finally {
    state.isLoading = false;
    render();
  }
}

async function updateAudioPreview(file, policy = state.policy) {
  const targetFile = file ?? state.selectedFile;

  if (!targetFile) {
    state.status = createStatus(STATUS_TYPES.FILE_EMPTY_SELECTION);
    render();
    return;
  }

  if (!isSupportedAudioUploadFile(targetFile.name)) {
    state.status = createStatus(STATUS_TYPES.AUDIO_UNSUPPORTED);
    render();
    return;
  }

  if (targetFile.size === 0) {
    state.status = createStatus(STATUS_TYPES.FILE_EMPTY);
    render();
    return;
  }

  if (targetFile.size > MAX_UPLOAD_FILE_BYTES) {
    state.status = createStatus(STATUS_TYPES.AUDIO_TOO_LARGE);
    render();
    return;
  }

  state.isLoading = true;
  state.policy = policy;
  state.selectedFile = targetFile;
  state.selectedFileName = targetFile.name;
  state.lastPreviewLabel = `${targetFile.name} audio result`;
  state.restoredText = "";
  state.restoreStatus = "Restore test has not been run yet.";
  state.isDragActive = false;
  resetComparison();
  state.status = createStatus(STATUS_TYPES.AUDIO_REQUEST_LOADING, { policy });
  render();

  try {
    const preview = await uploadManualPreviewAudio(targetFile, policy);
    state.preview = preview;
    state.originalText = preview.original_text;
    state.source = "backend-audio";
    state.status = createStatus(STATUS_TYPES.AUDIO_SUCCESS, { policy });
  } catch (error) {
    state.source = "audio-error";
    state.status = classifyAudioFailure(error);
  } finally {
    state.isLoading = false;
    render();
  }
}

function setInputMode(mode) {
  state.inputMode = mode;
  state.isDragActive = false;
  render();
}

async function setSelectedFile(file) {
  state.selectedFile = file;
  state.selectedFileName = file?.name ?? "";
  state.selectedFileContent = "";
  state.isDragActive = false;
  if (!file) {
    render();
    return;
  }

  if (isKnownButUnsupportedUploadFile(file.name)) {
    state.status = createStatus(STATUS_TYPES.FILE_HWP_UNSUPPORTED);
  } else if (state.inputMode === "audio" && !isSupportedAudioUploadFile(file.name)) {
    state.status = createStatus(STATUS_TYPES.AUDIO_UNSUPPORTED);
  } else if (state.inputMode !== "audio" && !isSupportedUploadFile(file.name)) {
    state.status = createStatus(STATUS_TYPES.FILE_UNSUPPORTED);
  } else if (file.size === 0) {
    state.status = createStatus(STATUS_TYPES.FILE_EMPTY);
  } else if (file.size > MAX_UPLOAD_FILE_BYTES) {
    state.status = createStatus(
      state.inputMode === "audio" ? STATUS_TYPES.AUDIO_TOO_LARGE : STATUS_TYPES.FILE_TOO_LARGE,
    );
  } else {
    state.status = createStatus(
      state.inputMode === "audio" ? STATUS_TYPES.AUDIO_SELECTED : STATUS_TYPES.FILE_SELECTED,
      {
        detail: `${file.name} 파일이 선택되었습니다. 내용을 확인한 뒤 검사 실행을 눌러 진행하세요.`, 
      },
    );
  }

  try {
    state.selectedFileContent = state.inputMode === "audio" ? "" : await file.text();
  } catch (error) {
    state.selectedFileContent = "";
  }
  render();
}

function handleFileDrop(file) {
  state.isDragActive = false;
  void setSelectedFile(file);
}

function setUiMode(mode) {
  state.uiMode = mode;
  render();
}

function resetComparison() {
  state.comparison = {
    loading: false,
    error: "",
    sourceText: "",
    strictToken: null,
    localRewrite: null,
  };
}

async function fetchPolicyPreview(text, policy, taskType = state.taskType) {
  try {
    return await fetchManualPreview(text, policy, taskType);
  } catch (error) {
    return runManualPreviewMock(text, policy);
  }
}

async function loadComparison() {
  const sourceText = state.preview?.original_text || state.originalText;
  if (!sourceText) {
    return;
  }

  if (
    state.comparison.sourceText === sourceText &&
    state.comparison.strictToken &&
    state.comparison.localRewrite
  ) {
    return;
  }

  state.comparison = {
    loading: true,
    error: "",
    sourceText,
    strictToken: null,
    localRewrite: null,
  };
  render();

  try {
    const [strictToken, localRewrite] = await Promise.all([
      fetchPolicyPreview(sourceText, "strict_token", state.taskType),
      fetchPolicyPreview(sourceText, "local_rewrite", state.taskType),
    ]);
    state.comparison = {
      loading: false,
      error: "",
      sourceText,
      strictToken,
      localRewrite,
    };
  } catch (error) {
    state.comparison = {
      loading: false,
      error: error?.message || "Failed to load comparison previews.",
      sourceText,
      strictToken: null,
      localRewrite: null,
    };
  } finally {
    render();
  }
}

function clearComparison() {
  resetComparison();
  render();
}

async function restoreCurrentPreview() {
  if (!state.preview?.session_id || !state.preview?.replaced_text) {
    state.restoreStatus = "Restore test has not been run yet.";
    render();
    return;
  }

  state.isRestoring = true;
  state.restoreStatus = "Restore request in progress.";
  render();

  try {
    const restored = await restoreManualPreview(
      state.preview.session_id,
      state.preview.replaced_text,
    );
    state.restoredText = restored.restored_text;
    state.restoreStatus = restored.restored
      ? "Restore test completed successfully."
      : "No restorable session mapping was found, so the sanitized text was kept as-is.";
  } catch (error) {
    state.restoreStatus = error?.message || "Restore request failed.";
  } finally {
    state.isRestoring = false;
    render();
  }
}

async function restoreAiResponse() {
  if (!state.preview?.session_id || !state.aiResponseText) {
    state.aiRestoreStatus = "Paste an AI response to restore original terms.";
    render();
    return;
  }

  state.isAiRestoring = true;
  state.aiRestoreStatus = "AI response restore in progress.";
  render();

  try {
    const restored = await restoreManualPreview(
      state.preview.session_id,
      state.aiResponseText,
    );
    state.aiRestoredText = restored.restored_text;
    state.aiRestoreStatus = restored.restored
      ? "AI response restore completed."
      : "No restore token was found, so the response was returned unchanged.";
  } catch (error) {
    state.aiRestoreStatus = error?.message || "AI response restore failed.";
  } finally {
    state.isAiRestoring = false;
    render();
  }
}

function handleAiResponseChange(text) {
  state.aiResponseText = text;
}

function getHeroCopy() {
  if (state.uiMode === "general") {
    return {
      eyebrow: "IPU Firewall",
      title: "Document screening",
      description:
        "Upload text or a document to quickly review the sanitized result before external sharing.",
    };
  }

  return {
    eyebrow: "IPU Firewall Console",
    title: "Document review console",
    description:
      "Inspect input, policy status, sanitized output, and external transfer guidance in one place.",
  };
}

function getInputPanelCopy() {
  if (state.uiMode === "general") {
    return {
      title: "Input",
      description:
        "Paste text or upload a document or audio file to apply masking before external AI use.",
      showPolicy: false,
      metaText: "Supported: .txt, .md, .csv, .pdf, .docx, .hwpx, .wav, .mp3, .m4a, .mp4, .webm",
    };
  }

  return {
    title: "1. Document input",
    description:
      "Paste text or upload a document or audio file for review.",
    showPolicy: true,
    metaText: "Text runs immediately. File and audio uploads use backend processing.",
  };
}

function getVisibleStatusMessage() {
  if (state.uiMode === "expert") {
    return state.status.message;
  }

  switch (state.status.type) {
    case STATUS_TYPES.INITIAL_MOCK:
      return "Showing a default sample result.";
    case STATUS_TYPES.BACKEND_REQUEST_LOADING:
    case STATUS_TYPES.FILE_REQUEST_LOADING:
      return "Generating the screening result.";
    case STATUS_TYPES.BACKEND_SUCCESS:
      return "Screening is complete.";
    case STATUS_TYPES.FILE_SUCCESS:
      return "Showing the processed document result.";
    case STATUS_TYPES.AUDIO_REQUEST_LOADING:
      return "Transcribing and screening the audio file.";
    case STATUS_TYPES.AUDIO_SUCCESS:
      return "Showing the audio-based screening result.";
    case STATUS_TYPES.MOCK_FALLBACK:
      return "Backend is unavailable, so a mock result is shown.";
    case STATUS_TYPES.FILE_UNSUPPORTED:
      return "Supported file types are .txt, .md, .csv, .pdf, .docx, and .hwpx.";
    case STATUS_TYPES.FILE_HWP_UNSUPPORTED:
      return "Binary .hwp is not supported directly. Convert it to .hwpx, .pdf, .docx, or .txt first.";
    case STATUS_TYPES.FILE_OCR_TOOL_MISSING:
      return "OCR tools are missing for scanned PDF handling.";
    case STATUS_TYPES.FILE_EMPTY_SELECTION:
      return "Select a file first.";
    case STATUS_TYPES.FILE_SELECTED:
      return state.status.message;
    case STATUS_TYPES.FILE_EMPTY:
      return "Select a file that contains readable content.";
    case STATUS_TYPES.FILE_TOO_LARGE:
      return "Only files up to 100MB are supported.";
    case STATUS_TYPES.FILE_REQUEST_FAILED:
      return "File processing failed. Try again.";
    case STATUS_TYPES.AUDIO_SELECTED:
      return state.status.message;
    case STATUS_TYPES.AUDIO_UNSUPPORTED:
      return "Supported audio types are .wav, .mp3, .m4a, .mp4, and .webm.";
    case STATUS_TYPES.AUDIO_TOO_LARGE:
      return "Only audio files up to 100MB are supported.";
    case STATUS_TYPES.AUDIO_NOT_READY:
      return "Local STT is not ready yet.";
    case STATUS_TYPES.AUDIO_REQUEST_FAILED:
      return "Audio processing failed. Try again.";
    default:
      return state.status.message;
  }
}

function render() {
  app.innerHTML = "";

  const heroCopy = getHeroCopy();
  const inputPanelCopy = getInputPanelCopy();
  const modeToggle = createViewModeToggle({
    value: state.uiMode,
    onChange: setUiMode,
  });

  const shell = createAppShell({
    hero: {
      eyebrow: heroCopy.eyebrow,
      title: heroCopy.title,
      description: heroCopy.description,
      sessionId: getSessionBadge(),
    },
    modeToggle,
    layoutMode: state.uiMode,
    showSession: state.uiMode === "expert",
  });

  const inputPanel = createInputPanel({
    title: inputPanelCopy.title,
    description: inputPanelCopy.description,
    value: state.originalText,
    inputMode: state.inputMode,
    onModeChange: setInputMode,
    onSubmit: updatePreview,
    onFileSubmit: updateFilePreview,
    onAudioSubmit: updateAudioPreview,
    policy: state.policy,
    policySummary: getPolicySummary(state.policy),
    onPolicyChange: (policy) => {
      state.policy = policy;
    },
    onTaskTypeChange: (taskType) => {
      state.taskType = taskType;
    },
    selectedFileName: state.selectedFileName,
    selectedFileContent: state.selectedFileContent,
    isDragActive: state.isDragActive,
    onFileChange: (file) => {
      void setSelectedFile(file);
    },
    onFileDrop: handleFileDrop,
    isLoading: state.isLoading,
    statusMessage: getVisibleStatusMessage(),
    statusTone: state.status.tone,
    showPolicy: inputPanelCopy.showPolicy,
    allowAudioUpload: true,
    metaText: inputPanelCopy.metaText,
  });

  shell.querySelector("[data-slot='input']").append(inputPanel);

  if (state.uiMode === "general") {
    const simpleResultPanel = createSimpleResultPanel({
      originalText: state.preview.original_text,
      replacedText: state.preview.replaced_text,
      protectedCount: state.preview.report.total_detections,
      previewLabel: state.lastPreviewLabel,
      policySummary: getPolicySummary(state.policy),
      replacements: state.preview.replacements,
      detections: state.preview.detections,
      report: state.preview.report,
      selectedPolicy: state.policy,
    });
    shell.querySelector("[data-slot='result']").append(simpleResultPanel);
  } else {
    const resultPanel = createResultPanel({
      originalText: state.preview.original_text,
      replacedText: state.preview.replaced_text,
      replacements: state.preview.replacements,
      detections: state.preview.detections,
      report: state.preview.report,
      selectedPolicy: state.policy,
      comparison: state.comparison,
      onLoadComparison: loadComparison,
      onClearComparison: clearComparison,
      policyLookup: getPolicySummary,
    });

    const reportPanel = createReportPanel({
      detections: state.preview.detections,
      report: state.preview.report,
      policySummary: getPolicySummary(state.policy),
      selectedPolicy: state.policy,
    });

    const copyPanel = createCopyPromptPanel({
      copyReadyPrompt: state.preview.copy_ready_prompt,
      readiness: state.preview.readiness,
      onRestore: restoreCurrentPreview,
      restoredText: state.restoredText,
      restoreStatus: state.restoreStatus,
      isRestoring: state.isRestoring,
      aiResponseText: state.aiResponseText,
      onAiResponseChange: handleAiResponseChange,
      onRestoreAiResponse: restoreAiResponse,
      aiRestoreStatus: state.aiRestoreStatus,
      aiRestoredText: state.aiRestoredText,
      isAiRestoring: state.isAiRestoring,
    });

    shell.querySelector("[data-slot='result']").append(resultPanel);
    shell.querySelector("[data-slot='report']").append(reportPanel);
    shell.querySelector("[data-slot='copy']").append(copyPanel);
  }

  app.append(shell);
}

updatePreview(defaultText);

function isSupportedUploadFile(filename) {
  const lowered = filename.toLowerCase();
  return SUPPORTED_UPLOAD_EXTENSIONS.some((extension) => lowered.endsWith(extension));
}

function isSupportedAudioUploadFile(filename) {
  const lowered = filename.toLowerCase();
  return SUPPORTED_AUDIO_EXTENSIONS.some((extension) => lowered.endsWith(extension));
}

function isKnownButUnsupportedUploadFile(filename) {
  const lowered = filename.toLowerCase();
  return KNOWN_BUT_UNSUPPORTED_UPLOAD_EXTENSIONS.some((extension) => lowered.endsWith(extension));
}




