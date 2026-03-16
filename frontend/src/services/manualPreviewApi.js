import {
  getManualPreviewAudioUrl,
  getManualPreviewFileUrl,
  getManualPreviewRestoreUrl,
  getManualPreviewUrl,
} from "../config.js";

export async function fetchManualPreview(content, policy = "default") {
  const payload = buildManualPreviewPayload(content, policy);
  const manualPreviewUrl = getManualPreviewUrl();

  let response;
  try {
    response = await fetch(manualPreviewUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    throw createApiError(
      "backend-unreachable",
      "백엔드에 연결할 수 없어 mock fallback 결과를 표시합니다.",
    );
  }

  if (!response.ok) {
    throw createApiError(
      "backend-response-failed",
      `백엔드 응답이 실패하여 mock fallback 결과를 표시합니다. (${response.status})`,
    );
  }

  let data;
  try {
    data = await response.json();
  } catch (error) {
    throw createApiError(
      "backend-invalid-json",
      "백엔드 응답 JSON을 해석할 수 없어 mock fallback 결과를 표시합니다.",
    );
  }

  return normalizeManualPreviewResponse(data);
}

export async function uploadManualPreviewFile(file, policy = "default") {
  const manualPreviewFileUrl = getManualPreviewFileUrl();
  const formData = new FormData();
  formData.append("file", file);
  formData.append("policy", policy);

  let response;
  try {
    response = await fetch(manualPreviewFileUrl, {
      method: "POST",
      body: formData,
    });
  } catch (error) {
    throw createApiError(
      "file-backend-unreachable",
      "백엔드에 연결할 수 없어 파일 미리보기를 생성하지 못했습니다.",
    );
  }

  if (!response.ok) {
    let detail = "";
    try {
      const errorBody = await response.json();
      detail = errorBody.detail ? ` ${errorBody.detail}` : "";
    } catch (error) {
      detail = "";
    }
    throw createApiError(
      classifyFileResponseCode(response.status, detail),
      `파일 미리보기 요청이 실패했습니다.(${response.status})${detail}`,
    );
  }

  let data;
  try {
    data = await response.json();
  } catch (error) {
    throw createApiError(
      "file-invalid-json",
      "파일 미리보기 응답 JSON을 해석할 수 없습니다.",
    );
  }

  return normalizeManualPreviewResponse(data);
}

export async function uploadManualPreviewAudio(file, policy = "default") {
  const manualPreviewAudioUrl = getManualPreviewAudioUrl();
  const formData = new FormData();
  formData.append("file", file);
  formData.append("policy", policy);

  let response;
  try {
    response = await fetch(manualPreviewAudioUrl, {
      method: "POST",
      body: formData,
    });
  } catch (error) {
    throw createApiError(
      "audio-backend-unreachable",
      "백엔드에 연결할 수 없어 음성 미리보기를 생성하지 못했습니다.",
    );
  }

  if (!response.ok) {
    let detail = "";
    try {
      const errorBody = await response.json();
      detail = errorBody.detail ? ` ${errorBody.detail}` : "";
    } catch (error) {
      detail = "";
    }
    throw createApiError(
      classifyAudioResponseCode(response.status, detail),
      `음성 미리보기 요청이 실패했습니다.(${response.status})${detail}`,
    );
  }

  let data;
  try {
    data = await response.json();
  } catch (error) {
    throw createApiError(
      "audio-invalid-json",
      "음성 미리보기 응답 JSON을 해석할 수 없습니다.",
    );
  }

  return normalizeManualPreviewResponse(data);
}

export async function restoreManualPreview(sessionId, replacedText) {
  const manualPreviewRestoreUrl = getManualPreviewRestoreUrl();

  let response;
  try {
    response = await fetch(manualPreviewRestoreUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        replaced_text: replacedText,
      }),
    });
  } catch (error) {
    throw createApiError("restore-backend-unreachable", "복원 API에 연결할 수 없습니다.");
  }

  if (!response.ok) {
    throw createApiError(
      "restore-backend-response-failed",
      `복원 API 응답이 실패했습니다. (${response.status})`,
    );
  }

  let data;
  try {
    data = await response.json();
  } catch (error) {
    throw createApiError("restore-invalid-json", "복원 응답 JSON을 해석할 수 없습니다.");
  }

  return {
    session_id: data.session_id ?? "",
    restored_text: data.restored_text ?? "",
    restored: Boolean(data.restored),
  };
}

export function buildManualPreviewPayload(content, policy = "default") {
  return {
    content,
    content_type: "text",
    policy,
  };
}

function normalizeManualPreviewResponse(data) {
  return {
    session_id: data.session_id ?? "",
    original_text: data.original_text ?? "",
    replaced_text: data.replaced_text ?? "",
    detections: Array.isArray(data.detections) ? data.detections : [],
    replacements: Array.isArray(data.replacements) ? data.replacements : [],
    report: {
      total_detections: data.report?.total_detections ?? 0,
      risk_level: normalizeRiskLevel(data.report?.risk_level),
      strategy: normalizeStrategy(data.report?.strategy),
      review_status: normalizeReviewStatus(data.report?.review_status),
    },
    copy_ready_prompt: data.copy_ready_prompt ?? "",
  };
}

function normalizeRiskLevel(value) {
  if (value === "moderate-risk" || value === "high-risk" || value === "low-risk") {
    return value;
  }

  return "low-risk";
}

function normalizeStrategy(value) {
  if (value === "alias" || value === "strict_token") {
    return value;
  }

  return "alias";
}

function normalizeReviewStatus(value) {
  if (value === "clean" || value === "review-required") {
    return value;
  }

  return "clean";
}

function createApiError(code, message) {
  const error = new Error(message);
  error.code = code;
  return error;
}

function classifyFileResponseCode(status, detail) {
  if (status === 415 && detail.includes("tesseract") && detail.includes("pdftoppm")) {
    return "file-ocr-tool-missing";
  }

  if (status === 415 && detail.includes("바이너리 .hwp 파일")) {
    return "file-hwp-unsupported";
  }

  if (status === 415 || detail.includes(".txt, .md, .csv, .pdf, .docx, .hwpx 파일만 지원")) {
    return "file-unsupported";
  }

  if (status === 400 && detail.includes("비어 있는 텍스트 파일")) {
    return "file-empty";
  }

  if (status === 413 || (status === 400 && (detail.includes("100MB") || detail.includes("100 MB")))) {
    return "file-too-large";
  }

  if (status === 400 && detail.includes("UTF-8 텍스트 파일만 지원")) {
    return "file-invalid-encoding";
  }

  return "file-request-failed";
}

function classifyAudioResponseCode(status, detail) {
  if (status === 501 || detail.includes("STT")) {
    return "audio-not-ready";
  }

  if (status === 415 || detail.includes(".wav, .mp3, .m4a, .mp4, .webm")) {
    return "audio-unsupported";
  }

  if (status === 413 || detail.includes("100MB") || detail.includes("100 MB")) {
    return "audio-too-large";
  }

  return "audio-request-failed";
}
