export function buildDetectionChips(detections) {
  const counts = detections.reduce((acc, item) => {
    acc[item.type] = (acc[item.type] ?? 0) + 1;
    return acc;
  }, {});

  return Object.entries(counts).map(([type, count]) => {
    const chip = document.createElement("span");
    chip.className = "summary-chip";
    chip.textContent = `${type} ${count}`;
    return chip;
  });
}

export function createModeBadge(selectedPolicy, strategy) {
  const badge = document.createElement("span");
  const mode = selectedPolicy || strategy || "default";
  const variant = mode === "local_rewrite" ? "rewrite" : mode === "strict_token" ? "strict" : "default";
  badge.className = `policy-badge policy-badge--${variant}`;
  badge.textContent = `정책 ${mode}`;
  return badge;
}

export function createStatusBadge(report) {
  const badge = document.createElement("span");
  const variant = report.review_status === "review-required" ? "warning" : "clean";
  badge.className = `review-badge review-badge--${variant}`;
  badge.textContent = `${formatReviewStatus(report.review_status)} · ${formatRiskLevel(report.risk_level)}`;
  return badge;
}

export function formatReviewStatus(value) {
  if (value === "review-required") return "검토 필요";
  if (value === "clean") return "전송 가능";
  return value;
}

export function formatRiskLevel(value) {
  if (value === "high-risk") return "높음";
  if (value === "moderate-risk") return "중간";
  if (value === "low-risk") return "낮음";
  return value;
}

export function highlightText(text, values, className) {
  const container = document.createElement("span");
  const source = String(text ?? "");
  const uniqueValues = [...new Set(values.filter(Boolean).map(String))]
    .sort((left, right) => right.length - left.length);

  if (uniqueValues.length === 0) {
    container.textContent = source;
    return container;
  }

  const normalizedSource = source.toLowerCase();
  let cursor = 0;
  const matches = [];

  for (const value of uniqueValues) {
    if (!value) continue;
    const normalizedValue = value.toLowerCase();
    let searchFrom = 0;
    while (true) {
      const index = normalizedSource.indexOf(normalizedValue, searchFrom);
      if (index === -1) break;
      matches.push({ start: index, end: index + value.length, value: source.slice(index, index + value.length) });
      searchFrom = index + Math.max(value.length, 1);
    }
  }

  matches.sort((left, right) => left.start - right.start || right.end - left.end);

  const nonOverlapping = [];
  let lastEnd = 0;
  for (const match of matches) {
    if (match.start < lastEnd) continue;
    nonOverlapping.push(match);
    lastEnd = match.end;
  }

  for (const match of nonOverlapping) {
    if (cursor < match.start) {
      container.append(document.createTextNode(source.slice(cursor, match.start)));
    }
    const mark = document.createElement("mark");
    mark.className = className;
    mark.textContent = match.value;
    container.append(mark);
    cursor = match.end;
  }

  if (cursor < source.length) {
    container.append(document.createTextNode(source.slice(cursor)));
  }

  return container;
}

export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
