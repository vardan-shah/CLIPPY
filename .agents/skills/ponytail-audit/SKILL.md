---
name: ponytail-audit
description: >
  Audits the whole repository or a named area for bugs, security, expected-load
  failures, missing tests, slow paths and unnecessary complexity. Produces a
  prioritised report and makes no changes. Use for repository audits, finding
  bloat, or deciding what can safely be deleted.
---

# Ponytail audit

Audit the requested repository or area like the senior developer who inherits it.
Order of importance: correct, safe, handles expected load, tested, fast, lean.

## Map first

- Audit the named folder, package or repository. If none is named, audit the repo.
- Read the README, deployment/build configuration, dependency list, entry points,
  routes, handlers, jobs and tests.
- Establish expected load from deployment docs; state the load assumption.
- Trace important paths end to end: user input, data storage, background work,
  authorization and outputs.
- In a large repository, go deep where mistakes cost most. State what was not read.

## Look for

1. **Bugs:** incorrect results, crashes, missed edge cases and inconsistent behavior.
2. **Risks:** injection, secrets, weak randomness, missing user-input checks,
   missing authorization, swallowed errors, unsafe writes and data loss.
3. **Scale:** races, duplicated work, unbounded growth, N+1 queries,
   quadratic work and process-local state that must be shared.
4. **Missing tests:** risky branches, parsers, security checks or data writes
   without a focused regression test.
5. **Performance:** substantial slow paths and repeated work in hot paths.
6. **Unnecessary complexity:** dead code, unused options/configuration,
   speculative features, duplicate helpers, needless dependencies, one-use
   abstractions and wrappers that only forward calls.

## CLIPPY-specific checks

- Confirm identity and roles are derived from the server-side session.
- Confirm transcript/video-derived text is treated as untrusted.
- Check that prompt sanitization, output handling, account isolation, permission
  checks, abuse limits, queue fairness and user-data ownership remain intact.
- Never recommend removing error handling that protects user data.
- Do not infer AI authorship from code style.

## Verify before reporting

- Every finding must include a concrete case, reachability and impact.
- Before calling code unused, search the whole repo including tests, fixtures,
  configuration and dynamic/string references.
- Treat a documented shortcut as intentional unless actual expected load
  exceeds its stated limit.
- Recommend the smallest correct fix. Prefer safe deletion over adding layers.
- Do not modify code as part of the audit.

## Output

Start with **What this repo does:** in two or three sentences and state the
expected load assumed.

Prioritise numbered findings in:
- **Must fix:** bugs, security, data loss or failures under expected load.
- **Should fix:** risky code without tests, real slowness or unjustified complexity.
- **Nice to have:** minor performance or simplification opportunities.

Each finding includes:
- **What this is**
- **Problem** with a concrete example
- **Fix** with the smallest remedy
- **If we skip it** practical consequence

Report at most 20 findings and state if more were left out. End with a
clear verdict and **Not checked** details for areas not inspected or tests
not run. If no findings exist, state what was checked and that the repo
looks healthy.

This skill reports findings only. Do not change code.