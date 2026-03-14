import { createAppShell } from "./components/AppShell.js";
import { createCopyPromptPanel } from "./components/CopyPromptPanel.js";
import { createInputPanel } from "./components/InputPanel.js";
import { createReportPanel } from "./components/ReportPanel.js";
import { createResultPanel } from "./components/ResultPanel.js";
import { createSimpleResultPanel } from "./components/SimpleResultPanel.js";
import { createViewModeToggle } from "./components/ViewModeToggle.js";
import {
  fetchManualPreview,
  uploadManualPreviewFile,
} from "./services/manualPreviewApi.js";
import { runManualPreviewMock } from "./services/manualPreviewMock.js";
import {
  classifyFileFailure,
  classifyTextFailure,
  createStatus,
  STATUS_TYPES,
} from "./statusMessages.js";

const app = document.querySelector("#app");
const defaultText =
  "아이피유테크 홍길동 이사는 고객사 contact@ipu.co.kr 과 010-1234-5678 정보를 포함한 제안서를 검토해 주세요. 계약 금액은 12,500,000원입니다.";

const state = {
  originalText: defaultText,
  preview: runManualPreviewMock(defaultText),
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
};

async function updatePreview(nextText, policy = state.policy) {
  state.originalText = nextText;
  state.policy = policy;
  state.lastPreviewLabel = "텍스트 입력 결과";
  state.isLoading = true;
  state.status = createStatus(STATUS_TYPES.BACKEND_REQUEST_LOADING, { policy });
  render();

  try {
    const preview = await fetchManualPreview(nextText, policy);
    state.preview = preview;
    state.source = "backend";
    state.status = createStatus(STATUS_TYPES.BACKEND_SUCCESS, { policy });
  } catch (error) {
    state.preview = runManualPreviewMock(nextText);
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

  if (!targetFile.name.toLowerCase().endsWith(".txt")) {
    state.status = createStatus(STATUS_TYPES.FILE_UNSUPPORTED);
    render();
    return;
  }

  if (targetFile.size === 0) {
    state.status = createStatus(STATUS_TYPES.FILE_EMPTY);
    render();
    return;
  }

  state.isLoading = true;
  state.policy = policy;
  state.selectedFile = targetFile;
  state.selectedFileName = targetFile.name;
  state.lastPreviewLabel = `${targetFile.name} 결과`;
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
  if (file) {
    try {
      state.selectedFileContent = await file.text();
    } catch (error) {
      state.selectedFileContent = "";
    }
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
        "원하는 글을 붙여넣거나 파일을 올리면 <strong>주민번호, 전화번호, 이메일 같은 민감한 정보가 자동으로 가려져</strong> 나옵니다.",
      showPolicy: false,
      metaText: "💡 .txt 파일도 바로 업로드할 수 있어요",
    };
  }

  return {
    title: "1. 원문 입력",
    description:
      "사내 메모, 계약서 초안, 고객 대응 문구 등 민감정보가 포함될 수 있는 원문을 붙여넣거나 .txt 파일로 업로드합니다.",
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
    case STATUS_TYPES.MOCK_FALLBACK:
      return "연결 문제로 예시 결과를 보여주고 있습니다.";
    case STATUS_TYPES.FILE_UNSUPPORTED:
      return "현재는 .txt 파일만 올릴 수 있습니다.";
    case STATUS_TYPES.FILE_EMPTY_SELECTION:
      return "먼저 .txt 파일을 선택해 주세요.";
    case STATUS_TYPES.FILE_EMPTY:
      return "내용이 있는 .txt 파일을 선택해 주세요.";
    case STATUS_TYPES.FILE_REQUEST_FAILED:
      return "파일 처리에 실패했습니다. 다시 시도해 주세요.";
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
      sessionId: `${state.preview.session_id} · ${state.source}`,
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
    policy: state.policy,
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
    metaText: inputPanelCopy.metaText,
  });

  shell.querySelector("[data-slot='input']").append(inputPanel);

  if (state.uiMode === "general") {
    const simpleResultPanel = createSimpleResultPanel({
      originalText: state.preview.original_text,
      replacedText: state.preview.replaced_text,
      protectedCount: state.preview.report.total_detections,
      previewLabel: state.lastPreviewLabel,
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
    });

    const copyPanel = createCopyPromptPanel({
      copyReadyPrompt: state.preview.copy_ready_prompt,
    });

    shell.querySelector("[data-slot='result']").append(resultPanel);
    shell.querySelector("[data-slot='report']").append(reportPanel);
    shell.querySelector("[data-slot='copy']").append(copyPanel);
  }

  app.append(shell);
}

render();
updatePreview(defaultText);
