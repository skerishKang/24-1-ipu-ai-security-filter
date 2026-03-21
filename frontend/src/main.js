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
  "고객 문의가 접수되었습니다. 연락처는 contact@ipu.co.kr, 010-1234-5678이며 계약 금액은 12,500,000 KRW입니다.";
const POLICY_PRESETS = {
  default: {
    title: "default | 읽기 쉬운 기본 보호",
    description:
      "이메일, 전화번호, 담당자명처럼 자주 나오는 항목을 읽기 쉬운 alias 토큰으로 치환합니다.",
    examples:
      "예: contact@ipu.co.kr, 010-1234-5678, 홍길동 과장",
  },
  strict_token: {
    title: "strict_token | 보수적 비식별화",
    description:
      "조직명과 금액까지 더 넓게 탐지하고, 유형이 드러나는 strict token으로 치환합니다.",
    examples:
      "예: security at ipu dot co kr, 박 부장 전달, 120,000,000 KRW, 미래전자",
  },
  local_rewrite: {
    title: "local_rewrite | 로컬 모델 보조 치환",
    description:
      "strict_token 수준으로 탐지한 뒤, 더 읽기 쉬운 일반화 문장으로 다시 씁니다.",
    examples:
      "예: 담당자 1, A사 1, 이메일 주소 1, 비공개 금액 1",
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
  lastPreviewLabel: "기본 샘플 결과",
  status: createStatus(STATUS_TYPES.INITIAL_MOCK),
  restoredText: "",
  restoreStatus: "복원 테스트를 아직 실행하지 않았습니다.",
  isRestoring: false,
  aiResponseText: "",
  aiRestoreStatus: "외부 응답을 붙여넣으면 원문 용어를 복원할 수 있습니다.",
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
  state.lastPreviewLabel = "텍스트 미리보기 결과";
  state.restoredText = "";
  state.restoreStatus = "복원 테스트를 아직 실행하지 않았습니다.";
  state.aiResponseText = "";
  state.aiRestoreStatus = "외부 응답을 붙여넣으면 원문 용어를 복원할 수 있습니다.";
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
  state.lastPreviewLabel = `${targetFile.name} 결과`;
  state.restoredText = "";
  state.restoreStatus = "복원 테스트를 아직 실행하지 않았습니다.";
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
  state.lastPreviewLabel = `${targetFile.name} 음성 결과`;
  state.restoredText = "";
  state.restoreStatus = "복원 테스트를 아직 실행하지 않았습니다.";
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
      error: error?.message || "비교 결과를 불러오지 못했습니다.",
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
    state.restoreStatus = "복원 테스트를 아직 실행하지 않았습니다.";
    render();
    return;
  }

  state.isRestoring = true;
  state.restoreStatus = "복원 요청을 처리하고 있습니다.";
  render();

  try {
    const restored = await restoreManualPreview(
      state.preview.session_id,
      state.preview.replaced_text,
    );
    state.restoredText = restored.restored_text;
    state.restoreStatus = restored.restored
      ? "복원 테스트가 완료되었습니다."
      : "복원 가능한 세션 매핑이 없어 현재 비식별 결과를 유지했습니다.";
  } catch (error) {
    state.restoreStatus = error?.message || "복원 요청이 실패했습니다.";
  } finally {
    state.isRestoring = false;
    render();
  }
}

async function restoreAiResponse() {
  if (!state.preview?.session_id || !state.aiResponseText) {
    state.aiRestoreStatus = "외부 응답을 붙여넣으면 원문 용어를 복원할 수 있습니다.";
    render();
    return;
  }

  state.isAiRestoring = true;
  state.aiRestoreStatus = "외부 응답 복원을 진행하고 있습니다.";
  render();

  try {
    const restored = await restoreManualPreview(
      state.preview.session_id,
      state.aiResponseText,
    );
    state.aiRestoredText = restored.restored_text;
    state.aiRestoreStatus = restored.restored
      ? "외부 응답 복원이 완료되었습니다."
      : "복원 토큰이 없어 현재 응답을 그대로 유지했습니다.";
  } catch (error) {
    state.aiRestoreStatus = error?.message || "외부 응답 복원이 실패했습니다.";
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
      title: "문서 사전 점검",
      description:
        "텍스트나 문서를 올려 외부 전달 전에 비식별 결과를 빠르게 검토합니다.",
    };
  }

  return {
    eyebrow: "IPU Firewall Console",
    title: "문서 검토 콘솔",
    description:
      "입력 원문, 정책 상태, 비식별 결과, 외부 전달 보조를 한 화면에서 검토합니다.",
  };
}

