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

const app = document.querySelector("#app");
const MAX_UPLOAD_FILE_BYTES = 104_857_600;
const SUPPORTED_UPLOAD_EXTENSIONS = [".txt", ".md", ".csv", ".pdf", ".docx", ".hwpx"];
const KNOWN_BUT_UNSUPPORTED_UPLOAD_EXTENSIONS = [".hwp"];
const SUPPORTED_AUDIO_EXTENSIONS = [".wav", ".mp3", ".m4a", ".mp4", ".webm"];
const defaultText =
  "아이피유 담당자 홍길동은 고객사 문의를 검토 중입니다. 연락처는 contact@ipu.co.kr, 010-1234-5678이며 계약 금액은 12,500,000원입니다.";
const POLICY_PRESETS = {
  default: {
    title: "default · 읽기 쉬운 기본 보호",
    description:
      "이메일, 전화번호, 인명 등 자주 쓰는 항목을 읽기 쉬운 alias 형태로 치환합니다.",
    examples:
      "예: contact@ipu.co.kr, 010-1234-5678, 홍길동 이사",
  },
  strict_token: {
    title: "strict_token · 보수적 비식별화",
    description:
      "조직명, 금액, 변형 이메일, 전달 문맥까지 더 넓게 탐지하고 타입 토큰으로 치환합니다.",
    examples:
      "예: security at ipu dot co kr, 박팀장에게 전달, 120,000,000원, 미래전자",
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
  lastPreviewLabel: "기본 예시 텍스트",
  status: createStatus(STATUS_TYPES.INITIAL_MOCK),
  restoredText: "",
  restoreStatus: "복원 테스트를 아직 실행하지 않았습니다.",
  isRestoring: false,
  aiResponseText: "",
  aiRestoreStatus: "외부 응답을 붙여넣은 뒤 복원할 수 있습니다.",
  aiRestoredText: "",
  isAiRestoring: false,
};

function getPolicySummary(policy) {
  return POLICY_PRESETS[policy] ?? POLICY_PRESETS.default;
}

function getSessionBadge() {
  if (!state.preview?.session_id) {
    return "";
  }
  return `${state.preview.session_id} 쨌 ${state.source}`;
}

async function updatePreview(nextText, policy = state.policy, taskType = state.taskType) {
  state.originalText = nextText;
  state.policy = policy;
  state.taskType = taskType;
  state.lastPreviewLabel = "텍스트 입력 결과";
  state.restoredText = "";
  state.restoreStatus = "복원 테스트를 아직 실행하지 않았습니다.";
  state.aiResponseText = "";
  state.aiRestoreStatus = "외부 응답을 붙여넣은 뒤 복원할 수 있습니다.";
  state.aiRestoredText = "";
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
  state.lastPreviewLabel = `${targetFile.name} 寃곌낵`;
  state.restoredText = "";
  state.restoreStatus = "복원 테스트를 아직 실행하지 않았습니다.";
  state.isDragActive = false;
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
  state.lastPreviewLabel = `${targetFile.name} ?뚯꽦 寃곌낵`;
  state.restoredText = "";
  state.restoreStatus = "복원 테스트를 아직 실행하지 않았습니다.";
  state.isDragActive = false;
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
      detail: `${file.name} ?뚯씪???좏깮?덉뒿?덈떎. 誘몃━蹂닿린瑜??앹꽦??二쇱꽭??`,
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

async function restoreCurrentPreview() {
  if (!state.preview?.session_id || !state.preview?.replaced_text) {
    state.restoreStatus = "복원 테스트를 아직 실행하지 않았습니다.";
    render();
    return;
  }

  state.isRestoring = true;
  state.restoreStatus = "복원 테스트를 아직 실행하지 않았습니다.";
  render();

  try {
    const restored = await restoreManualPreview(
      state.preview.session_id,
      state.preview.replaced_text,
    );
    state.restoredText = restored.restored_text;
    state.restoreStatus = restored.restored
      ? "蹂듭썝 ?뚯뒪?멸? ?깃났?덉뒿?덈떎."
      : "蹂듭썝???몄뀡 留ㅽ븨???놁뼱 移섑솚蹂몄쓣 洹몃?濡??좎??덉뒿?덈떎.";
  } catch (error) {
    state.restoreStatus = error?.message || "蹂듭썝 ?뚯뒪???붿껌???ㅽ뙣?덉뒿?덈떎.";
  } finally {
    state.isRestoring = false;
    render();
  }
}

async function restoreAiResponse() {
  if (!state.preview?.session_id || !state.aiResponseText) {
    state.aiRestoreStatus = "외부 응답을 붙여넣은 뒤 복원할 수 있습니다.";
    render();
    return;
  }

  state.isAiRestoring = true;
  state.aiRestoreStatus = "외부 응답을 붙여넣은 뒤 복원할 수 있습니다.";
  render();

  try {
    const restored = await restoreManualPreview(
      state.preview.session_id,
      state.aiResponseText,
    );
    state.aiRestoredText = restored.restored_text;
    state.aiRestoreStatus = restored.restored
      ? "AI ?묐떟 蹂듭썝???꾨즺?섏뿀?듬땲??"
      : "蹂듭썝???좏겙???놁뼱 洹몃?濡?諛섑솚?섏뿀?듬땲??";
  } catch (error) {
    state.aiRestoreStatus = error?.message || "AI ?묐떟 蹂듭썝???ㅽ뙣?덉뒿?덈떎.";
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
      title: "문서 검사",
      description:
        "민감정보가 포함된 텍스트나 문서를 업로드하고, 비식별 결과를 빠르게 확인합니다.",
    };
  }

  return {
    eyebrow: "IPU Firewall Console",
    title: "문서 검사 콘솔",
    description:
      "입력, 정책 판정, 비식별 결과, 외부 전달 보조 기능을 한 화면에서 검토합니다.",
  };
}

function getInputPanelCopy() {
  if (state.uiMode === "general") {
    return {
      title: "입력",
      description:
        "검사할 텍스트를 붙여넣거나 문서·음성 파일을 업로드하면 민감정보를 자동으로 가립니다.",
      showPolicy: false,
      metaText: "지원 형식: .txt, .md, .csv, .pdf, .docx, .hwpx, .wav, .mp3, .m4a, .mp4, .webm",
    };
  }

  return {
    title: "1. 문서 입력",
    description:
      "검사할 텍스트를 붙여넣거나 문서·음성 파일을 업로드합니다.",
    showPolicy: true,
    metaText: "텍스트는 즉시 검사할 수 있고, 파일 업로드는 백엔드 처리 결과를 사용합니다.",
  };
}

function getVisibleStatusMessage() {
  if (state.uiMode === "expert") {
    return state.status.message;
  }

  switch (state.status.type) {
    case STATUS_TYPES.INITIAL_MOCK:
      return "예시 결과를 먼저 표시하고 있습니다.";
    case STATUS_TYPES.BACKEND_REQUEST_LOADING:
    case STATUS_TYPES.FILE_REQUEST_LOADING:
      return "검사 결과를 생성하는 중입니다.";
    case STATUS_TYPES.BACKEND_SUCCESS:
      return "검사가 완료됐습니다.";
    case STATUS_TYPES.FILE_SUCCESS:
      return "문서 처리 결과를 표시합니다.";
    case STATUS_TYPES.AUDIO_REQUEST_LOADING:
      return "음성 파일을 전사하고 검사하는 중입니다.";
    case STATUS_TYPES.AUDIO_SUCCESS:
      return "음성 기반 검사 결과를 표시합니다.";
    case STATUS_TYPES.MOCK_FALLBACK:
      return "연결 문제로 예시 결과를 표시하고 있습니다.";
    case STATUS_TYPES.FILE_UNSUPPORTED:
      return "현재는 .txt, .md, .csv, .pdf, .docx, .hwpx 파일만 지원합니다.";
    case STATUS_TYPES.FILE_HWP_UNSUPPORTED:
      return "바이너리 .hwp는 직접 지원하지 않습니다. 가능하면 .hwpx, .pdf, .docx, .txt로 변환하세요.";
    case STATUS_TYPES.FILE_OCR_TOOL_MISSING:
      return "스캔 PDF OCR 도구가 없습니다. tesseract 또는 pdftoppm 설치 후 다시 시도하세요.";
    case STATUS_TYPES.FILE_EMPTY_SELECTION:
      return "먼저 파일을 선택하세요.";
    case STATUS_TYPES.FILE_SELECTED:
      return state.status.message;
    case STATUS_TYPES.FILE_EMPTY:
      return "내용이 있는 파일을 선택하세요.";
    case STATUS_TYPES.FILE_TOO_LARGE:
      return "100MB 이하 파일만 업로드할 수 있습니다.";
    case STATUS_TYPES.FILE_REQUEST_FAILED:
      return "파일 처리에 실패했습니다. 다시 시도하세요.";
    case STATUS_TYPES.AUDIO_SELECTED:
      return state.status.message;
    case STATUS_TYPES.AUDIO_UNSUPPORTED:
      return "현재는 .wav, .mp3, .m4a, .mp4, .webm 음성 파일만 지원합니다.";
    case STATUS_TYPES.AUDIO_TOO_LARGE:
      return "100MB 이하 음성 파일만 업로드할 수 있습니다.";
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
    });
    shell.querySelector("[data-slot='result']").append(simpleResultPanel);
  } else {
    const resultPanel = createResultPanel({
      originalText: state.preview.original_text,
      replacedText: state.preview.replaced_text,
      replacements: state.preview.replacements,
    });

    const reportPanel = createReportPanel({
      detections: state.preview.detections,
      report: state.preview.report,
      policySummary: getPolicySummary(state.policy),
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


