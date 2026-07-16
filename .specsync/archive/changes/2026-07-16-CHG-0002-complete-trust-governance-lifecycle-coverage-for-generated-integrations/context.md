---
change: CHG-0002-complete-trust-governance-lifecycle-coverage-for-generated-integrations
artifact: context
---

# Context

The Trust rollout already added the four generated agent integrations plus Augur,
Attest, and managed-agent policy files. CHG-0001 covered the plugin, tests,
workflow, Trust policy, specs, and SpecSync workspace, but its affected paths did
not enumerate these generated governance files. Hosted Trust therefore completed
all 33 PostgreSQL tests and then correctly rejected lifecycle coverage.

This successor records that missing governance scope without changing the
PostgreSQL implementation, public contract, or canonical specification.