function getInputPanelCopy() {
  if (state.uiMode === "general") {
    return {
      title: "입력",
      description:
        "외부 AI에 보내기 전, 텍스트나 문서·음성 파일에 비식별 처리를 적용합니다.",
      showPolicy: false,
      metaText: "지원 형식: .txt, .md, .csv, .pdf, .docx, .hwpx, .wav, .mp3, .m4a, .mp4, .webm",
    };
  }

  return {
    title: "1. Document input",
    description:
      "검토할 텍스트를 붙여넣거나 문서·음성 파일을 업로드합니다.",
    showPolicy: true,
    metaText: "텍스트는 즉시 실행하고, 파일과 음성은 백엔드 처리 결과를 사용합니다.",
  };
}

function getVisibleStatusMessage() {
  if (state.uiMode === "expert") {
    return state.status.message;
  }

  switch (state.status.type) {
    case STATUS_TYPES.INITIAL_MOCK:
      return "기본 샘플 결과를 보여주고 있습니다.";
    case STATUS_TYPES.BACKEND_REQUEST_LOADING:
    case STATUS_TYPES.FILE_REQUEST_LOADING:
      return "비식별 결과를 생성하고 있습니다.";
    case STATUS_TYPES.BACKEND_SUCCESS:
      return "비식별 점검이 완료되었습니다.";
    case STATUS_TYPES.FILE_SUCCESS:
      return "처리된 문서 결과를 보여주고 있습니다.";
    case STATUS_TYPES.AUDIO_REQUEST_LOADING:
      return "음성을 전사하고 비식별 점검을 진행하고 있습니다.";
    case STATUS_TYPES.AUDIO_SUCCESS:
      return "음성 기반 점검 결과를 보여주고 있습니다.";
    case STATUS_TYPES.MOCK_FALLBACK:
      return "백엔드를 사용할 수 없어 mock 결과를 표시합니다.";
    case STATUS_TYPES.FILE_UNSUPPORTED:
      return "지원 문서 형식은 .txt, .md, .csv, .pdf, .docx, .hwpx 입니다.";
    case STATUS_TYPES.FILE_HWP_UNSUPPORTED:
      return "바이너리 .hwp는 직접 지원하지 않습니다. 먼저 .hwpx, .pdf, .docx, .txt로 변환하세요.";
    case STATUS_TYPES.FILE_OCR_TOOL_MISSING:
      return "스캔 PDF 처리를 위한 OCR 도구가 준비되지 않았습니다.";
    case STATUS_TYPES.FILE_EMPTY_SELECTION:
      return "먼저 파일을 선택하세요.";
    case STATUS_TYPES.FILE_SELECTED:
      return state.status.message;
    case STATUS_TYPES.FILE_EMPTY:
      return "읽을 수 있는 내용이 있는 파일을 선택하세요.";
    case STATUS_TYPES.FILE_TOO_LARGE:
      return "파일은 최대 100MB까지 지원합니다.";
    case STATUS_TYPES.FILE_REQUEST_FAILED:
      return "파일 처리에 실패했습니다. 다시 시도하세요.";
    case STATUS_TYPES.AUDIO_SELECTED:
      return state.status.message;
    case STATUS_TYPES.AUDIO_UNSUPPORTED:
      return "지원 음성 형식은 .wav, .mp3, .m4a, .mp4, .webm 입니다.";
    case STATUS_TYPES.AUDIO_TOO_LARGE:
      return "음성 파일은 최대 100MB까지 지원합니다.";
    case STATUS_TYPES.AUDIO_NOT_READY:
      return "로컬 STT가 아직 준비되지 않았습니다.";
    case STATUS_TYPES.AUDIO_REQUEST_FAILED:
      return "음성 처리에 실패했습니다. 다시 시도하세요.";
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




