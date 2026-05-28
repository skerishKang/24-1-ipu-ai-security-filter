# Frontend CSP Guidance

## Purpose

This note records the recommended Content Security Policy for the static frontend deployment path.

The current frontend is intentionally dependency-light and served as static files. Browser-side CSP still provides useful defense in depth, especially for template-mode pages that render approved JSON metadata and generated document previews.

## Recommended Static Deployment Header

For a controlled static deployment, start with this policy and adjust `connect-src` to the actual backend origin.

```http
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self' http://127.0.0.1:8241 http://localhost:8241; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'
```

## Production Notes

- Replace local backend origins in `connect-src` with the production backend URL.
- Do not add `unsafe-inline` unless a hosting constraint makes it unavoidable.
- Keep `object-src 'none'` because the app does not need plugin/object embedding.
- Keep `frame-ancestors 'none'` unless the app is intentionally embedded in a trusted parent.
- Serve template JSON from the same trusted static origin where possible.

## Template Mode Notes

Template mode currently reads approved JSON files from `templates/approved/...` and renders metadata into the UI.

The UI should continue to treat template metadata as data, not markup:

- Escape metadata before `innerHTML` insertion.
- Prefer `textContent` or DOM APIs when adding new template-derived fields.
- Keep generated document previews constrained to text rendering unless a later feature explicitly requires rich markup.

## Relationship to Issue #77

Issue #77 tracks template-mode rendering hardening and CSP guidance. This document covers the CSP guidance side, while `frontend/src/template-mode-main.js` handles the escaping consistency side.
