# Contributing

Repo Chronicle stays small on purpose: a local-first CLI that turns Git
history into a commit-evidenced Markdown context pack for one proposed
change. It is not becoming an MCP server, a RAG/vector-search system, a code
graph, or a hosted service — see [ROADMAP.md](ROADMAP.md) for what's actually
planned versus explicitly out of scope.

## Local setup

```bash
git clone https://github.com/richardkuo2002/repo-chronicle.git
cd repo-chronicle
python3 -m venv .venv
.venv/bin/pip install -e .
```

Zero third-party runtime dependencies — keep it that way unless a fix
genuinely requires one, and say why in the PR.

## Running tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Tests must not depend on your global `git` author config, an existing local
repository, network access, your locale, or wall-clock time. If a test needs
a real repository, build one with
[`examples/create_fixture_repo.py`](examples/create_fixture_repo.py)'s
`fixture_repo()` context manager (fixed author/committer/timestamps, created
in a temp directory, cleaned up automatically) rather than committing a
static fixture or hardcoding SHAs.

Each core module also keeps a `_self_check()` you can run directly for a
fast manual sanity check (`python -m repo_chronicle.scanner`, `.db`,
`.explain`) — the test suite wraps these, so passing tests already covers
them.

## Fixture expectations

If you change `examples/create_fixture_repo.py`'s commit history, update
[`examples/walkthrough.md`](examples/walkthrough.md) and the README quick
start example to match — don't let the docs quote stale SHAs or subjects.
`tests/test_fixture_repo.py` asserts the fixture's shape (commit count,
subjects, order, reproducibility); update it alongside the generator.

## Output-format compatibility

The generated Markdown's structure (section order and headers) is something
people script around. If your change is a bug fix or a safety fix (like
character escaping) that only affects pathological input, normal-input
output should stay byte-for-byte identical — `tests/test_render.py` checks
this for the escaping helpers specifically; add to it rather than loosening
it. If your change *does* alter the structure for normal input, call that
out explicitly in the PR description and in `CHANGELOG.md` — don't let it
happen as a side effect.

Changes to the output format or to `explain`'s commit-matching logic need a
test that would fail without the change — a test-free doc update claiming
new behavior isn't enough.

## Contribution checklist

- [ ] `python -m unittest discover -s tests -v` passes
- [ ] `git diff --check` is clean (no trailing whitespace, no conflict markers)
- [ ] `python scripts/check_markdown_links.py` reports no broken local links
- [ ] New behavior has a test; changed output-format behavior is called out
      in the PR description and `CHANGELOG.md`
- [ ] No new third-party runtime dependency, unless justified in the PR
- [ ] No network calls, telemetry, or credentials added
- [ ] README/`examples/walkthrough.md` updated if a documented command's
      behavior changed
