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
    regex: /\b\d{1,3}(?:,\d{3})*(?:만원|원)\b/g,
    token: "AMOUNT",
    reason: "금액 및 재무 정보 보호",
  },
  {
    type: "PERSON",
    regex: /[가-힣]{2,4}\s?(?:이사|부장|과장|대표|매니저|님)/g,
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

export function runManualPreviewMock(originalText, policy = "default", taskType = "") {
  const sessionId = createSessionId();
  const detections = [];
  const replacements = [];
  const replacementPlan = [];
  const counters = {};
  const strategy = policy === "strict_token" ? "strict_token" : "alias";

  for (const pattern of PATTERNS) {
    const matches = [...originalText.matchAll(pattern.regex)];
    for (const match of matches) {
      const label = match[0];
      counters[pattern.type] = (counters[pattern.type] ?? 0) + 1;
      const tokenPrefix = strategy === "strict_token" ? pattern.token : `${pattern.token}_ALIAS`;
      const token = `[${tokenPrefix}_${String(counters[pattern.type]).padStart(2, "0")}]`;
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
      replacementPlan.push({
        start: match.index ?? 0,
        end: (match.index ?? 0) + label.length,
        token,
      });
    }
  }

  let replacedText = originalText;
  for (const replacement of [...replacementPlan].sort((left, right) => right.start - left.start)) {
    replacedText =
      replacedText.slice(0, replacement.start) +
      replacement.token +
      replacedText.slice(replacement.end);
  }

  const report = buildMockReport(detections, replacements, strategy);
  const readiness = buildMockReadiness(detections, report);

  return {
    session_id: sessionId,
    original_text: originalText,
    replaced_text: replacedText,
    detections,
    replacements,
    report,
    task_type: taskType,
    readiness,
    copy_ready_prompt: buildCopyReadyPrompt(replacedText, report, taskType),
  };
}

function buildMockReport(detections, replacements, strategy) {
  const totalDetections = Math.max(detections.length, replacements.length);
  const reviewStatus = totalDetections > 0 ? "review-required" : "clean";
  return {
    total_detections: totalDetections,
    risk_level: totalDetections >= 3 ? "high-risk" : totalDetections > 0 ? "moderate-risk" : "low-risk",
    strategy,
    review_status: reviewStatus,
  };
}

function buildMockReadiness(detections, report) {
  const totalDetections = detections.length;
  const riskLevel = report.risk_level;
  const reviewStatus = report.review_status;

  let readyToSend = true;
  let status = "pass";
  let reason = "";
  const remainingRisks = [...new Set(detections.map((d) => d.type))];

  if (totalDetections === 0) {
    readyToSend = true;
    status = "pass";
    reason = "추가로 탐지된 민감정보가 없습니다. 외부 전송이 가능합니다.";
  } else if (reviewStatus === "clean") {
    readyToSend = true;
    status = "pass";
    reason = "검토 상태가 clean입니다.";
  } else if (riskLevel === "high-risk") {
    readyToSend = false;
    status = "fail";
    reason = `높은 위험도(high-risk)로 ${totalDetections}개의 민감정보를 먼저 검토해야 합니다.`;
  } else if (riskLevel === "moderate-risk") {
    readyToSend = false;
    status = "review-required";
    reason = `중간 위험도(moderate-risk)로 ${totalDetections}개의 민감정보가 탐지되었습니다. 전송 전 검토가 필요합니다.`;
  } else {
    readyToSend = false;
    status = "review-required";
    reason = `${totalDetections}개의 민감정보가 탐지되었습니다. 전송 전 검토가 필요합니다.`;
  }

  return {
    ready_to_send: readyToSend,
    review_status: status,
    reason,
    remaining_risks: remainingRisks,
    detection_count: totalDetections,
    risk_level: riskLevel,
  };
}

const TASK_GUIDES = {
  summarize: "아래 문서의 핵심 내용을 3~5문장 이내로 요약해 주세요.",
  risk_review: "아래 문서에서 확인되는 잠재 리스크나 문제점을 검토해 정리해 주세요.",
  action_items: "아래 문서에서 실행해야 할 작업이나 액션 아이템을 추출해 주세요.",
};

const RESPONSE_FORMAT_GUIDES = {
  summarize: "요약은 단락 형태로 작성해 주세요.",
  risk_review: "리스크 검토는 항목별로 (1) 리스크 내용 (2) 심각도 (3) 권장 조치 형태로 작성해 주세요.",
  action_items: "액션 아이템은 체크리스트 형태로 작성해 주세요.",
};

function buildCopyReadyPrompt(replacedText, report, taskType = "") {
  const lines = [
    "[IPU External Transfer Text]",
    "아래 내용은 민감정보가 비식별 처리된 상태입니다.",
    "토큰이나 일반화 표현의 실제 원문을 추정하지 말고, 현재 보이는 텍스트만 기준으로 작업해 주세요.",
    "",
    "[Review Status]",
    `risk_level: ${report.risk_level}`,
    `review_status: ${report.review_status}`,
    "",
  ];

  if (taskType && TASK_GUIDES[taskType]) {
    lines.push("[Requested Task]", TASK_GUIDES[taskType], "", "[Response Format]", RESPONSE_FORMAT_GUIDES[taskType], "");
  }

  lines.push("[Sanitized Text]", replacedText);

  return lines.join("\n");
}
