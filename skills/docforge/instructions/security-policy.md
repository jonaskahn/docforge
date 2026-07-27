# Security Policy — Instruction Template

Craft guidance for writing root `SECURITY.md` / `docs/security/README.md`.
Content contract (must-present, keep-out, Diátaxis mode): `references/document-catalog.md`
→ "security/README.md (posture) and root SECURITY.md (disclosure)" and `references/risk-docs.md`.
Depth: `references/depth-and-audience.md`.

## Purpose
Give security researchers a safe, obvious way to report vulnerabilities, plus scope and timeline.

## Data Requirements
- No source data — these are policy choices by the repo owner.
- External values become typed tokens: `<SECURITY_CONTACT>`, `<SLA_RESPONSE_HOURS>`, `<DISCLOSURE_URL>`.

## Template Structure
- Lead with: "We take security seriously. Here's how to report vulnerabilities."
- Reporting method: a role address or security.txt contact (RFC 9116); never the public issue
  tracker for vulnerabilities; optionally a GPG key.
- Scope: in-scope issue types (e.g. auth flaws, data exposure, injection) and out-of-scope ones
  (e.g. non-exploitable bugs, social engineering).
- Response timeline: acknowledgment window, patch target, disclosure timeline.
- Recognition: credit-in-release-notes vs confidential; hall of fame / compensation if any.

## Provenance Requirements
- Reference organization security policies if applicable.
- Link the RFC 9116 security.txt definition (auto-discoverable at /.well-known/security.txt).
- Cross-reference reference/limitations.md if known vulnerabilities exist.

## Notes
- Keep it under a page; make the contact method obvious — reports are time-sensitive.
- Use a role address, not an individual's name.
- If your forge offers a private security-advisory feature, mention it host-neutrally.
- Don't publish this unless prepared to respond — inaction erodes trust.
