---
change: CHG-0002-complete-trust-governance-lifecycle-coverage-for-generated-integrations
artifact: testing
---

# Testing

Local verification requires `fledge lanes run verify`, strict SpecSync at the
committed threshold, and `specsync agents status` with Claude, Cursor, Codex,
and Gemini installed. Trust doctor and verification must also pass using the
committed standard policy.

Hosted acceptance requires the exact pushed head to pass the unified `trust`
job with its PostgreSQL 16 service and all CodeQL checks. A prior hosted run's
33 passing native cases are retained as history but do not substitute for a
green run on the corrected head.
