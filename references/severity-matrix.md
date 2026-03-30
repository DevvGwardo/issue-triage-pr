# Severity Scoring Reference

## Dimension 1: Impact (1-5)

How badly does this bug affect users?

| Score | Criteria | Examples |
|-------|----------|---------|
| 5 | Crash, data loss, security vulnerability, blocks core feature | `FileNotFoundError`, `KeyError` crash, SQL injection, auth bypass |
| 4 | Significant functionality broken, workaround exists but painful | Feature returns wrong results, timeout on common operation |
| 3 | Moderate impact on common workflow | Incorrect display, wrong default value, confusing error message |
| 2 | Minor impact, easy workaround | Cosmetic issue with workaround, edge case failure |
| 1 | Cosmetic, typo, documentation-only | Spelling error, alignment issue, stale comment |

### High-Impact Keywords

```
crash, segfault, panic, fatal, data loss, corruption, security,
unauthorized, injection, permission denied, FileNotFoundError,
KeyError, TypeError, AttributeError, blocks, breaks, unusable,
regression, silent failure, drops, loses, truncates
```

### Low-Impact Keywords

```
cosmetic, typo, minor, nit, style, formatting, alignment,
documentation, comment, spelling, wording, visual, display-only
```

---

## Dimension 2: Clarity (1-5)

How well does the reporter describe the bug?

| Score | Criteria | What to Look For |
|-------|----------|-----------------|
| 5 | Full reproduction steps, error trace, root cause identified, proposed fix | Issue includes code patch or exact fix location |
| 4 | Clear reproduction steps, error trace, affected component identified | Traceback with file/line, but no proposed fix |
| 3 | Partial reproduction steps, some error info | Description of what happens but missing exact steps |
| 2 | Vague description, no reproduction steps | "It doesn't work" with some context |
| 1 | No useful information, can't understand the bug | One-line complaint, no details |

### Clarity Signals

**High clarity (+):**
- Includes traceback/stack trace
- Lists exact steps to reproduce
- Specifies environment (OS, version, Python version)
- Proposes a specific fix with code
- Identifies root cause file and line

**Low clarity (-):**
- "I don't know how to reproduce"
- No error message
- Vague expected/actual behavior
- Missing environment details

---

## Dimension 3: Fix Scope (1-5)

How contained and feasible is the fix?

| Score | Criteria | Examples |
|-------|----------|---------|
| 5 | 1 file, <20 lines, obvious change | Add a null check, fix a typo in code, add missing import |
| 4 | 1-2 files, <50 lines, clear change | Add platform guard, register missing handler |
| 3 | 2-3 files, moderate complexity | Refactor function, add error handling path |
| 2 | 3-5 files, requires understanding architecture | Change data flow, modify API contract |
| 1 | 5+ files, architecture change, or new feature needed | Redesign scheduler, add new platform support |

### Scope Signals

**Small scope (+):**
- Issue includes exact file and line number
- Proposed fix is a few lines of code
- Similar pattern exists elsewhere in codebase (copy-adapt)
- Issue is about missing registration/configuration

**Large scope (-):**
- Issue describes a design flaw
- Fix requires changing public APIs
- Multiple components need coordinated changes
- Issue mentions "refactor" or "redesign"

---

## Dimension 4: Strategic Value (1-5)

How well does fixing this align with the project's priorities and community?

| Score | Criteria | Signals |
|-------|----------|---------|
| 5 | Core feature, many users affected, aligns with top contributing priority | High reaction count, many comments, bug label, maintainer acknowledged |
| 4 | Important feature, significant user impact | Multiple users reporting, some reactions |
| 3 | Useful fix, moderate user base | A few reactions, relevant to common use case |
| 2 | Niche use case, few users affected | Specific platform/configuration edge case |
| 1 | Extremely niche, questionable value | One user, unusual setup, workaround is trivial |

### Strategic Signals

**High value (+):**
- Issue has `bug` label (maintainer-confirmed)
- Multiple users have reacted (thumbs up, +1)
- Maintainer has commented or assigned
- Aligns with CONTRIBUTING.md stated priorities (e.g., "cross-platform compatibility")
- Affects the default/recommended installation path

**Low value (-):**
- No labels, no reactions
- Very specific to one user's unusual setup
- Author hasn't responded to clarification requests
- Issue has been deprioritized by maintainers

---

## Combined Scoring

| Total (out of 20) | Category | Action |
|--------------------|----------|--------|
| 16-20 | FIX NOW | Proceed immediately — high confidence fix |
| 12-15 | GOOD CANDIDATE | Strong option — may need some investigation |
| 8-11 | INVESTIGATE FIRST | Promising but unclear — gather more info before committing |
| 4-7 | SKIP | Low impact or unclear scope — better candidates exist |
| 1-3 | SKIP | Not worth the effort at this time |
| N/A | BLOCKED | Competing PR exists — do not duplicate work |

---

## Tie-Breaking Rules

When two issues have the same total score:

1. **Prefer higher Impact** — fixing crashes over cosmetic issues
2. **Prefer higher Clarity** — clear issues get fixed faster and more correctly
3. **Prefer higher Strategic Value** — maintainers are more likely to merge
4. **Prefer newer issues** — less likely someone else is already working on it
