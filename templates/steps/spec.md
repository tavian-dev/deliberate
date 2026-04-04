# Step: Write a Spec (Campaign)

You're at the first step of a campaign. The spec defines *what* you're
building and *why*, without prescribing *how*.

## How to approach this

1. **Start with the problem, not the solution.** What's broken or missing
   today? Who does it affect? If you can't articulate the problem clearly,
   you're not ready to spec — consider a research step first.
2. **Write user stories before requirements.** Stories ground the spec in
   real usage. Requirements without stories tend to drift into
   over-engineering.
3. **Be explicit about what's out of scope.** The biggest risk in a
   campaign is scope creep. Name the things you're deliberately not doing.
4. **Every requirement must be testable.** If you can't describe how to
   verify it, it's not a requirement — it's a wish.
5. **List edge cases and assumptions.** These are where bugs hide. Forcing
   yourself to enumerate them now saves debugging later.

## Before moving on

Re-read your spec and check:
- Does every requirement have a clear acceptance test?
- Are out-of-scope items explicitly named?
- Do success criteria include something measurable?
- If you have 2+ open assumptions or unresolved questions, resolve
  them before writing the plan. Ambiguities in the spec become
  unfixable constraints downstream.

If any of these fail, revise the spec before proceeding.

## Read the output template

Read `templates/spec.md` in the deliberate install directory. It shows
the format your spec should follow. Fill it in for your specific task.

## Save the spec

```
deliberate step spec --campaign <campaign-dir> --content "$(cat your-spec.md)"
```

Or pipe it:
```
cat your-spec.md | deliberate step spec --campaign <campaign-dir>
```

## Next step

Write the plan: `deliberate step plan --campaign <campaign-dir>`

Before writing the plan, read `templates/steps/plan.md` for guidance.
