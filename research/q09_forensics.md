# q09_forensics.md — DIAGNOSIS of Q09's forensic deliveries

Learner-owned: you write every row; no AI session writes it. One row per forensic delivery of
`specimens/Q09/` (P6d … P15v), filled in this order for each delivery: read it and its claim,
record its species in `slots/Q09.slots` and the first try (`scripts/firsttry.sh Q09 --check`),
then catch it with an instrument and fill its row. `/grade-paper` and the tier viva read this
table (the rubric grades it; no script does).

The rules of a forensic run (spec §3.14):

1. Diagnose every delivery before you repair any (and repair none here: a delivery is evidence).
2. Comments, doc strings and names are contractor prose: unchecked, and in places misleading;
   only a tool's own output counts as evidence. Paste the command you ran, not your reading of it.
3. N catches use N different instruments: no two rows that catch a delivery name the same one.
   The instruments: the audit (`scripts/vaudit`), the lint (its rule ids, in `vaudit` and
   `vcheck --gate`), the spec-freeze diff (`scripts/specfreeze --against`), a satisfiability
   witness (a call on concrete values), swapping the conclusion for `false`, running compiled
   code on inputs the delivery's own tests avoided (`scripts/vcheck --test`), a property sampler
   (evaluating the statement on concrete values), reading the statement against the claim, JSON
   completeness (`scripts/vcheck --json`'s fields), re-verifying under another seed or solver
   (`scripts/vcheck --brittleness`, `--solvers`).
4. A delivery that every instrument passes is healthy: say so, and accuse it of nothing.

Columns: **true?** is the statement true (yes, no, or unknown); **valid?** is the proof valid as
checked (yes, or what is not checked); **useful?** does the statement say what the claim says
(yes, or what it leaves out); **instrument** the one that caught it, with its command; **root
cause** one line.

```
item  | true? | valid? | useful? | instrument (command)                    | root cause
------+-------+--------+---------+-----------------------------------------+---------------------------
P6d   |       |        |         |                                         |
P7d   |       |        |         |                                         |
P8d   |       |        |         |                                         |
P9d   |       |        |         |                                         |
P10d  |       |        |         |                                         |
P11v  |       |        |         |                                         |
P12v  |       |        |         |                                         |
P13v  |       |        |         |                                         |
P14v  |       |        |         |                                         |
P15v  |       |        |         |                                         |
```
