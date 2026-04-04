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

## Read the output template

Read `templates/tasks.md` in the deliberate install directory for
the format your task list should follow.

## Save the tasks

```
deliberate step tasks --campaign <campaign-dir> --content "$(cat your-tasks.md)"
```

This will verify that the plan exists before accepting the task list.

## Next step

Implement. Work through the task list top to bottom. Check off each
task as you complete it. If scope changes significantly during
implementation, check escalation:

```
deliberate check-escalation C --actual-files <N>
```
