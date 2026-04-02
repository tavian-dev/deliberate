# Tasks: ${title}

**Plan**: [plan.md](plan.md) | **Date**: ${date}

## Format
`- [ ] [ID] [P?] Description with file path`
- **[P]**: parallelizable (different files, no dependencies)
- IDs: T001, T002, ... in execution order

## Phase 1: Setup
- [ ] T001 [description with file path]

## Phase 2: Core Implementation
Write tests first, then implement.
- [ ] T002 [P] Write tests for [component] in tests/test_[name].py
- [ ] T003 Implement [component] in src/[path].py

## Phase 3: Integration
- [ ] T004 Wire components together in [file]
- [ ] T005 Verify end-to-end: [how to test]

## Phase 4: Polish
- [ ] T006 [P] Update documentation
- [ ] T007 Run full test suite, fix gaps

## Dependencies
- Phase 2 depends on Phase 1
- Phase 3 depends on Phase 2
- Tasks marked [P] can run in parallel

## Done When
- [ ] All tasks checked off
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changes committed and pushed
