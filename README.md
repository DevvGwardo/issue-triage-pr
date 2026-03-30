# issue-triage-pr

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) skill that automates the full GitHub issue triage-to-pull-request pipeline.

## What It Does

Six-phase autonomous workflow:

1. **FETCH** — Pull open issues from any GitHub repository
2. **TRIAGE** — Score and rank issues by Impact, Clarity, Fix Scope, and Strategic Value (1-5 each)
3. **INVESTIGATE** — Read contributing guidelines, trace the bug, formulate root cause hypothesis
4. **FIX** — Create branch, apply minimal correct fix, run tests, commit
5. **PR** — Open pull request following the repo's conventions, monitor CI
6. **FOLLOW-UP** — Comment on the issue, link the PR, report summary

## Installation

### Via Hermes Skills Hub

```bash
hermes skills install issue-triage-pr
```

### Manual

```bash
cp -R . ~/.hermes/skills/github/issue-triage-pr/
```

## Usage

Once installed, Hermes will automatically load the skill when you ask it to triage issues or fix bugs. Examples:

```
> Triage the latest 20 issues on NousResearch/hermes-agent and find a bug to fix
> Pick an important bug from owner/repo and open a PR for it
> Score the open issues on my-org/my-project by severity
```

### Standalone Scripts

The skill includes two standalone scripts that can be used independently:

#### Triage Issues

```bash
python3 scripts/triage_issues.py --repo NousResearch/hermes-agent --limit 20
python3 scripts/triage_issues.py --repo owner/repo --label bug --output report.md
```

Outputs a scored and ranked markdown table:

```
| # | Title | Impact | Clarity | Scope | Strategic | Total | Category |
|---|-------|--------|---------|-------|-----------|-------|----------|
| #123 | Crash on startup... | 5 | 4 | 4 | 3 | 16 | FIX NOW |
| #456 | Wrong color in... | 2 | 3 | 5 | 2 | 12 | GOOD CANDIDATE |
```

Categories: **FIX NOW** (16-20), **GOOD CANDIDATE** (12-15), **INVESTIGATE FIRST** (8-11), **SKIP** (1-7), **BLOCKED** (competing PR exists)

#### Extract Repo Conventions

```bash
python3 scripts/extract_conventions.py --repo-dir /path/to/cloned/repo
```

Auto-detects:
- Branch naming convention
- Commit message format (Conventional Commits, Angular, etc.)
- Test command (`pytest`, `npm test`, `cargo test`, etc.)
- Lint command
- PR template sections
- CI workflow names
- CLA/DCO requirements

## Structure

```
issue-triage-pr/
├── SKILL.md                    # Main skill instructions (Hermes loads this)
├── scripts/
│   ├── triage_issues.py        # Automated issue scoring engine
│   └── extract_conventions.py  # Repo convention extractor
├── templates/
│   ├── triage-report.md        # Markdown triage report template
│   └── pr-body-issue-fix.md    # PR body template
└── references/
    ├── severity-matrix.md      # 4-dimension scoring reference
    └── workflow-checklist.md   # Full pipeline checklist
```

## Requirements

- Python 3.11+
- [GitHub CLI (`gh`)](https://cli.github.com/) — authenticated
- Git

No external Python dependencies (stdlib only).

## Severity Scoring

Each issue is scored on four dimensions (1-5, max 20 total):

| Dimension | What It Measures |
|-----------|-----------------|
| **Impact** | How badly the bug affects users (crash > cosmetic) |
| **Clarity** | How well the reporter described the problem (repro steps, traces, proposed fix) |
| **Fix Scope** | How contained the fix is (1 file > architecture change) |
| **Strategic Value** | Alignment with project priorities, community interest (labels, reactions) |

See [`references/severity-matrix.md`](references/severity-matrix.md) for the full scoring rubric.

## Related Skills

- [github-issues](https://github.com/NousResearch/hermes-agent/tree/main/skills/github/github-issues) — Issue CRUD operations
- [github-pr-workflow](https://github.com/NousResearch/hermes-agent/tree/main/skills/github/github-pr-workflow) — PR lifecycle management
- [systematic-debugging](https://github.com/NousResearch/hermes-agent/tree/main/skills/software-development/systematic-debugging) — Structured root cause analysis

## License

MIT
