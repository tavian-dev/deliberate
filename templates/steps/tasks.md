# Step: Write Tasks (Campaign)

You have a spec and a plan. Now break the plan into concrete,
ordered tasks that can be executed one at a time.

## How to approach this

1. **One task = one verifiable change.** Each task should result in
   something you can test or review independently. "Implement the
   feature" is too big. "Add the endpoint handler in api/routes.py"
   is right.
2. **Include file paths.** Every task should name the file(s) it
   touches. This prevents surprises and makes tasks assignable to
   parallel agents.
3. **Write tests before implementation tasks.** List the test task
   first, then the implementation. This forces you to think about
   what "done" looks like before writing code.
4. **Mark parallelizable tasks with [P].** Tasks that touch different
   files with no dependencies can run concurrently. This matters if
   you're dispatching to multiple agents.
5. **Order matters.** Tasks are executed top to bottom. Dependencies
   should be obvious from the ordering. If task T005 depends on T003,
   T003 must come first.
6. **Identify MVP scope.** After ordering tasks, find the minimal
   subset that delivers the first working slice. Label those tasks
   as MVP. Implement them first before tackling the rest.

## Validate before saving

Re-read the task list. Confirm every task has a file path, an ID,
and is independently verifiable. Any task that says "implement X"
without naming a specific file or function is not concrete enough.

## Write the tasks

The output format is in `templates/tasks.md` (the *template*). This
file is the *step guide*.

Task IDs are author-assigned: `T001`, `T002`, etc. in execution order.
Mark parallelizable tasks with `[P]` after the ID. Label MVP-scope
tasks with `[MVP]`.

Draft your task list, then submit:
```
deliberate step tasks --campaign <campaign-dir> --content "$(cat your-tasks.md)"
```

The tool verifies the plan exists before accepting.

## Do not proceed unless

- Every task names specific file(s) it touches
- Tasks are ordered so dependencies come first
- MVP scope is identified

## Next step

Implement. Work through the task list top to bottom. If scope changes
significantly during implementation:

```
deliberate check-escalation C --actual-files <N>
```
