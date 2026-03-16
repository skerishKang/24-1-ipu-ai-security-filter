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
  "아이피유테크 홍길동 이사는 고객사 contact@ipu.co.kr 과 010-1234-5678 정보를 포함한 제안서를 검토해 주세요. 계약 금액은 12,500,000원입니다.";
const POLICY_PRESETS = {
  default: {
    title: "default: 읽기 쉬운 기본 보호",
    description:
      "직접 표기된 이메일, 전화번호, 직함 포함 이름 중심으로 빠르게 가립니다.",
    examples:
      "예: contact@ipu.co.kr, 010-1234-5678, 홍길동 이사",
  },
  strict_token: {
    title: "strict_token: 더 보수적으로 가립니다",
    description:
      "조직명, 금액, 변형 이메일, 직함 없는 실명 전달 문맥까지 더 넓게 탐지합니다.",
    examples:
      "예: security at ipu dot co kr, 박지은에게 전달, 120,000,000원, 미래전자",
  },
};

const state = {
  originalText: defaultText,
  preview: runManualPreviewMock(defaultText, "default"),
  isLoading: false,
  source: "mock",
  policy: "default",
  inputMode: "text",
  selectedFile: null,
  selectedFileName: "",
  selectedFileContent: "",
  isDragActive: false,
  uiMode: "general",
  lastPreviewLabel: "기본 예시 텍스트",
  status: createStatus(STATUS_TYPES.INITIAL_MOCK),
  restoredText: "",
  restoreStatus: "아직 복원 테스트를 실행하지 않았습니다.",
  isRestoring: false,
};

function getPolicySummary(policy) {
  return POLICY_PRESETS[policy] ?? POLICY_PRESETS.default;
}

function getSessionBadge() {
  if (!state.preview?.session_id) {
    return "";
  }
  return `${state.preview.session_id} · ${state.source}`;
}

async function updatePreview(nextText, policy = state.policy) {
  state.originalText = nextText;
  state.policy = policy;
  state.lastPreviewLabel = "텍스트 입력 결과";
  state.restoredText = "";
  state.restoreStatus = "아직 복원 테스트를 실행하지 않았습니다.";
  state.isLoading = true;
  state.status = createStatus(STATUS_TYPES.BACKEND_REQUEST_LOADING, { policy });
  render();

  try {
    const preview = await fetchManualPreview(nextText, policy);
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
  state.restoreStatus = "아직 복원 테스트를 실행하지 않았습니다.";
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
  state.lastPreviewLabel = `${targetFile.name} 음성 결과`;
  state.restoredText = "";
  state.restoreStatus = "아직 복원 테스트를 실행하지 않았습니다.";
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
      detail: `${file.name} 파일을 선택했습니다. 미리보기를 생성해 주세요.`,
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
    state.restoreStatus = "복원 가능한 세션이나 치환 결과가 없습니다.";
    render();
    return;
  }

  state.isRestoring = true;
  state.restoreStatus = "현재 세션 매핑으로 복원 테스트를 요청하는 중입니다.";
  render();

  try {
    const restored = await restoreManualPreview(
      state.preview.session_id,
      state.preview.replaced_text,
    );
    state.restoredText = restored.restored_text;
    state.restoreStatus = restored.restored
      ? "복원 테스트가 성공했습니다."
      : "복원할 세션 매핑이 없어 치환본을 그대로 유지했습니다.";
  } catch (error) {
    state.restoreStatus = error?.message || "복원 테스트 요청이 실패했습니다.";
  } finally {
    state.isRestoring = false;
    render();
  }
}

function getHeroCopy() {
  if (state.uiMode === "general") {
    return {
      eyebrow: "IPU Easy Mode",
      title: "안전하게 바꿔서 쓰기",
      description:
        "<strong>민감한 정보가 묻어있더라도</strong> 그냥 붙여넣기 전에 이걸 쓰세요!",
    };
  }

  return {
    eyebrow: "IPU Manual Mode",
    title: "보안 치환 워크벤치",
    description:
      "원문을 입력하면 민감정보 탐지, 치환, 리포트, 외부 AI용 복사 프롬프트를 한 화면에서 검토합니다.",
  };
}

