# instructor/ — your instructor state

This directory belongs to you, the learner: commit it on your branch (`leobwang-*`). The instructor skills read and write it, two course scripts write rows of their own, and a `/contract` session never touches it. The formats are defined in `.claude/skills/instructor/CORE.md` §State files, which is authoritative; this README is a map.

| path | what it holds | written by |
|---|---|---|
| `ledger.md` | your error patterns, one line each, plus the Leitner review queue (boxes and due dates) | `/tutor`, `/discuss`, `/viva`, `/grade-paper`, `/review-code` append; `/review` reschedules |
| `gradebook.md` | one row per graded artifact, both tracks | `/grade-paper`, `/review-code`, `/viva`; `scripts/firsttry.sh --record` (`calib` rows) and `scripts/challenge_gate.sh` (`challenge` rows) only |
| `calib/<ID>.tsv` | first-try records of predictions and exit scores, append-only | `scripts/firsttry.sh` only |
| `feedback/<ID>_paper.md`, `feedback/<ID>_code.md` | full grading reports, with margin notes ready to paste | `/grade-paper`, `/review-code` |
| `records/` | viva, defense and discussion logs, your key formulations quoted | `/viva`, `/discuss` |
| `scratch/` | verifier probes; gitignored, never committed | the instructor skills |

- The ledger stores the **error**, never the question, so `/review` can build fresh variants.
- The tutor and `/discuss` never write the gradebook; graders read it first and escalate repeat findings.
- The SessionStart banner counts ledger lines whose `due:` date is today or earlier; run `/review` when it shows.
- Every grade here is advisory: a verifier check outranks it, and you may dispute any finding by its rubric line.
