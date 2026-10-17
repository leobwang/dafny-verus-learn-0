---
name: review
description: "Spaced-repetition review session over the dafny-verus-learn-0 error ledger (Leitner scheduling, fresh predict-then-verify variants), shared by the Q and R tracks. Invoked as /review, typically when the session banner shows due items."
disable-model-invocation: true
---

Read `.claude/skills/instructor/CORE.md` first and operate under it: you are the INSTRUCTOR running spaced repetition.

# /review — Leitner review from the error ledger

## Session check — before anything else

`/review` is coach-side. Refuse in one line if this session shows any examiner (`/viva`, `/grade-paper`, `/review-code`) or contractor (`/contract`) activity (CORE.md §Session check).

## The scheduling model

`instructor/ledger.md` is the single source of truth. Each line is one item (CORE.md schema) with a Leitner **box** and a **due** date:

| box | interval until next due |
|-----|------------------------|
| 1   | 1 day  |
| 2   | 3 days |
| 3   | 7 days |
| 4   | 21 days |
| 5   | 60 days |

An item is **due** when `due:` ≤ today. The SessionStart hook (`.claude/hooks/review-due.sh`) banners the due count; this skill runs the session.

## One queue, both tracks

The ledger mixes tracks: a line's tag is `<ID>/<vocab-tag>`, where `<ID>` is a Q id (`Q04/loop-invariant`) or an R id (`R06/loop-invariant`). Accept both. A prefix that does not resolve (`python3 scripts/check_course_map.py --resolve <prefix>` exits 3) marks a corrupt line: report it once and skip it.

`/review` takes no module id, so there is no up-front Step 0; but before a probe that needs course code, resolve that item's module and run `scripts/vcheck --module <ID>` (CORE.md Step 0). A variant never draws on a given layer above that module's `layer`, and never on another track's material.

## Procedure

1. Read `instructor/ledger.md`; collect the items with `due:` ≤ today.
2. If there are none, say so and stop.
3. Select at most **6**, prioritized by (a) most overdue first, (b) higher `hint-depth:` first (leaning on the tutor buys future review load: say this once if it changes the selection); then **interleave**: never two consecutive items with the same module or the same canonical tag. The module is the tag's prefix; the tag is the part after the slash, compared across tracks as a canonical tag, with aliases resolved through `.claude/skills/instructor/concepts.md` (`Q04/loop-invariant` and `R06/loop-invariant` count as the same tag).
4. For each item, **generate a FRESH variant** from the recorded concept–error pair. The ledger stores the error, not the original question, so verbatim re-asking is impossible: build a new small exercise or question that a learner still carrying that error would get wrong and a learner who has fixed it would get right. Keep variants small (≤5 minutes each) and on toy terms, never a course exercise statement. Prefer **predict-then-verify** where the error is formal: the learner commits a prediction, then you run the probe through `scripts/vcheck` (CORE.md dispute recipe) and paste the output verbatim. Pick variants whose referee is decisive under the asymmetry rule: a value checked by execution, or a verified/not-verified question about toy code at the pinned limits; ask for "inconclusive" only when that is the concept under review.
5. One item per message. Classify the answer (CORE.md §Answer classification); on a misconception give the mechanism, never the corrected answer (the anti-spoiler contract binds here too).
6. Update the ledger line of every reviewed item, same schema:
   - **Answered well** → box + 1 (max 5), `due:` = today + the new box's interval, `seen:` = today.
   - **Answered poorly** → box = 1, `due:` = tomorrow, `seen:` = today; refine the `error:` text if the session revealed a sharper description.
   - An item answered well at box 5 may be dropped (delete the line): graduated. Exception: a `source: tutor` line of a `solo` module stays (at box 5) until that module's `defense` gradebook row exists, because the defense reads its `hint-depth:` to mark the row `assisted`.
7. Close with a one-line summary: items reviewed, promoted, demoted and graduated, and the next due date.

Never add NEW items here unless the review itself surfaced a genuinely new concept–error pair (then: box 1, `source: review`, `hint-depth: 0`). `/review` never writes the gradebook.
