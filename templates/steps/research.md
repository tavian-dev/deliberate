# Step: Research (Class D)

You're working on something unfamiliar or uncertain. Before writing a
spec, you need to resolve unknowns that would block planning.

## How to approach this

1. **List what you don't know.** Be specific. "I don't understand the
   codebase" is too vague. "I don't know how auth tokens are stored
   or which module handles refresh" is actionable.
2. **Timebox the research.** Set a limit (e.g., 30 minutes, 2 hours).
   Research expands to fill available time. When the timebox expires,
   write up what you found — even if incomplete.
3. **Record findings with sources.** Future you needs to know where
   information came from and how confident you are in it. "I think
   it uses JWT" is less useful than "auth.py line 45 creates a JWT
   with HS256, confirmed by reading the code."
4. **Make decisions from findings.** Research that doesn't lead to
   decisions is just reading. For each unknown resolved, state what
   you decided and why.
5. **Name what's still unknown.** Unresolved unknowns become risks in
   the plan. Don't pretend you know more than you do.

## When is research done?

Research is complete when every question from step 1 is either answered
or explicitly deferred with a reason. If a question is still open and
is on the critical path for the spec, that is a blocker — do not
proceed to `spec` until it is resolved or accepted as a known risk.

## Write the research document

The output format is in `templates/research.md` (the *template*). This
file is the *step guide*.

Draft your research, then submit:
```
deliberate step research --campaign <campaign-dir> --content "$(cat your-research.md)"
```

## Do not proceed unless

- Every question from step 1 is answered or deferred with a reason
- Critical-path unknowns are resolved (not just acknowledged)
- A clear recommendation exists: proceed, pivot, or abandon

## Next step

Write the spec. Read the step guide first:
`templates/steps/spec.md`

Then run:
`deliberate step spec --campaign <campaign-dir> --content "..."`
