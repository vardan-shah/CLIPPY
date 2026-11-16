---
name: ponytail-review
description: >
  Reviews a change for correctness, security, scale, missing tests, speed and
  unnecessary complexity. Reads connected code and callers, not only the diff.
  Use when asked for a code review, PR review, last-commit review, or to assess
  whether a change is over-engineered. Reports findings; does not change code.
---

# Ponytail review

Review the requested change like the senior developer who will be paged when it breaks.
Order of importance: correct, safe, handles expected load, tested, fast, lean.

## Understand first

- Review the named uncommitted changes, branch, commit, PR or files. If none
  are named, inspect uncommitted changes, or the last commit if there are none.
- Read the diff and the code it touches: callers, called functions, tests and docs.
- Trace the flow from input through storage and processing to output.
- When a signature, return value or behavior changes, inspect every caller.
- Use CLIPPY's documented deployment and execution model when judging scale.

## Look for

1. **Bugs:** wrong results, crashes, edge cases, broken callers, inconsistent rules.
2. **Risks:** injection, secrets, weak randomness, missing validation or
   authorization, swallowed errors, unsafe write ordering and data loss.
3. **Scale:** races, duplicated work, unbounded memory, N+1 queries, quadratic
   work on large inputs, or process-local state that should be shared.
4. **Missing tests:** risky new logic without a focused test that would fail
   when it breaks.
5. **Performance:** substantial regressions or repeated work in hot paths.
6. **Unnecessary complexity:** dead code, unused options, speculative features,
   duplicate helpers, wrappers with no purpose, dependencies replacing a few
   standard-library lines, or abstractions with one implementation.

## CLIPPY-specific review checks

- Identity and roles must come from the server-side session, not request data.
- Transcript/video-derived text remains untrusted and must pass existing safe
  prompt/output handling.
- Account isolation, permission checks, abuse limits, queue fairness and
  data ownership must remain intact.
- Error handling that prevents lost user data must not be removed.
- Do not describe code as AI-generated based on style or heuristics.

## Verify before reporting

- Every finding needs a concrete input or situation and a reproducible impact.
- Re-read the relevant code and confirm callers, reachability and evidence.
- Do not call code unused without searching the repository, tests, fixtures,
  configuration and dynamic/string references.
- A documented shortcut is not a finding unless actual expected usage exceeds
  its stated limit.
- Propose the smallest correct fix. No style-only opinions or vague worries.

## Output

Start with **What this change does:** in two or three sentences.

Group numbered findings by severity, skipping empty groups:
- **Must fix:** bugs, security, data loss or failures under expected load.
- **Should fix:** risky logic without tests, real slowness or unjustified complexity.
- **Nice to have:** minor performance or simplification opportunities.

Each finding must include:
- **What this is:** context in plain language.
- **Problem:** concrete case and impact.
- **Fix:** smallest viable remedy.
- **If we skip it:** practical consequence.

End with a clear ship/fix-first verdict and a **Not checked** line when relevant.
If no findings exist, say what was checked and that it looks good.

This skill reports findings only. Do not change code.