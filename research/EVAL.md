# EVAL.md — how I run and report an evaluation

Learner-owned: you write every section, when the module named in its heading asks for it; no AI session writes it. This is one shared file for both tracks (design D3): each version is a section, a later section adds to the earlier ones and never relaxes them, and where two sections conflict, the stricter rule wins. `/grade-paper` reads it when it grades a pre-registration or a lab report: the `disclosure` dimension checks a report against the rules written here.

<!-- Section format, one section per version. Replace "(not written yet)" with the date when you write it:
     ## Q-v0 — Q06, YYYY-MM-DD
     1. <rule> — earned by: <the run, exercise or reading that taught it> — checked by: <a command, an audit, or only a reader>
     2. ...
     Applies to: <which reports and runs> -->

## Q-v0 — Q06 (not written yet)

<!-- What Q06 asks for here (its chapter's EVAL.md v0 step): your first evaluation report, over your own
     first tries (instructor/calib/*.tsv, read through fvh.records): the claim; the metric and its
     estimator; n; the interval (H6's function in harness/q/fvh_q/q06_stats.py, or fvh.stats directly);
     the exclusions and how many; the cost; and one disclosure line. -->

## Q-v1 — Q09 (not written yet)

<!-- What Q09 asks for here (its chapter's EVAL.md v1 step): your second evaluation report. The
     claim: the share of your own Dafny proofs of Q04–Q09 (every hole you filled) that are stable,
     that is, they verify under seeds 1–3 and under both Z3 binaries bundled with Dafny
     (`scripts/vcheck --brittleness --solvers`). The metric and its estimator: a proportion with
     its Wilson interval (fvh.stats); n: the number of proofs; the exclusions: none (a
     resource-limit hit counts as unstable); the cost: the solver time of the runs; and the
     disclosure: one machine, one solver pair, three seeds, and you as the author of the proofs
     you measure. -->

## R-v0 — R07 (not written yet)

<!-- A later version gets its own section here when a chapter asks for one. -->
