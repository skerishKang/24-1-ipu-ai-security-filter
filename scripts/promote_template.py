from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWED_APPROVED_TYPES = {
    "person",
    "org",
    "email",
    "phone",
    "amount",
    "date",
    "address",
    "business_reg_no",
    "clause",
    "free_text",
    "text",
    "enum",
    "list_text",
}
LEGACY_TYPE_HINTS = {
    "business_id": "Use 'business_reg_no' before approval.",
}
PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote a reviewed draft template into templates/approved.",
    )
    parser.add_argument("--draft", required=True, help="Path to draft template JSON.")
    parser.add_argument("--version", required=True, help="Approved version, e.g. 1.1.0")
    parser.add_argument("--reviewer", required=True, help="Reviewer or approver identity.")
    parser.add_argument(
        "--approved-at",
        help="ISO 8601 timestamp. Defaults to current local timestamp.",
    )
    parser.add_argument(
        "--updated-by",
        help="Updater identity. Defaults to reviewer.",
    )
    parser.add_argument(
        "--checklist-version",
        default="template-approval-minimum-v1",
        help="Approval checklist version label.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only. Do not write approved file.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_output_path(template_id: str, version: str) -> Path:
    return REPO_ROOT / "templates" / "approved" / template_id / f"v{version}.template.json"


def validate_template(data: dict[str, Any], approved_version: str) -> list[str]:
    errors: list[str] = []

    top_level_required = [
        "template_id",
        "template_name",
        "document_type",
        "version",
        "status",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "fields",
        "template_text",
        "validation_rules",
        "sensitivity_profile",
    ]
    for key in top_level_required:
        value = data.get(key)
        if value in (None, "", []):
            errors.append(f"Missing required top-level field: {key}")

    if data.get("status") not in {"draft", "review"}:
        errors.append("Template status must be 'draft' or 'review' before promotion.")

    if data.get("approval") not in (None, {}):
        errors.append("Draft template approval must be empty before promotion.")

    fields = data.get("fields")
    if not isinstance(fields, list) or not fields:
        errors.append("Template must contain at least one field.")
        return errors

    seen_field_ids: set[str] = set()
    seen_field_names: set[str] = set()
    required_fields_from_fields: set[str] = set()

    for index, field in enumerate(fields, start=1):
        prefix = f"fields[{index}]"
        for key in ("field_id", "field_name", "type", "label", "required", "sensitive", "ui", "render"):
            if key not in field:
                errors.append(f"{prefix} is missing '{key}'.")

        field_id = str(field.get("field_id", "")).strip()
        field_name = str(field.get("field_name", "")).strip()
        field_type = str(field.get("type", "")).strip()
        label = str(field.get("label", "")).strip()

        if not field_id:
            errors.append(f"{prefix} has empty field_id.")
        if not field_name:
            errors.append(f"{prefix} has empty field_name.")
        if not label:
            errors.append(f"{prefix} has empty label.")

        if field_id:
            if field_id in seen_field_ids:
                errors.append(f"Duplicate field_id: {field_id}")
            seen_field_ids.add(field_id)

        if field_name:
            if field_name in seen_field_names:
                errors.append(f"Duplicate field_name: {field_name}")
            seen_field_names.add(field_name)

        if field_type not in ALLOWED_APPROVED_TYPES:
            hint = LEGACY_TYPE_HINTS.get(field_type)
            if hint:
                errors.append(f"{prefix} uses legacy type '{field_type}'. {hint}")
            else:
                errors.append(f"{prefix} uses unsupported approved type '{field_type}'.")

        if field.get("required") is True:
            required_fields_from_fields.add(field_name)

        ui = field.get("ui") or {}
        if not ui.get("widget"):
            errors.append(f"{prefix} is missing ui.widget.")
        if ui.get("order") in (None, ""):
            errors.append(f"{prefix} is missing ui.order.")

        render = field.get("render") or {}
        expected_token = f"{{{{{field_name}}}}}" if field_name else None
        if not render.get("token"):
            errors.append(f"{prefix} is missing render.token.")
        elif expected_token and render.get("token") != expected_token:
            errors.append(
                f"{prefix} render.token must be {expected_token}, got {render.get('token')!r}."
            )

    template_text = str(data.get("template_text", ""))
    placeholders = set(PLACEHOLDER_PATTERN.findall(template_text))
    field_names = seen_field_names

    for placeholder in sorted(placeholders - field_names):
        errors.append(f"template_text placeholder has no matching field: {placeholder}")

    required_fields = set(
        item
        for item in (data.get("validation_rules", {}) or {}).get("required_fields", [])
        if isinstance(item, str)
    )
    missing_required_rules = sorted(required_fields_from_fields - required_fields)
    extra_required_rules = sorted(required_fields - required_fields_from_fields)

    for field_name in missing_required_rules:
        errors.append(
            f"Required field '{field_name}' is not listed in validation_rules.required_fields."
        )
    for field_name in extra_required_rules:
        errors.append(
            f"validation_rules.required_fields contains non-required or unknown field '{field_name}'."
        )

    for field_name in sorted(required_fields_from_fields):
        if field_name not in placeholders:
            errors.append(f"Required field '{field_name}' is not used in template_text.")

    sensitivity_profile = data.get("sensitivity_profile") or {}
    for key in ("profile_id", "level", "default_masking"):
        if not sensitivity_profile.get(key):
            errors.append(f"sensitivity_profile.{key} is required before approval.")

    if sensitivity_profile and not isinstance(sensitivity_profile.get("contains", []), list):
        errors.append("sensitivity_profile.contains must be a list.")

    if not re.fullmatch(r"\d+\.\d+\.\d+", approved_version):
        errors.append("Approved version must match SemVer core format, for example 1.1.0.")

    return errors


def promote_template(
    data: dict[str, Any],
    draft_path: Path,
    version: str,
    reviewer: str,
    approved_at: str,
    updated_by: str,
    checklist_version: str,
) -> tuple[dict[str, Any], Path]:
    promoted = json.loads(json.dumps(data))
    promoted["version"] = version
    promoted["status"] = "approved"
    promoted["updated_at"] = approved_at
    promoted["updated_by"] = updated_by
    promoted["approval"] = {
        "reviewer": reviewer,
        "approved_by": reviewer,
        "approved_at": approved_at,
        "checklist_version": checklist_version,
    }

    source_document = promoted.get("source_document")
    if not isinstance(source_document, dict):
        source_document = {}
        promoted["source_document"] = source_document
    source_document.setdefault("origin", "derived_extraction_draft")
    source_document["draft_template_path"] = str(draft_path.relative_to(REPO_ROOT))

    output_path = build_output_path(str(promoted["template_id"]), version)
    return promoted, output_path


def main() -> int:
    args = parse_args()
    draft_path = (REPO_ROOT / args.draft).resolve() if not Path(args.draft).is_absolute() else Path(args.draft)
    if not draft_path.exists():
        print(f"Draft file not found: {draft_path}", file=sys.stderr)
        return 2

    approved_at = args.approved_at or datetime.now().astimezone().isoformat(timespec="seconds")
    updated_by = args.updated_by or args.reviewer
    data = load_json(draft_path)
    errors = validate_template(data, args.version)

    if errors:
        print("Template validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    promoted, output_path = promote_template(
        data=data,
        draft_path=draft_path,
        version=args.version,
        reviewer=args.reviewer,
        approved_at=approved_at,
        updated_by=updated_by,
        checklist_version=args.checklist_version,
    )

    print(f"Draft: {draft_path}")
    print(f"Approved target: {output_path}")
    print(f"template_id: {promoted['template_id']}")
    print(f"version: {promoted['version']}")
    print(f"status: {promoted['status']}")
    print(f"approved_at: {approved_at}")

    if args.dry_run:
        print("Dry run only. No file written.")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        print(f"Refusing to overwrite existing approved template: {output_path}", file=sys.stderr)
        return 3

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(promoted, file, ensure_ascii=False, indent=2)
        file.write("\n")

    print("Promotion complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
