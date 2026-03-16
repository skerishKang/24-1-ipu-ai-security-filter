export const STATUS_TYPES = {
  INITIAL_MOCK: "initial-mock",
  BACKEND_REQUEST_LOADING: "backend-request-loading",
  BACKEND_SUCCESS: "backend-success",
  BACKEND_REQUEST_FAILED: "backend-request-failed",
  MOCK_FALLBACK: "mock-fallback",
  FILE_REQUEST_LOADING: "file-request-loading",
  FILE_SUCCESS: "file-success",
  FILE_UNSUPPORTED: "file-unsupported",
  FILE_HWP_UNSUPPORTED: "file-hwp-unsupported",
  FILE_OCR_TOOL_MISSING: "file-ocr-tool-missing",
  FILE_EMPTY_SELECTION: "file-empty-selection",
  FILE_SELECTED: "file-selected",
  FILE_EMPTY: "file-empty",
  FILE_TOO_LARGE: "file-too-large",
  FILE_REQUEST_FAILED: "file-request-failed",
  AUDIO_REQUEST_LOADING: "audio-request-loading",
  AUDIO_SUCCESS: "audio-success",
  AUDIO_SELECTED: "audio-selected",
  AUDIO_UNSUPPORTED: "audio-unsupported",
  AUDIO_TOO_LARGE: "audio-too-large",
  AUDIO_NOT_READY: "audio-not-ready",
  AUDIO_REQUEST_FAILED: "audio-request-failed",
};

export function createStatus(type, options = {}) {
  const policySuffix = options.policy ? ` (policy: ${options.policy})` : "";

  switch (type) {
    case STATUS_TYPES.INITIAL_MOCK:
      return {
        type,
        tone: "info",
        message: "백엔드 연결 전 초기 mock 결과를 표시합니다.",
      };
    case STATUS_TYPES.BACKEND_REQUEST_LOADING:
      return {
        type,
        tone: "info",
        message: `텍스트 manual-preview를 백엔드에 요청하는 중입니다.${policySuffix}`,
      };
    case STATUS_TYPES.BACKEND_SUCCESS:
      return {
        type,
        tone: "success",
        message: `백엔드 응답으로 텍스트 치환 결과를 갱신했습니다.${policySuffix}`,
      };
    case STATUS_TYPES.BACKEND_REQUEST_FAILED:
      return {
        type,
        tone: "error",
        message: options.detail || "텍스트 manual-preview 요청이 실패했습니다.",
      };
    case STATUS_TYPES.MOCK_FALLBACK:
      return {
        type,
        tone: "warning",
        message:
          options.detail ||
          `백엔드 요청이 실패해 mock fallback 결과를 표시합니다.${policySuffix}`,
      };
    case STATUS_TYPES.FILE_REQUEST_LOADING:
      return {
        type,
        tone: "info",
        message: `선택한 파일을 백엔드로 보내 미리보기를 생성하는 중입니다.${policySuffix}`,
      };
    case STATUS_TYPES.FILE_SUCCESS:
      return {
        type,
        tone: "success",
        message: `파일 업로드 결과로 치환 미리보기를 갱신했습니다.${policySuffix}`,
      };
    case STATUS_TYPES.FILE_UNSUPPORTED:
      return {
        type,
        tone: "error",
        message:
          options.detail ||
          "현재는 .txt, .md, .csv, .pdf, .docx, .hwpx 파일만 지원합니다. 다른 형식은 아직 연결되지 않았습니다.",
      };
    case STATUS_TYPES.FILE_HWP_UNSUPPORTED:
      return {
        type,
        tone: "warning",
        message:
          options.detail ||
          "바이너리 .hwp 파일은 아직 직접 읽지 못합니다. .hwpx, .pdf, .docx, .txt 중 하나로 변환한 뒤 다시 올려 주세요.",
      };
    case STATUS_TYPES.FILE_OCR_TOOL_MISSING:
      return {
        type,
        tone: "warning",
        message:
          options.detail ||
          "스캔형 PDF OCR 도구가 없습니다. tesseract 와 pdftoppm 설치 후 다시 시도해 주세요.",
      };
    case STATUS_TYPES.FILE_EMPTY_SELECTION:
      return {
        type,
        tone: "error",
        message: "업로드할 파일을 먼저 선택하세요.",
      };
    case STATUS_TYPES.FILE_SELECTED:
      return {
        type,
        tone: "info",
        message:
          options.detail ||
          "파일을 선택했습니다. 미리보기를 생성해 주세요.",
      };
    case STATUS_TYPES.FILE_EMPTY:
      return {
        type,
        tone: "error",
        message:
          options.detail ||
          "비어 있는 텍스트, PDF, DOCX, HWPX 파일은 처리할 수 없습니다. 내용이 있는 .txt, .md, .csv, .pdf, .docx, .hwpx 파일을 선택하세요.",
      };
    case STATUS_TYPES.FILE_TOO_LARGE:
      return {
        type,
        tone: "error",
        message:
          options.detail ||
          "현재는 100MB 이하의 .txt, .md, .csv, .pdf, .docx, .hwpx 파일만 업로드할 수 있습니다. 더 작은 파일로 나눠 다시 시도하세요.",
      };
    case STATUS_TYPES.FILE_REQUEST_FAILED:
      return {
        type,
        tone: "error",
        message:
          options.detail ||
          "파일 미리보기 요청이 실패했습니다. 백엔드 상태와 파일 내용을 다시 확인하세요.",
      };
    case STATUS_TYPES.AUDIO_REQUEST_LOADING:
      return {
        type,
        tone: "info",
        message: `선택한 음성 파일을 백엔드로 보내 전사 후 미리보기를 생성하는 중입니다.${policySuffix}`,
      };
    case STATUS_TYPES.AUDIO_SUCCESS:
      return {
        type,
        tone: "success",
        message: `음성 업로드 결과로 전사 기반 치환 미리보기를 갱신했습니다.${policySuffix}`,
      };
    case STATUS_TYPES.AUDIO_SELECTED:
      return {
        type,
        tone: "info",
        message: options.detail || "음성 파일을 선택했습니다. 미리보기를 생성해 주세요.",
      };
    case STATUS_TYPES.AUDIO_UNSUPPORTED:
      return {
        type,
        tone: "error",
        message:
          options.detail ||
          "현재는 .wav, .mp3, .m4a, .mp4, .webm 음성 파일만 고려합니다.",
      };
    case STATUS_TYPES.AUDIO_TOO_LARGE:
      return {
        type,
        tone: "error",
        message:
          options.detail || "현재는 100MB 이하의 음성 파일만 업로드할 수 있습니다.",
      };
    case STATUS_TYPES.AUDIO_NOT_READY:
      return {
        type,
        tone: "warning",
        message:
          options.detail || "로컬 STT가 아직 준비되지 않았습니다. backend audio transcriber 설정을 확인해 주세요.",
      };
    case STATUS_TYPES.AUDIO_REQUEST_FAILED:
      return {
        type,
        tone: "error",
        message:
          options.detail || "음성 미리보기 요청이 실패했습니다. backend 상태와 음성 파일을 다시 확인하세요.",
      };
    default:
      return {
        type,
        tone: "info",
        message: options.detail || "",
      };
  }
}

