Fix the following issue. Before writing any code, create a brief plan:

1. Run: `deliberate brief "${description}"` to create a checklist
2. Read the generated brief.md
3. Follow the checklist items in order
4. Mark each item done as you complete it: `deliberate check B001`, etc.
5. After all items are done, run the test command to verify

Issue: ${description}

Repository: ${repo}
Test command: ${test_command}
${setup_instructions}
After making your changes, run the test command to verify your fix works.