function getInputPanelCopy() {
  if (state.uiMode === "general") {
    return {
      title: "내용 입력",
      description:
        "원하는 글을 붙여넣거나 문서/음성 파일을 올리면 <strong>주민번호, 전화번호, 이메일 같은 민감한 정보가 자동으로 가려져</strong> 나옵니다.",
      showPolicy: false,
      metaText: "💡 .txt, .md, .csv, .pdf, .docx, .hwpx 문서와 .wav, .mp3, .m4a, .mp4, .webm 음성도 바로 올릴 수 있어요",
    };
  }

  return {
    title: "1. 원문 입력",
    description:
      "사내 메모, 계약서 초안, 고객 대응 문구 등 민감정보가 포함될 수 있는 원문을 붙여넣거나 텍스트 파일로 업로드합니다.",
    showPolicy: true,
    metaText: "텍스트 입력은 fallback을 유지하고, 파일 업로드는 backend live 응답만 사용합니다.",
  };
}

function getVisibleStatusMessage() {
  if (state.uiMode === "expert") {
    return state.status.message;
  }

  switch (state.status.type) {
    case STATUS_TYPES.INITIAL_MOCK:
      return "준비된 예시 결과를 먼저 보여줍니다.";
    case STATUS_TYPES.BACKEND_REQUEST_LOADING:
    case STATUS_TYPES.FILE_REQUEST_LOADING:
      return "안전한 결과를 준비하는 중입니다.";
    case STATUS_TYPES.BACKEND_SUCCESS:
      return "안전하게 바뀐 텍스트를 준비했습니다.";
    case STATUS_TYPES.FILE_SUCCESS:
      return "파일 내용을 안전하게 바꿔서 보여줍니다.";
    case STATUS_TYPES.AUDIO_REQUEST_LOADING:
      return "음성을 전사한 뒤 안전한 결과를 준비하는 중입니다.";
    case STATUS_TYPES.AUDIO_SUCCESS:
      return "음성 전사 결과를 바탕으로 안전하게 바꿔서 보여줍니다.";
    case STATUS_TYPES.MOCK_FALLBACK:
      return "연결 문제로 예시 결과를 보여주고 있습니다.";
    case STATUS_TYPES.FILE_UNSUPPORTED:
      return "현재는 .txt, .md, .csv, .pdf, .docx, .hwpx 파일만 올릴 수 있습니다.";
    case STATUS_TYPES.FILE_HWP_UNSUPPORTED:
      return "바이너리 .hwp 파일은 아직 직접 읽지 못합니다. .hwpx, .pdf, .docx, .txt로 변환해 주세요.";
    case STATUS_TYPES.FILE_OCR_TOOL_MISSING:
      return "스캔형 PDF OCR 도구가 없습니다. tesseract 와 pdftoppm 설치 후 다시 시도해 주세요.";
    case STATUS_TYPES.FILE_EMPTY_SELECTION:
      return "먼저 파일을 선택해 주세요.";
    case STATUS_TYPES.FILE_SELECTED:
      return state.status.message;
    case STATUS_TYPES.FILE_EMPTY:
      return "내용이 있는 .txt, .md, .csv, .pdf, .docx, .hwpx 파일을 선택해 주세요.";
    case STATUS_TYPES.FILE_TOO_LARGE:
      return "100MB 이하의 .txt, .md, .csv, .pdf, .docx, .hwpx 파일만 올릴 수 있습니다.";
    case STATUS_TYPES.FILE_REQUEST_FAILED:
      return "파일 처리에 실패했습니다. 다시 시도해 주세요.";
    case STATUS_TYPES.AUDIO_SELECTED:
      return state.status.message;
    case STATUS_TYPES.AUDIO_UNSUPPORTED:
      return "현재는 .wav, .mp3, .m4a, .mp4, .webm 음성 파일만 올릴 수 있습니다.";
    case STATUS_TYPES.AUDIO_TOO_LARGE:
      return "100MB 이하의 음성 파일만 올릴 수 있습니다.";
    case STATUS_TYPES.AUDIO_NOT_READY:
      return "로컬 STT가 아직 준비되지 않았습니다.";
    case STATUS_TYPES.AUDIO_REQUEST_FAILED:
      return "음성 처리에 실패했습니다. 다시 시도해 주세요.";
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
      onRestore: restoreCurrentPreview,
      restoredText: state.restoredText,
      restoreStatus: state.restoreStatus,
      isRestoring: state.isRestoring,
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
