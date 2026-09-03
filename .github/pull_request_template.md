## What this changes

<!-- One or two sentences. -->

## Why

<!-- What problem does this solve, or what did the inspection/report find? -->

## Output-format compatibility

- [ ] Normal-input CLI/Markdown output is byte-for-byte unchanged
- [ ] Output changes, and I've called out exactly what changes and why below
- [ ] N/A (docs/tests/CI only)

## Checklist

- [ ] `python -m unittest discover -s tests -v` passes
- [ ] `git diff --check` is clean
- [ ] New/changed behavior has a test that would fail without this change
- [ ] No new third-party runtime dependency (or: justified below)
- [ ] No network calls, telemetry, or credentials added
- [ ] `CHANGELOG.md` updated under `## Unreleased`
- [ ] README / `examples/walkthrough.md` updated if a documented command's behavior changed

## Notes for reviewers

<!-- Anything that needs manual verification, e.g. worktree/subdirectory behavior. -->
