---
name: ponytail
description: >
  Minimal, correct implementation guidance for coding tasks. Prefer the
  smallest complete solution, reuse existing code, avoid speculative
  abstractions and dependencies, and preserve correctness and security.
  Use for coding, debugging, refactoring, dependency choices, and requests
  to reduce over-engineering or AI-generated code bloat.
---

# Ponytail

Use lazy senior-developer judgment: the best code is often the code not written.
Solve the task with the least new code that fully works.

## Before changing code

Read the task and the code it touches. Inspect callers, tests, fixtures,
configuration and exports that the change may affect. Consider what could
break for users, including data they rely on or information they must not
be able to access. Extra features are not part of the scope.

## Prefer the smallest complete solution

1. Skip features, options and flexibility nobody asked for.
2. Reuse existing helpers, components, services and project conventions.
3. Prefer standard-library or platform functionality over new dependencies.
4. Do not add abstractions, wrappers, conversions, configuration or boilerplate
   without a concrete need.
5. Prefer clear code over clever compression. The shortest working diff wins
   only when correctness and readability are preserved.
6. Fix root causes in shared code after checking all callers.
7. Complete every affected caller, test and fixture.
8. Add a focused test for non-trivial new logic, especially branches, loops,
   parsing, money, security or data writes.
9. Document a known shortcut with a comment in this form:
   `shortcut: <the limit>, <when to upgrade>`.

## Never remove

Do not remove trust-boundary validation, authorization, security controls,
meaningful error handling, data-loss safeguards, accessibility, required
functionality or tests merely to reduce line count.

Do not infer that code is AI-generated from its style. Remove code only when
its redundancy or lack of purpose is established and its behavior is understood.
Do not apply speculative cleanups automatically.

## CLIPPY-specific constraints

- Preserve the existing session-derived identity and authorization model.
  Never trust a user ID or role supplied in a request body.
- Treat transcript and video-derived text as untrusted input. Preserve the
  project's prompt sanitization and output-text handling.
- Preserve validation, abuse limits, queue fairness, account isolation and
  data ownership.
- Keep secrets, tokens, real addresses and personal paths out of tracked files.
- Follow the existing Python, FastAPI, plain HTML/CSS/JavaScript and test
  conventions. Do not introduce a build system or dependency without need.
- For changes affecting `studio/`, run `python tests/run.py`.

## Finish

Report what changed, what was deliberately not added, checks actually run,
and any remaining risk. Be explicit about checks not run.