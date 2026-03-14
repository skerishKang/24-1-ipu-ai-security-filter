import { createSessionId } from "../utils/createSessionId.js";

const PATTERNS = [
  {
    type: "EMAIL",
    regex: /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi,
    token: "EMAIL",
    reason: "외부 전송 시 이메일 주소 직접 노출 방지",
  },
  {
    type: "PHONE",
    regex: /01[0-9]-\d{3,4}-\d{4}/g,
    token: "PHONE",
    reason: "연락처 직접 노출 방지",
  },
  {
    type: "AMOUNT",
    regex: /\b\d{1,3}(?:,\d{3})*(?:원|만원|억원)\b/g,
    token: "AMOUNT",
    reason: "계약 금액 및 재무 정보 보호",
  },
  {
    type: "PERSON",
    regex: /[가-힣]{2,4}\s?(이사|부장|과장|대표|매니저|님)/g,
    token: "PERSON",
    reason: "담당자 실명 및 직함 보호",
  },
  {
    type: "ORG",
    regex: /[가-힣A-Za-z]+(?:테크|전자|금융|그룹|기업|회사)/g,
    token: "ORG",
    reason: "조직명 보호",
  },
];

export function runManualPreviewMock(originalText) {
  const sessionId = createSessionId();
  let replacedText = originalText;
  const detections = [];
  const replacements = [];
  const counters = {};

  for (const pattern of PATTERNS) {
    const matches = [...originalText.matchAll(pattern.regex)];
    for (const match of matches) {
      const label = match[0];
      counters[pattern.type] = (counters[pattern.type] ?? 0) + 1;
      const token = `[${pattern.token}_${String(counters[pattern.type]).padStart(2, "0")}]`;
      replacedText = replacedText.replace(label, token);
      detections.push({
        type: pattern.type,
        label,
        start: match.index,
        end: (match.index ?? 0) + label.length,
        score: 0.88,
        note: pattern.reason,
      });
      replacements.push({
        type: pattern.type,
        original: label,
        replaced: token,
        reason: pattern.reason,
      });
    }
  }

  const report = buildMockReport(detections);

  return {
    session_id: sessionId,
    original_text: originalText,
    replaced_text: replacedText,
    detections,
    replacements,
    report,
    copy_ready_prompt: buildCopyReadyPrompt(replacedText, report),
  };
}

function buildMockReport(detections) {
  const reviewStatus = detections.length > 0 ? "review-required" : "clean";
  return {
    total_detections: detections.length,
    risk_level: detections.length >= 3 ? "high-risk" : detections.length > 0 ? "moderate-risk" : "low-risk",
    strategy: "strict_token",
    review_status: reviewStatus,
  };
}

function buildCopyReadyPrompt(replacedText, report) {
  return [
    "[IPU Manual Mode Prompt]",
    "아래 내용은 민감정보가 세션 기반 토큰으로 치환된 상태입니다.",
    "토큰을 유지한 채 문맥만 분석하고, 토큰의 실제 의미를 추정하지 마세요.",
    "",
    "[Security Review]",
    `risk_level: ${report.risk_level}`,
    `review_status: ${report.review_status}`,
    "",
    "[Redacted Input]",
    replacedText,
  ].join("\n");
}
