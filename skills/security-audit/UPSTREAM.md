# Upstream provenance

This directory vendors Cloudflare's `security-audit` skill.

- Repository: https://github.com/cloudflare/security-audit-skill
- Source revision: `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`
- Source directory: `skills/security-audit/`
- Imported: November 4, 2026
- License: MIT, copyright Cloudflare, Inc. See [LICENSE](LICENSE).

All 20 upstream skill, companion, schema, validator, and test files are retained
without modifications. The local additions are this provenance note and a copy
of the upstream repository's license. No hooks or dependency installers are
added, and inclusion in this collection does not run an audit or enable global
agent instructions.

The workflow is agent-neutral. Guidance mode covers focused security questions;
full audit mode requires an explicit audit request. Target-controlled execution
requires the upstream sandbox and resource-isolation controls. Read
[SKILL.md](SKILL.md) before using the workflow.

## Validator regression checks

The validators and their tests use built-in Node.js modules only:

```sh
node --test skills/security-audit/validate-findings.test.cjs skills/security-audit/validate-coverage-ledger.test.cjs
```

These tests validate the bundled report and coverage contracts. Passing them
does not establish that an arbitrary target repository has been audited or is
free of vulnerabilities.
