# Step: Write a Plan (Campaign)

You have a spec. Now decide *how* to build it. The plan turns
requirements into technical decisions and a phased approach.

## How to approach this

1. **Read the spec again.** Not skimming — actually read it. The plan
   must address every requirement and user story in the spec.
2. **Make technical decisions explicitly.** For each non-obvious choice,
   document what you chose, why, and what you rejected. Future you (or
   another agent) needs to understand the reasoning.
3. **Break work into phases with end conditions.** Each phase should be
   independently verifiable. "Phase 1 is done when tests pass" is good.
   "Phase 1 is done when the code looks right" is not.
4. **Identify files you'll touch.** List them. This grounds the plan in
   the actual codebase and catches scope surprises early.
5. **Name the risks.** What could go wrong? What are you unsure about?
   Each risk should have a mitigation or at least an acknowledgment.
6. **Verify coverage.** For each requirement in the spec, find the
   phase or decision in the plan that addresses it. If any requirement
   has no corresponding plan entry, add it or explicitly defer it with
   a reason.

## Write the plan

The output format is in `templates/plan.md` (the *template*). This
file is the *step guide* — how to approach producing it.

Draft your plan, then submit:
```
deliberate step plan --campaign <campaign-dir> --content "$(cat your-plan.md)"
```

The tool verifies the spec exists before accepting the plan.

## Do not proceed unless

- Every spec requirement maps to a phase or decision in the plan
- Each phase has a concrete end condition
- Risks are named with mitigations

## Next step

Break the plan into tasks. Read the step guide first:
`templates/steps/tasks.md`

Then run:
`deliberate step tasks --campaign <campaign-dir> --content "..."`
