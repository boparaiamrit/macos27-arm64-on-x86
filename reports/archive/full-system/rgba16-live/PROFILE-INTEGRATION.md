# RGBA16 profile integration

Implemented only three new production files plus the explicit two-line RGBA16 branch in the existing frame wrapper. The global wrapper default and all prior profiles remain unchanged. The new rendering-only launcher selects `fresh-01`, cleanup4 readiness, the RGBA16 artifact and existing frame/shader/log/MTTCG/resource/guard paths. Its 900/800 limits are upper bounds and defaults. It defaults to 8 guest CPUs, 12 container CPUs/12GiB, TB1024, LP128/two threads and Mesa26. Transfer/final-capture switches retain their existing explicit semantics. No mouse or keyboard controller is included.

## Verification

- Meaningful dispatch RED: before the new branch, explicit `m27-pages-rgba16` selected the old crypto artifact and failed the exact expected path/hash assertion. `profile-red-behavior.log` retains this. Initial `profile-red.log` is a disclosed test-harness path-comparison error, not the behavior RED.
- **13 new Linux CPU tests passed**: 4 profile/identity-plan cases and 9 synthetic migration cases. Actual old-byte backup, changed-field-only, wrong identity/dict/artifact/previous build, concurrent AUX/identity changes, fatal directory-sync failure without rollback and real directory fsync on an owned synthetic directory are covered. `linux-python-green.log`.
- **5 existing IO/RGB10 profile tests passed**. `prior-profile-green.log`.
- **9 affected existing frame/MTTCG tests passed** under Ubuntu Python3.12 with synthetic Unix QMP servers. `frames-regression-green.log`. Existing fake-server unclosed-socket warnings and a background BrokenPipe from the intentional deadline case are retained; no test method failed. No unrelated test-harness fix was made.
- **7 mocked PowerShell launcher cases passed**, including exact defaults/resources/flags/paths, mocked CheckOnly forwarding and mocked no-CheckOnly form, whole-CONTROL conflict, invalid profile/readiness and excessive deadlines. No Docker executable or parent metadata writer was called. `launcher-green.log`.
- All new Python files parse; PowerShell parser passed. The existing wrapper with only the new two-line branch removed reproduces its exact parent-before SHA256. `profile-source-sha256.json` and `wrapper-dispatch.patch` identify the final bytes.

The initial Windows transaction run found that fsync on a read-only file descriptor fails there. The new owned migration tool now opens its own temporary file as r+b for fsync; bytes remain untouched. `migration-windows-readonly-fsync-error.log` preserves the failure. The 12 Windows cases then passed; Linux's final 13 cases include actual directory fsync. These repeat checks are not counted as distinct tests above.

No Docker mutation, build, GPU, live CheckOnly, actual identity migration, VM or guest input was executed. Only synthetic temporary directories changed during migration tests. Parent-created `parent-before.json`, `parent-preserve.py` and qualification review were preserved. No existing core, prior profiles, source pins or old admissions were edited. No commits or staging. Codebase-memory graph/index/coverage tools were unavailable per parent; exact named-source fallback was used with no graph-coverage claim.

See `MIGRATION.md` for the parent-only command and mounts. Guest acceptance and rendering/desktop effect remain unverified.
