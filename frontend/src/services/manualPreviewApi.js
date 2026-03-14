import { getManualPreviewUrl } from "../config.js";

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
  const manualPreviewFileUrl = `${getManualPreviewUrl()}/file`;
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
      risk_level: data.report?.risk_level ?? "low-risk",
      strategy: data.report?.strategy ?? "strict_token",
      review_status: data.report?.review_status ?? "clean",
    },
    copy_ready_prompt: data.copy_ready_prompt ?? "",
  };
}

function createApiError(code, message) {
  const error = new Error(message);
  error.code = code;
  return error;
}

function classifyFileResponseCode(status, detail) {
  if (status === 415 || detail.includes(".txt 파일만 지원")) {
    return "file-unsupported";
  }

  if (status === 400 && detail.includes("비어 있는 텍스트 파일")) {
    return "file-empty";
  }

  if (status === 400 && detail.includes("UTF-8 텍스트 파일만 지원")) {
    return "file-invalid-encoding";
  }

  return "file-request-failed";
}
