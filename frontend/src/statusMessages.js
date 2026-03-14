export const STATUS_TYPES = {
  INITIAL_MOCK: "initial-mock",
  BACKEND_REQUEST_LOADING: "backend-request-loading",
  BACKEND_SUCCESS: "backend-success",
  BACKEND_REQUEST_FAILED: "backend-request-failed",
  MOCK_FALLBACK: "mock-fallback",
  FILE_REQUEST_LOADING: "file-request-loading",
  FILE_SUCCESS: "file-success",
  FILE_UNSUPPORTED: "file-unsupported",
  FILE_EMPTY_SELECTION: "file-empty-selection",
  FILE_EMPTY: "file-empty",
  FILE_REQUEST_FAILED: "file-request-failed",
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
        message: `선택한 .txt 파일을 백엔드로 보내 미리보기를 생성하는 중입니다.${policySuffix}`,
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
          "현재는 UTF-8 기반 .txt 파일만 지원합니다. 다른 형식은 아직 연결되지 않았습니다.",
      };
    case STATUS_TYPES.FILE_EMPTY_SELECTION:
      return {
        type,
        tone: "error",
        message: "업로드할 .txt 파일을 먼저 선택하세요.",
      };
    case STATUS_TYPES.FILE_EMPTY:
      return {
        type,
        tone: "error",
        message:
          options.detail ||
          "비어 있는 텍스트 파일은 처리할 수 없습니다. 내용이 있는 .txt 파일을 선택하세요.",
      };
    case STATUS_TYPES.FILE_REQUEST_FAILED:
      return {
        type,
        tone: "error",
        message:
          options.detail ||
          "파일 미리보기 요청이 실패했습니다. 백엔드 상태와 파일 내용을 다시 확인하세요.",
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

  if (error?.code === "file-unsupported" || loweredDetail.includes(".txt 파일만 지원")) {
    return createStatus(STATUS_TYPES.FILE_UNSUPPORTED, { detail });
  }

  if (
    error?.code === "file-empty" ||
    loweredDetail.includes("비어 있는 텍스트 파일")
  ) {
    return createStatus(STATUS_TYPES.FILE_EMPTY, { detail });
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
