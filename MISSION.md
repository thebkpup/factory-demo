# Mission

<!--
  Owner: humans only. This file is on the protected list; the factory cannot edit it.
  Written from ZCode on install day; edit it as the product's intent changes.
-->

**Derived from:** the demo brief for the AI software factory (this repository).
**Last reconciled with it:** 2026-10-18

## What the task service is

A single-user task list behind a small JSON HTTP API. Someone keeps a list of open
tasks, finishes them one at a time, and the list they reload always reflects what they
did — including after a restart. That persistence-through-restarts property is the
whole point of the product; everything else exists to serve it.

Single tenant, single deployment, one SQLite file of state. Those are invariants, not
assumptions to be revisited.

## Who it is for

- One person tracking their own work items, from scripts or curl.

The task service is not a team collaboration tool and not a project manager.

## Core capabilities (in scope)

**Tasks**
- create, list, complete, rename and delete tasks
- an open count that always agrees with the list
- state that survives a process restart

## Out of scope -- the factory must never build this

**Collaboration**
- multiple users, sharing, assignments, or mentions
- comments, activity feeds, or notifications

**Product surface**
- a web UI, theming, or any browser-rendered interface
- due dates, priorities, tags, or recurring tasks
- search, filtering, or sorting beyond listing in creation order

**Platform**
- accounts, authentication, or API keys
- sync, import/export, or a mobile client
- multi-database backends or configuration profiles

## Hard invariants -- not tunable by any issue

1. **State survives a restart.** An acknowledged write is a persisted write; nothing
   ships if a restart can lose or resurrect tasks.
2. **The API stays JSON over HTTP with /health and /identity.** The runtime
   verification contract depends on them.
3. **The factory cannot modify governance files.** `MISSION.md`, `FACTORY_RULES.md`
   and the conventions file are the constitution; a PR touching them is a reject.
4. **The factory cannot modify its own judge.** `harness/` and `.factory/holdout/`
   define what "working" means; loosening an assertion is a human decision.

## Allowed evolutions

- Refactoring `app.py` freely as long as behavior and the gate stay green.
- Adding tests anywhere, any time.

## Definition of done

**Gate 1 -- static checks and tests pass.** `python harness/ci.py` (py_compile +
unittest suite, currently 5 tests).

**Gate 2 -- the API stays honest.** Error cases return 4xx with JSON, never a crash,
and the open count always equals the number of not-done tasks.

**Gate 3 -- the end-to-end path passes as a real user.** The journeys in
`harness/END-TO-END.md` (create a task, see it listed, finish it, reload, restart).

## Open questions -- decisions nobody has made yet

- **Q1** Should completed tasks be archived (hidden by default) rather than deleted
  by the client? The factory may propose an answer and hold the merge for a human.

**Except these, which do stop the factory:**

- Anything touching data deletion or migration of the SQLite schema: hold for a human.

## Decisions

- 2026-10-18 **Storage engine?** SQLite, single file, no ORM.

## What the factory does NOT own -- permanently human

- Does the API feel right to use -- naming, shape, error wording.
- Whether this demo should grow into a real product at all.
