# Step: Create a Brief (Class B)

You're starting a bounded task. A brief keeps you focused and lets you
track progress without heavyweight planning.

## How to approach this

1. **Understand the scope first.** Read relevant code or context before
   writing the checklist. A brief is only useful if the items are concrete.
2. **Break it into 3-8 items.** Fewer than 3 means it's probably Class A
   (just do it). More than 8 means it might be Class C (needs a spec).
3. **Each item should be independently verifiable.** "Fix the bug" is bad.
   "Add test reproducing the crash in parser.py" is good.
4. **Write the done criteria.** What's true when you're finished? Not
   "all items checked" — what observable outcome proves success?

If you can't write 3-8 concrete, independently verifiable items from
the description, stop. Either it's Class A (just do it) or Class C
(needs a spec). A brief with vague items is worse than no brief.

## Create the brief

Run:
```
deliberate brief "your task description" --items "item 1,item 2,item 3"
```

Or let deliberate auto-extract items from your description:
```
deliberate brief "your task description"
```

This creates `brief.md` in the current directory.

## Working the brief

- Mark items done as you go: `deliberate check B001`
- Check progress: `deliberate status`
- If scope grows beyond the checklist, consider escalating:
  `deliberate check-escalation B --scope-grew`

## Next step

Do the work. Follow the checklist. When all items are done, you're done.
