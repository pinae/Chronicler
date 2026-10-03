---
name: usage-docs
description: Write or update user documentation in docs/usage/ so that it doubles as the specification for AI-driven browser testing. Use after implementing any user-facing behavior, and when writing or updating e2e tests.
---

# Writing usage documentation

Each file in `docs/usage/` describes one feature or workflow for a human user,
and is precise enough that an AI agent with a browser can verify it step by step.

## File structure

```markdown
# <Feature name>

<One or two sentences: what the user can do and why.>

## Before you start
<Preconditions: logged in as which kind of user, what data must exist.>

## <Scenario name, e.g. "Create a project">
1. Go to **<page / URL path>**.
2. Click the **<exact visible button or link text>** button.
3. Enter `<example value>` in the **<exact field label>** field.
4. Click **<button text>**.

**Result:** <What the user sees: exact messages, where the item appears,
what changes on the page.>

## <Error or edge case scenario>
...
```

## Rules
- Use the exact visible text of buttons, links, labels and messages, in bold.
  These must match the UI; if you change UI text, update the docs in the same commit.
- Use concrete example values, not placeholders.
- Every scenario ends with a **Result** that is observable in the browser.
- Cover the main path plus the important error cases (invalid input,
  missing permission, empty states).
- Write for a human first: plain language, no implementation details.
- Each scenario maps to one e2e test; name the test after the scenario so the
  link is obvious.

## Browser testing from the docs
When asked to browser-test a feature, read its usage file and execute each
scenario literally. Report each scenario as passed or failed, and for failures
state whether the app or the documentation is wrong.
