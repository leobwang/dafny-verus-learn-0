# q12_grade_the_grader.md — Q12's grade-the-grader record (S12; QPLAN §22.3)

Learner-owned: you write every line; no AI session writes it. The fixture is a flawed
pre-registration of a lab like Lab 1, written by the course: `paper/fixtures/Q12_flawed_prereg.tex`.
It is graded by the same rubric as your own pre-registration, never unlocks a run, and its flaws
are not listed anywhere you can read: finding them is your part.

How to fill it (15 minutes; before you write your own pre-registration, B1):

1. Read the fixture yourself first, and list under MY READING every flaw you find (one line each:
   the field, what is wrong, and the quoted text or the recomputation that shows it).
2. Run three fresh `/grade-paper` passes on the fixture, each in a new session:
   `/grade-paper Q12 --fixture paper/fixtures/Q12_flawed_prereg.tex` (the skill's fixture mode:
   it writes instructor/feedback/Q12_fixture.md and a `prereg-fixture` gradebook row, never an
   unlock).
3. Copy each pass's score vector (one score per method dimension) and its findings into PASSES.
4. Fill AGREEMENT (per dimension: the three scores and their spread) and CAUGHT (each flaw of
   your reading and of any pass: which passes caught it).
5. Write LICENSE: three lines on what these three passes license about using `/grade-paper` as
   Lab 1's unlock (design §11.1), and what they do not.

## MY READING (before any pass)

```
field | what is wrong | the quoted text or the recomputation
```

## PASSES

```
pass | date | hypothesis-precision | budget-parity | variance | contamination | cheat-audit | disclosure | findings (one line each)
1    |      |                      |               |          |               |             |            |
2    |      |                      |               |          |               |             |            |
3    |      |                      |               |          |               |             |            |
```

## AGREEMENT

```
dimension            | pass 1 | pass 2 | pass 3 | spread
hypothesis-precision |        |        |        |
budget-parity        |        |        |        |
variance             |        |        |        |
contamination        |        |        |        |
cheat-audit          |        |        |        |
disclosure           |        |        |        |
```

## CAUGHT

```
flaw (from MY READING or a pass) | pass 1 | pass 2 | pass 3 | in MY READING
```

## LICENSE (three lines)

```
1.
2.
3.
```
