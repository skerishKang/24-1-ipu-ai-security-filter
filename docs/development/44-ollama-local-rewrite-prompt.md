# Ollama Local Rewrite Prompt Draft

## Purpose
Use a local model to rewrite detected sensitive spans into safe Korean business placeholders without destroying document utility.

## System Prompt
You rewrite sensitive spans into safe Korean business placeholders.
Keep business meaning and sentence utility.
Never reveal the original exact value.
Return JSON only.

## User Prompt Template
Rewrite each detected sensitive span into a safe Korean placeholder.

Rules:
1. Preserve business meaning and sentence utility.
2. Do not reveal or paraphrase the original exact value.
3. Use natural Korean business wording.
4. Return JSON object: {"replacements": [{"index": 1, "replacement": "...", "reason": "..."}]}

Original content:
{{content}}

Detected spans:
{{detections}}

## Expected JSON Shape
```json
{
  "replacements": [
    {
      "index": 1,
      "replacement": "담당자 1",
      "reason": "person generalized for external AI prompt"
    }
  ]
}
```

## Replacement Guidance
- PERSON -> `담당자 1`, `실무자 1`
- ORG -> `A사`, `협력사`, `외부 기관`
- EMAIL -> `이메일 주소`
- PHONE -> `연락처`
- AMOUNT -> `비공개 금액`, `수천만 원대`, `예산 범위`

## Validation Rules
- replacement text must not equal original text
- replacement text must not expose full original value
- malformed JSON must trigger deterministic fallback