export function classifyTextFailure(error, policy) {
  const detail = error?.message || "백엔드 요청이 실패해 mock fallback 결과를 표시합니다.";
  return createStatus(STATUS_TYPES.MOCK_FALLBACK, {
    policy,
    detail,
  });
}

export function classifyFileFailure(error) {
  const detail = error?.message || "";
  const loweredDetail = detail.toLowerCase();

  if (error?.code === "file-unsupported" || loweredDetail.includes(".txt, .md, .csv, .pdf, .docx, .hwpx 파일만 지원")) {
    return createStatus(STATUS_TYPES.FILE_UNSUPPORTED, { detail });
  }

  if (error?.code === "file-hwp-unsupported" || loweredDetail.includes("바이너리 .hwp 파일")) {
    return createStatus(STATUS_TYPES.FILE_HWP_UNSUPPORTED, { detail });
  }

  if (error?.code === "file-ocr-tool-missing" || loweredDetail.includes("tesseract") || loweredDetail.includes("pdftoppm")) {
    return createStatus(STATUS_TYPES.FILE_OCR_TOOL_MISSING, { detail });
  }

  if (
    error?.code === "file-empty" ||
    loweredDetail.includes("비어 있는 텍스트 파일")
  ) {
    return createStatus(STATUS_TYPES.FILE_EMPTY, { detail });
  }

  if (
    error?.code === "file-too-large" ||
    loweredDetail.includes("100mb") ||
    loweredDetail.includes("100 mb") ||
    loweredDetail.includes("too large")
  ) {
    return createStatus(STATUS_TYPES.FILE_TOO_LARGE, { detail });
  }

  if (
    error?.code === "file-invalid-encoding" ||
    loweredDetail.includes("utf-8 텍스트 파일만 지원")
  ) {
    return createStatus(STATUS_TYPES.FILE_UNSUPPORTED, { detail });
  }

  return createStatus(STATUS_TYPES.FILE_REQUEST_FAILED, {
    detail: detail || undefined,
  });
}

export function classifyAudioFailure(error) {
  const detail = error?.message || "";
  const loweredDetail = detail.toLowerCase();

  if (error?.code === "audio-not-ready" || loweredDetail.includes("stt")) {
    return createStatus(STATUS_TYPES.AUDIO_NOT_READY, { detail });
  }

  if (error?.code === "audio-unsupported" || loweredDetail.includes(".wav, .mp3, .m4a, .mp4, .webm")) {
    return createStatus(STATUS_TYPES.AUDIO_UNSUPPORTED, { detail });
  }

  if (error?.code === "audio-too-large" || loweredDetail.includes("100mb") || loweredDetail.includes("100 mb")) {
    return createStatus(STATUS_TYPES.AUDIO_TOO_LARGE, { detail });
  }

  return createStatus(STATUS_TYPES.AUDIO_REQUEST_FAILED, {
    detail: detail || undefined,
  });
}
