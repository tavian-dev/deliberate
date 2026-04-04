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

## Read the output template

Read `templates/plan.md` in the deliberate install directory for the
format your plan should follow.

## Save the plan

```
deliberate step plan --campaign <campaign-dir> --content "$(cat your-plan.md)"
```

This will verify that the spec exists before accepting the plan.

## Next step

Break the plan into tasks: `deliberate step tasks --campaign <campaign-dir>`

Before writing tasks, read `templates/steps/tasks.md` for guidance.
