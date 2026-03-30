# Issue Triage Report — {{REPO}}

**Date:** {{DATE}}
**Issues Analyzed:** {{COUNT}}
**Filter:** {{FILTER}}

---

## Summary

- **Total issues scanned:** {{COUNT}}
- **FIX NOW:** {{FIX_NOW_COUNT}}
- **GOOD CANDIDATE:** {{GOOD_COUNT}}
- **INVESTIGATE FIRST:** {{INVESTIGATE_COUNT}}
- **SKIP:** {{SKIP_COUNT}}
- **BLOCKED:** {{BLOCKED_COUNT}}

## Top Recommendation

**Issue #{{TOP_NUM}}** — {{TOP_TITLE}}

- **Score:** {{TOP_SCORE}}/20
- **Root cause:** {{ROOT_CAUSE_SUMMARY}}
- **Estimated fix scope:** {{FIX_SCOPE}}
- **Contributing priority alignment:** {{PRIORITY_ALIGNMENT}}

---

## Full Rankings

| Rank | Issue | Title | Impact | Clarity | Scope | Strategic | Total | Status |
|------|-------|-------|--------|---------|-------|-----------|-------|--------|
{{ROWS}}

---

## Detailed Analysis — Top 5

### #{{ISSUE_1_NUM}}: {{ISSUE_1_TITLE}}

**Score:** {{SCORE}}/20 | **Recommendation:** {{REC}}

- **Impact ({{IMPACT}}/5):** {{IMPACT_REASON}}
- **Clarity ({{CLARITY}}/5):** {{CLARITY_REASON}}
- **Fix Scope ({{SCOPE}}/5):** {{SCOPE_REASON}}
- **Strategic Value ({{STRATEGIC}}/5):** {{STRATEGIC_REASON}}
- **Competing PRs:** {{COMPETING}}
- **Key files:** {{FILES}}

---

## Notes

- Issues marked BLOCKED have an existing open PR targeting them
- Scores are heuristic — always read the full issue before committing to a fix
- Strategic value considers the repo's stated contributing priorities
