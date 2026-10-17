# R track author notes (DVR plan: R01–R16 records, band-1 item plan)

> **Author-only.** This file holds prediction answers (captured and expected), hole references and their levers, the planted errors and soft spots of the agent files, the checkpoint statements, the cards' intended demos and the reasoning behind every disjointness call. Never quote, paraphrase or link any of it from a learner-visible file (`PLAN.md`, `QPLAN.md`, the registry, exercise, check, exit and agent files, specimens, `slots/`, `expected/`, chapters, banks, rubrics, `docs/design/*`, `VERSIONS.md`, `CLAUDE.md`). The learner-visible plan is `PLAN.md`; item ids here are the same.

Written 2026-10-07 by the R-plan lane (scratch `/tmp/dvl0-plan5r-rplan/`), while DVR0's two spike lanes (`Solutions/spikes/regex/dafny/`, `…/verus/`) were still running; **revised the same day** after both spike lanes reported and after the plan review (§1.4 holds the spike evidence per item, §10 the review's dispositions). Section numbers below follow `PLAN.md`.

## 0. What was and was not run

Every result below was captured on the pins through the course wrapper (`scripts/vcheck`, `scripts/vaudit`) at the course limits, one solver job at a time; Verus jobs additionally ran under `systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0` (this lane's 8 GB share). `free -g` showed 102 GB available before the first job. Probe files are lane scratch under `/tmp/dvl0-plan5r-rplan/p/`, **not archived**; raw outputs under `/tmp/dvl-1000/runs/` (names below). These are plan-time probes on inline stand-ins, not the shipped files: **every answer is re-captured on the real files** by DVR1 (`scripts/pins.py --update --ref --module <ID>`; `scripts/firsttry.sh <ID> --empty-body` for the gate).

| probe | file | command | result (verbatim summary line and first diagnostic) | raw output |
|---|---|---|---|---|
| midpoint, Dafny | `p/mid.dfy` (`MidInt` over `int`, `MidU32` over `newtype u32 = x: int \| 0 <= x < 0x1_0000_0000`, `ExpectThenAssert`) | `scripts/vcheck mid.dfy` | `failed — 3 verified, 0 holes, 1 error`; `mid.dfy:14:12: error: result of operation might violate newtype constraint for 'u32'` (line 14 is `MidU32`'s body) | `dafny-verify-20261007-055937-3u87opib` |
| midpoint, Verus | `p/mid.rs` (`mid_u32`, `(lo + hi) / 2` on `u32`) | `scripts/vcheck mid.rs` | `failed — 1 verified, 0 holes, 1 error`; `mid.rs:7:5: error: possible arithmetic underflow/overflow` | `verus-verify-20261007-055947-rju516co` |
| A1 definitions, Dafny | `p/re.dfy` (`Re`, compiled `Matches` with `decreases r, \|s\|` and a non-empty `Star` chunk, `Nullable`, a `{:test}`) | `scripts/vcheck re.dfy`; `scripts/vcheck --test re.dfy` | `verified — 2 verified, 0 holes, 0 errors`; `verified — 1 passed, 0 failed` / `PASSED T` (the bounded existentials compile and run) | — |
| A1 definitions, Verus | `p/re.rs` (`enum Re` with `Box`, `open spec fn matches` with `decreases r, s.len()`, `#[trigger]` on the first conjunct of each existential) | `scripts/vcheck re.rs` | `verified — 2 verified, 0 holes, 0 errors` | — |
| test outside `requires`, Dafny | `p/pre.dfy` (`Halve` with `requires n % 2 == 0`; `@Test` calling `Halve(7)`) | `scripts/vcheck pre.dfy`; `scripts/vcheck --test pre.dfy` | `failed — 2 verified, 0 holes, 1 error`; `pre.dfy:10:17: error: a precondition for this call could not be proved`; test: `failed — 0 passed, 0 failed, stage verify` | `dafny-verify-20261007-060141-4k5476r0`, `dafny-test-20261007-060142-6c4tpyw3` |
| test outside `requires`, Verus | crate `p/prev` (`halve` with `requires n % 2 == 0`; `#[test]` in `#[cfg(test)] mod tests` outside `verus!`) | `scripts/vcheck prev/src/lib.rs`; `scripts/vcheck --test prev/src/lib.rs` | `verified — 1 verified, 0 holes, 0 errors`; test: `failed — 0 passed, 1 failed`, `FAILED tests::test_halve` | `verus-test-20261007-060152-3mwr9f88` |
| signed division | `p/div.dfy` (`expect (-7) / 2 == -4` in a `{:test}`), `p/div.rs` (`assert((-7int) / 2 == -4) by (compute_only)`; exec `let q: i32 = -7i32 / 2; assert(q == -3);`) | `scripts/vcheck --test div.dfy`; `scripts/vcheck div.rs` | Dafny `verified — 1 passed, 0 failed`; Verus `verified — 3 verified, 0 holes, 0 errors` | — |
| `expect` vs `assume`, gate and audit | `p/exp.dfy` (`Pos` with `expect x > 0;` outside a test), `p/asm.rs` (`pos` with `assume(x > 0);`) | `vcheck`, `vcheck --gate`, `vaudit` on each | Dafny: `vcheck` `verified — 1 verified, 0 holes, 0 errors` (exit 0); `vcheck --gate` `verified — 1 verified, 0 holes, 0 errors` (exit 0); `vaudit` `exp.dfy:4: expect-outside-test — \`expect\` outside a {:test}/@Test method is assumed by the verifier (Δ3, G11)`, `1 finding(s)` (exit 1). Verus: `vcheck` `verified — - verified, 1 hole, 0 errors` / `hole assume pos` (exit 0); `vaudit` `asm.rs:6: hole-assume — an assume hole (in pos) not on the trust allowlist`, `1 finding(s)` (exit 1); `vcheck --gate` exit 1 with `gate: 'success' is false, not true; --output-json lacks 'is-verifying-entire-crate'; 'encountered-vir-error' is true, not false; --output-json lacks 'verified'; 1 hole(s); exit 1` — the crate-level keys fail because a lone `.rs` file is not a crate, so this run is **not** evidence for R04.P5dv's Verus column | `verus-verify-20261007-060946-7fa4oh5o` |

**Revision round (plan review):** this lane ran **no solver job**. The spike evidence in §1.4 is the spike lanes' (Dafny: `scripts/dvl`, bundled Z3 4.12.1, resource limit 5M, 8 GB cap, archive `~/.cache/dafny-verus-learn-0/author-probes/dvr0-dafny/`; Verus: `dvl.verus`, `--rlimit 2`, 16 GB cap, archive `…/dvr0-verus/`), read from `Solutions/spikes/regex/dafny/summary.json` and the Verus `table-rl2.json`. The Lean name scan of §8 read declaration names only, from the learner checkout's `LeanLearn0/R07*–R16*.lean` exercise files (no solution, no proof body).

**Not run:** the empty-body gate on any band-1 hole (none exists as a file yet); any prediction other than those above; Verus seeds 2–3; anything needing Docker or a model. **Read, not run:** the spike lanes' files as of 06:15 on 2026-10-07 (`RG_A1_Re.dfy`, `RG_A2_Deriv.dfy`, `RX_Items.dfy`, the Verus A1/A2 declarations); their gate tools (`dafny/tools/gate.py`, `verus/tools/vrun.py`) were not run by this lane.

## 1. The layers and the spike lanes

### 1.1 What this plan takes from the spike files (mapping)

| spike region (`@hole-begin <id>`) | plan item | note |
|---|---|---|
| `A1.NullableCorrect` | R02.H1d / H1v | same statement; re-supplied by A1b (R06) |
| `A1.SizePositive` (`Size(r) >= 1 && Size(Rev(r)) == Size(r)`) | R02.H2d / H2v `NodeCountBackwards` | renamed (§1.2) |
| — (new) | R02.H3d / H3v `NullableBackwards` | structural; reference: per-constructor recursive calls, `Cat`'s conjunction commutes |
| `A1.StarOne` | R05.H3d / H3v | re-supplied by A1b |
| `A1.StarConcat` | R05.H4d / H4v (annotation: the spike's `if u == [] { assert u + v == v; } else { var i :\| …; StarConcat(…); assert (u + v)[..i] == u[..i]; assert (u + v)[i..] == u[i..] + v; }` minus the three asserts) | the hole is the asserts; re-supplied by A1b |
| `A1.ReverseLength`, `A1.ReverseAppend`, `A1.ReverseReverse`, `A1.RevRev`, `A1.RevSound`, `A1.RevCorrect` | R06's decomposer (agent), top statement `BackwardsCorrect` = the spike's `RevCorrect` | the helpers are the agent's to discover; the reference decomposition is the spike's |
| `X.WitnessAbb`, `X.WitnessNotBa`, `X.WitnessAnchored` (`RX_Items.dfy`) | R04.H1, H2, H3 | same statements |
| `A2.ClassMember` | R03.H1d (Dafny); the Verus `member_from` shape is this plan's | — |
| `A2.ClassInsert` (several regions) | R03.W2d / W2v (given, worked) | not a hole in R03 (ClassUnion is built on it) |
| `A2.ClassUnion` | R03.H3d / H3v | over `ClassInsert` |
| `A2.DerivCorrect` | R06.H1d / H1v (flagship) | spike's `Cat` case calls `NullableCorrect(a)` (Verus `lemma_deriv` calls `lemma_nullable(*a)` too): that call is the paper problem's discovery; A1b supplies the lemma, so the learner finds *which* given fact the case needs, and no R02 proof is redone |
| `A3.CatEpsLeft` | R02.H4d / H4v | same statement (`Cat(Eps, b)`); re-supplied by A1b |
| `A3.CatAssoc` | R05.H1 (⇒) and H2 (⇐) | the spike proves the equivalence (22 lines, `{:induction false}`); each R05 item is one direction; re-supplied by A1b as the equivalence |
| `A2.DerivMatch` | R06.H2d / H2v | invariants and the post-loop facts are the hole; the body's `DerivCorrect(cur, s[i], s[i + 1..])` call and `assert [s[i]] + s[i + 1..] == s[i..]` ship given |
| `X.Match` (`RX_DerivMatcher refines RX_MatcherSpec`) | R08 (band 2) | — |

### 1.2 Requests to DVR0 (also in `Solutions/spikes/regex/PLAN-R-NOTES.md`)

1. **Names** (avoid list, PLAN §5.5). By 06:30 the Dafny spike had renamed `Size` → `NodeCount` (as here) and `Rev` → `Mirror`, which hits Lean R's `mirror`/`mirror_mirror`; the plan keeps `Backwards`. The full list: `Size` → `NodeCount` (Q has `Size`, `size`; Lean R has `size` on `Tree`); `Rev` → `Backwards` (Q has `Rev`, `RevRev`, `RevAppend` in its exercise files); the string `Reverse` → `BackwardsStr`, `ReverseAppend` → `BackwardsStrAppend`, `ReverseReverse` → `BackwardsStrInvolution`, `ReverseLength` → `BackwardsStrLength` (Lean R has `reverse`, `reverse_append`, `reverse_reverse`); `RevRev` → `BackwardsInvolution`, `RevSound` → `BackwardsSound`, `RevCorrect` → `BackwardsCorrect`; `SizePositive` → `NodeCountBackwards`. Verus snake-case likewise (`node_count`, `backwards`, `backwards_str`, …).
2. **Dafny `Matches` ghost** (`ghost predicate`): otherwise R06.H2d's exec matcher answers itself with `b := Matches(r, s)`. `Nullable`, `NodeCount`, `Backwards`, `BackwardsStr` stay compiled (the matcher needs `Nullable`; the R02 agent's property tests use them).
3. **A1 ships no lemma.** Every lemma region of the spike's `RG_A1_Re.dfy` is a module hole (R02, R05) or the R06 agent's; A1 as shipped is the datatype, `Matches`, `Nullable`, `NodeCount`, `Backwards`, `BackwardsStr`, and in Verus `is_nullable` and `copy_re`.
4. **Gate the plan's items, not only the spike's regions:** R02.H3 (`NullableBackwards`), R02.H4 (`CatEpsLeft`), R02.H5 (`IsVoid`), R03.H2, H4, H5, R04.H4, H5, R04.T1, R06.H3, H4, H5, T1 and the R06 checkpoint have no spike region yet.

**Status after the spikes (revision).** 1: the Dafny spike kept `Mirror`/`Reverse`; DVR0's reconciliation renames (PLAN §2.5). 2: not done (the spike's `Matches` is a compiled `predicate`); DVR0. 3: not done (A1 holds every lemma); the plan review's answer is the new layer A1b, declared by R06, so the lemmas R06 needs are given there and R02's and R05's holes stay holes in R02 and R05. 4: the spikes gated their own regions only; §1.4 lists what is covered and what is not.

### 1.3 Plan-lane observations on the A1 definitions

- Both definitions of `Matches` were accepted as written (§0, `re.dfy`, `re.rs`): the lexicographic measure `r, |s|` with a non-empty `Star` chunk passes both tools' termination checks. The plan lane's Verus probe put `#[trigger]` on the recursive call `matches(*a, s.subrange(0, i))`. **Superseded by the Verus spike** (`probe-split-trigger/`, archived): with that trigger the one-step unfolding facts of `Cat` and `Star` fail; with `#[trigger]` on `s.subrange(0, i)` all four probes verify. A1 uses the subrange trigger. Because A1 shows it, no R14 prediction may ask which trigger A1's existentials need (PLAN §2.4 F5); R14 studies triggers on its own variants.
- A compiled Dafny `Matches` runs in tests (`re.dfy`'s `{:test}` passed): useful for the author's own differential checks, and the reason for request 2.

### 1.4 Spike evidence per band-1 item (revision; read from the spike lanes' results, not re-run)

Dafny modes: `maxauto` = default induction (maximal automation, the R01–R02 setting), `manualind` = `manual-lemma-induction` (the proposed R03–R16 setting), `indfalse` = `{:induction false}` on the lemma; each at seeds 1–3 (and the default seed for `maxauto`). Verus modes `E0`/`E0H`/`E1`/`NL` at seeds 1–3, `--rlimit 2`. "Fails" = the empty body fails in every run of that mode. Proof lines follow PLAN §0's rule (exec code excluded; invented statements not yet added).

| plan item | spike region | Dafny: empty body · lines | Verus: gate · lines | consequence for the plan |
|---|---|---|---|---|
| R02.H1d/v `NullableCorrect` | `A1.NullableCorrect`; V `lemma_nullable` | fails in all three modes · 13 | PASS (all fail) · 13 | no lever needed on R02's default induction: the plan drops `{:induction false}` from H1d |
| R02.H2d/v `NodeCountBackwards` | `A1.NodeCountFacts` (same statement) | **verifies under `maxauto`** (4/4); fails under `indfalse` and `manualind` · 12 | not spiked (no `node_count`/`backwards` in the Verus A1) | the `{:induction false}` lever is required, as planned |
| R02.H3d/v `NullableBackwards` | — | not spiked | not spiked | gate pending; risk as H2 (lever kept) |
| R02.H4d/v `CatEpsLeft` | `A3.CatEpsLeft` | fails in all modes · 3 | not spiked | intro size; minutes 5 / 7 stand; re-supplied by A1b |
| R02.H5d/v `IsVoid` | — | not spiked | not spiked | gate pending (TRIV on both) |
| R03.H1d `ClassMember` | `A2.ClassMember` | code only (4 code lines, 0 proof lines); a trivial body fails 3/3 | no Verus class API in the spike | an implementation hole, as planned; the Verus `member_from` is unspiked |
| R03.W2d `ClassInsert` (given) | `A2.ClassInsert` | 31 proof + 16 code lines; the empty proof region fails | — | a long worked example: R03's chapter walks it in the 30-min worked line |
| R03.H3d `ClassUnion` | `A2.ClassUnion` | code only (5 code lines); a trivial body fails 3/3 | — | intro size, not the "≈ 10–15 lines" §4.2 assumed; its 7 minutes stand (band-1 holes are not banded by line) |
| R03.H2, H4, H5 | — | not spiked | not spiked | gate pending |
| R04.H1d–H3d witnesses | `X.WitnessAbb`, `X.WitnessNotBa`, `X.WitnessAnchored` | fail in all modes · 7, 6, 5 | not spiked | gate passes for Dafny |
| R04.T1, H4, H5 | — | not spiked | not spiked | gate pending |
| R05.H1/H2 `CatAssocLR/RL` | `A3.CatAssoc` (the equivalence) | fails in all modes · 22 for both directions; under automatic induction at the default seed the reference ran out of resources (5.03M), so it keeps `{:induction false}` | not spiked | each direction about 11 lines [A]; R05 is on `manualind` (proposed), where the reference verifies 4/4 |
| R05.H3 `StarOne` | `A1.StarOne` | fails in all modes · 3 | not spiked | gate passes (Dafny) |
| R05.H4 `StarConcat` (annotation) | `A1.StarConcat` | the whole body: fails in all modes · 8 | `lemma_star_concat` (spike A4) PASS · 14 | the plan's annotation configuration (case split, `:\|` and call kept, the three asserts blanked) is not gated yet |
| R06.H1d/v `DerivCorrect` | `A2.DerivCorrect`; V `lemma_deriv` | fails in all modes · 50; calls `NullableCorrect` | PASS · 75 (`Cat` 38, `Star` 25); calls `lemma_nullable`; `Star` needs only the IH on the body | S1 closed; hard band in both; minutes 60 / 68 |
| R06.H2d/v `DerivMatch` | `A2.DerivMatch`; V `matches_vec` | fails under `maxauto` and `manualind` · 6 (with the body's call, which the plan ships given) | PASS · 16 | the plan's configuration (call kept) is not gated yet |
| R06.A1d decomposer | `A1.MirrorCorrect` 8, `MirrorSound` 30, `ReverseAppend` 7, `ReverseReverse` 8, `MirrorMirror` 12, `ReverseLength` 3 | all verify; `MirrorMirror` and `ReverseLength` verify empty under `maxauto` (fail under `manualind`) | not spiked | Dafny decomposition exists (uses `StarOne`, `StarConcat`: A1b); Verus pending |
| R06.T1, H3, H4, X1, X2 | — | not spiked | not spiked | gate pending (new objects of this revision, §7) |
| R01 (all) | — | not spiked | not spiked | gate pending |

**Still to gate on the shipped files (DVR1), both languages unless marked:** R01 T1, H1, H2, H3; R02 H2v, H3, H4v, H5; R03 H1v, H2, H3v, H4, H5; R04 T1, H1v–H3v, H4, H5; R05 H1v–H3v and H4 in its annotation form; R06 T1, H2 in its shipped form, H3, H4, X1, X2, A1v (pending spike). Every item the spike did gate is re-gated on the shipped file anyway (the spike's file is not the exercise file).

**Consequences recorded elsewhere:** Dafny `Matches` stays requested ghost (§1.2); the Verus split trigger (§1.3); A5's opaque `Accepts` and one-step lemmas, the A3 vacuity of `ClassItems`/`Counted`, and the given A4 congruence facts (PLAN §2.5).

## 2. R01

### 2.1 Prediction answers

| item | answer (slot text) | evidence / status |
|---|---|---|
| P1dv | `D-int:ok D-u32:fail V:fail` | captured (§0 midpoint rows; Dafny's message is the newtype constraint, Verus's the arithmetic overflow) |
| P2dv | `D:fail,not-run V:ok,failed` | captured (§0 test rows): Dafny verifies the test method, so the call's precondition fails at verification and the test never runs; Verus's `#[test]` outside `verus!` is unverified Rust |
| P3d | expected `FAILS b d` | to capture: the caller sees only `ensures y > x` (method bodies are opaque); [c] follows from `y > 5` over integers |
| P4v | expected `FAILS b d` | to capture (exec fn bodies are never visible to callers) |
| P5d | `-4` | captured (§0, `div.dfy`: Euclidean division) |
| P6v | `-3` | captured (§0, `div.rs`: exec `i32` division truncates; spec `int` division is Euclidean, `-4`) |

**Leak checks (R01).** No R01 worked example, card demo or given declaration divides a negative number (P5d, P6v), adds two bounded values without a bound (P1dv), calls a function outside its `requires` in a test (P2dv), or shows a caller asserting more than an `ensures` (P3d, P4v). W1v discharges an index underflow by its `requires`: it shows that Verus checks exec arithmetic, which R01's chapter states anyway (the Q-owned machine-subtraction fact, stated) and which does not answer P1dv's Dafny columns. The agent file must not hold a midpoint-overflow bug (its fix would be H1's answer).

### 2.2 Holes and test-out: references, levers, gate

| item | intended reference | lever | gate |
|---|---|---|---|
| T1d `CountCharSingle` | `assert [d][1..] == [];` (one fact) | none | pending; if the empty body proves it, use `CountCharPair(d, e, c)` over `[d, e]` instead |
| T1d `CountFirstTwo` | `n := (if s[0] == c then 1 else 0) + (if s[1] == c then 1 else 0);` plus `assert s[..2] == [s[0]] + [s[1]];` and a `CountCharAppend` call, or two unfolding asserts | none | pending |
| T1v | the same; `count_first_two` adds two `u32`s at most 2 | none | pending (TRIV on the exec fn) |
| H1d `Midpoint` | `m := lo + (hi - lo) / 2;` | none | pending |
| H1v `midpoint` | `lo + (hi - lo) / 2` | none | pending (TRIV) |
| H2d `CountCharAppend` | `if \|s\| > 0 { assert (s + t)[1..] == s[1..] + t; CountCharAppend(s[1..], t, c); } else { assert s + t == t; }` | `{:induction false}` (R01 is on Dafny's default induction) | pending |
| H2v | the same with `drop_first` and `=~=` | none | pending |
| H3d `MeanOfTwo` | `requires a as int + b as int < 0x1_0000_0000`; the given callers include `MeanOfTwo(0x7FFF_FFFF, 0x8000_0000)` so `requires a < 0x8000_0000 && b < 0x8000_0000` fails a caller | none | pending; the freeze leaves the `requires` open (Δ160; PLAN §8 R11) |
| H3v | `requires a + b <= u32::MAX` (spec arithmetic) | none | pending |

### 2.3 Agent files (planted errors)

Four one-line bugs per language, each its own declaration with one diagnostic, over midpoints-free objects: (1) an off-by-one index (`s[i + 1]` for `s[i]`) in a character lookup; (2) a wrong comparison (`<` for `<=`) that breaks an `ensures`; (3) a recursive call on the wrong suffix (`s[2..]` for `s[1..]`) in a `CountChar`-style function's lemma; (4) a missing `+ 1` in a length computation. No bug's fix is an R01 hole's answer. Verus: the same four kinds, with one of them an exec `u32` overflow whose one-line fix is a bound in the body (not the midpoint idiom).

### 2.4 Cards: intended demos

- C1–C3 (WRITE): success in the file; the failure demo a missing clause (an `ensures` the body violates, an `assert` the verifier cannot see, a lemma never called).
- C8dv false friends: the six rows on R01's own objects; the `decreases` row's demo is about a counting function, not about `Matches`.
- C9dv: integer division of negatives, Dafny `int` vs Verus exec `i32` (and Verus spec `int`), `// after: R01.P5d` and `// after: R01.P6v`, sealed sidecars.

### 2.5 The triage drill

Five outputs, captured on the pins by DVR1 and quoted with their runs: a `verified`, a `failed` with a postcondition, an `inconclusive` (resource limit), a resolve-stage error, and a Verus run that verifies with a counted hole. For each: what it licenses (and what not). The fourth must not be a missing-`decreases` error (Q01.P7dv's answer).

### 2.6 Bank (8 questions) seeds

Hole kinds and who counts them; what a `verified` licenses; the three loops' latencies; midpoint and bounded arithmetic; callers see contracts; `--test` vs verification; the contract's three keys; which guard layer refused which door.

## 3. R02

### 3.1 Prediction answers

| item | answer | status |
|---|---|---|
| P1d | expected `FAILS c d` ([a] and [b] unfold to their first disjunct; [c] needs the split witness 0 and the slice facts; [d] needs two nested witnesses) | to capture |
| P2v | expected `FAILS c d` | to capture |
| P3dv | expected `D:fail V:fail` (an empty first chunk re-calls `Matches(Star(a), s)` on the same arguments) | to capture; the stage each prints is part of the answer form only if it is `err:<stage>` |
| P4dv | expected `D:fail V:fail` (the `Star` case's call on `Star(a)` does not decrease `r`) | to capture |
| P5d | `true` (`Star(Empty)` is nullable) | by definition; capture through `pins.py` |

**Leak checks (R02).** A1 states `decreases r, |s|` and the non-empty chunk (the definitions are given), but no A1 or R02 text says why; the written problem asks why after P3dv/P4dv are committed. W1 names one split of a two-character string (a technique, not P1d's [c], whose split is at 0). No given code shows `Nullable` of a `Star(Empty)`.

### 3.2 Holes: references, levers

| item | intended reference | lever |
|---|---|---|
| H1 `NullableCorrect` | the spike's `A1.NullableCorrect` (per-constructor calls; `Cat` needs `assert e[..0] == e && e[0..] == e;` for `e == []`) | none (revision: the empty body fails under default induction, §1.4) |
| H2 `NodeCountBackwards` | per-constructor recursive calls | `{:induction false}` |
| H3 `NullableBackwards` | per-constructor recursive calls | `{:induction false}` |
| H4 `CatEpsLeft` | (⇐) witness 0 with `assert s[..0] == [] && s[0..] == s;`; (⇒) pick the split, show `s[..i] == []` so `i == 0` | none |
| H5 `IsVoid` / `is_void` | structural recursion mirroring `VoidSpec`; Verus `match r { Re::Alt(a, b) => is_void(a) && is_void(b), … }` with `decreases r` | none (TRIV on the Verus exec fn) |

Gate: pending on the shipped files. Evidence (§1.4): H1 needs no lever; H2's statement verifies empty under default induction, so its lever is required; H3 is unspiked and keeps the lever as a precaution until its gate runs (drop it if the empty body fails without it).

### 3.3 Agent file (spec-first): the three definitions and their soft spots

`Alphabet(r): set<char>` (soft spot: `Empty` and `Eps` give `{}`; an implementation that forgets `Star`'s body passes one shipped check); `StarHeight(r): nat` (soft spot: `Alt`/`Cat` take the max, an implementation that sums passes the shipped checks on single-star samples); `MinLen(r): nat` with the convention "0 for a regex that matches nothing" (soft spot: `Alt` takes the min, `Cat` the sum; the convention makes `Cat(Empty, Chr('a'))` report 1 unless the implementation tests voidness: the prose contract says such a `Cat` matches nothing, the formal `ensures` does not). Each prose contract is stronger than its `ensures`. The adversarial checks the learner should find: the `Star` body for `Alphabet`, a nested `Alt` for `StarHeight`, a void `Cat` for `MinLen`.

### 3.4 Cards

C7dv: matching on a recursive datatype through a reference and boxes (Dafny `match r` on a value; Verus `match r` on `&Re` with `Re::Cat(a, b)` binding `&Box<Re>`, and `*a` / `**a` in specs). No `after:` (it settles no prediction).

## 4. R03

### 4.1 Prediction answers

| item | answer | status |
|---|---|---|
| P3dv | expected `D:fail V:fail` (a `provides`-only function's body is hidden; a `closed` view and an `ensures` stating only validity say nothing about members) | to capture |
| P4dv | Dafny column to capture (the revealed body gives `ClassSingle('b') == CharClass([CRange('b', 'b')])`, and `InClass`'s existential then needs the witness 0, which the solver may or may not find unaided); Verus expected `fail` (an exec fn's body is never visible to a caller, whatever the view's visibility) | to capture; if Dafny's column is `ok`, the card C8dv shows the witness-free case |
| P1d | expected `FAILS c d`: the specimen's [a] `ClassSingle` and [b] `ClassInsert(ClassEmpty(), …)` carry `ensures ClassValid(…)`; [c] is a hand-written literal with an inverted range (`CRange('c', 'a')`), [d] a parameter with no `requires` | to capture; the author writes the specimen to these labels |
| P2v | expected `FAILS c d` | to capture |

Replacement for R03.P1d/P2v if the orchestrator rules the owner-tag boundary against R (PLAN §8 R9): a call-site question about an `ensures` the API weakens (which client asserts fail when `ClassUnion`'s `ensures` keeps only validity).

### 4.2 Holes

| item | intended reference |
|---|---|
| H1d `ClassMember` | `if \|cc.ranges\| == 0 then false else InRange(cc.ranges[0], c) \|\| ClassMember(CharClass(cc.ranges[1..]), c)` plus the `InClass` witness shift (a lemma or `assert`s); the spike's region |
| H1v `member_from` | `if i == self.ranges.len() { false } else { let (lo, hi) = self.ranges[i]; (lo <= c && c <= hi) \|\| self.member_from(c, i + 1) }`, `decreases self.ranges.len() - i` |
| H2 `ClassRange` | `if lo <= hi then CharClass([CRange(lo, hi)]) else ClassEmpty()` (+ `export` entry) |
| H3 `ClassUnion` | fold `b.ranges` into `a` with `ClassInsert`, by recursion on `b`'s ranges; membership by induction over the fold |
| H4 `Union3` | two `ClassUnion` calls; the proof is the two `ensures` |
| H5 `ClassOfString` | recursion over `s` with `ClassInsert(…, CRange(s[0], s[0]))` |

Gate pending. Band (revision, §1.4): `ClassMember` and `ClassUnion` need no proof lines over the given `ClassInsert` (4 and 5 code lines; the spike's annotations proved unnecessary), so R03's holes are short implementation holes; the given `ClassInsert` (31 proof lines) is the module's long worked example.

### 4.3 Agent

`ClassIntersect` and `ClassDiff`; soft spots: the agent adds `requires a != b` or a `requires` on non-emptiness (the freeze line catches it); `ClassDiff` at the character boundaries (`'\0'`, the largest `char`; the surrogate gap if it splits a range: Dafny's `char` and Verus's `char` are both Unicode scalar values at the pins, R09's divergence card checks this [verify]).

### 4.4 Cards

C8dv: what crosses a module boundary (Dafny `provides`/`reveals`, Verus `open`/`closed`, private fields, exec bodies); `// after: R03.P3dv`, `// after: R03.P4dv`; sealed.

## 5. R04

### 5.1 Prediction answers

| item | answer | status |
|---|---|---|
| P1d | `D:ok` | captured (§0: `exp.dfy` `verified`, and `ExpectThenAssert` in `mid.dfy` verified) |
| P2dv | `a d` ([a]: the empty substring `s[0..0]` matches `Star(…)`; [b]: `"b"` is not in `a*`, so it forces `false`; [c]: an implication forces nothing; [d]: the suffix `s[1..] == []` matches) | logic; the author proves each claim in both languages (four lemmas per language in `Solutions/`) |
| P3d | expected `FAILS a b c d` (every claim needs a witness pair or a reasoning over all pairs) | to capture; if [b] verifies (witness `0, 0` found from the trigger), the answer is `FAILS a c d` |
| P4v | to capture | — |
| P5d (was P5dv) | `D:0 1` | captured on a lone file (§0: `vcheck --gate` exit 0, `vaudit` 1 finding, `expect-outside-test`); re-capture on the specimen. The Verus column is dropped (plan review: the gate's exit code and the audit's count for an `assume` is Q's hole visibility, Q01.P10dv); the Verus `assume` delivery moves to the audit drill, run on a crate |
| P6dv (new) | expected `D:c V:c` ([a] fails: `Occurs(Eps, [])` holds, so `false` violates it; [b] fails: `Matches(Eps, [])`; [c] verifies: `false ==> …` is vacuous; [d] fails: the empty suffix matches `Eps`) | to capture in both languages; the author proves the three counterexamples (`r := Eps`, `s := []`) in `Solutions/`. Leak check: P2dv's answer is not implied (P6dv fixes `b`, P2dv fixes `r` and `s`); no given code runs a `Find` that returns a constant |

**Leak checks (R04).** W1 and W2 do not mention `Occurs`; the audit drill's Verus `assume` delivery is opened only after P5d's first try (it states the Verus fact P5dv used to ask); the card C3d states the ban on `expect` outside tests but no outcome (the demo's sidecar holds it, sealed, `// after: R04.P1d`).

### 5.2 Holes

| item | intended reference |
|---|---|
| T1 `SomeWordMatches` | witness `"o"` (or `"ok"`): `assert Matches(Cat(Chr('o'), Star(Chr('k'))), "o")` by the split at 1 and `Star`'s empty case |
| H1 `WitnessAbb` | the spike's `X.WitnessAbb` (three nested splits) |
| H2 `WitnessNotBa` | the spike's `X.WitnessNotBa` (pick the split, the first chunk must be `"a"`, `s[0] == 'b'`) |
| H3 `WitnessAnchored` | the spike's `X.WitnessAnchored` |
| H4 `PrefixMatch` | `exists i :: 0 <= i <= \|s\| && Matches(r, s[..i])`; the three checks: `PrefixMatch(Chr('a'), "ab")` (proof given: `assert "ab"[..1] == "a";`), `!PrefixMatch(Chr('b'), "ab")` (proof given: for every `i`, `"ab"[..i]` is not `"b"`), `PrefixMatch(Eps, s)` (proof given: `assert s[..0] == [];`). The checks discriminate: a definition with `i < \|s\|` fails the third on `s == []`; the unanchored `Occurs` fails the second (`Occurs(Chr('b'), "ab")` holds); a whole-string `Matches` fails the first |
| H5 `MutantKilled` | witness `r := Chr('a')`, `s := "a"`: `Nullable(r) == false`, `Occurs(r, s)` by `0, 1` |

### 5.3 Agent (audited prover) and its plant

Three lemmas: (1) `Occurs(r, s) ==> Occurs(r, s + t)` (true: the same indices); (2) `Matches(r, s) ==> Occurs(r, s)` (true: `0, |s|`); (3) **planted, false:** `Occurs(Cat(a, b), s) ==> Occurs(Cat(b, a), s)` (counterexample `a := Chr('x')`, `b := Chr('y')`, `s := "xy"`), with `// planted: R04.A1d` (`R04.A1v`). The debrief question: did the contractor stop and report, or add a `requires`, an `assume`, or weaken the `ensures`?

### 5.4 Cards

C5dv: runtime checks vs proof obligations (Dafny `expect` outside a test is assumed by the verifier and only the audit lists it; Verus has no `expect`, and `assume` is a hole the gate counts); `// after: R04.P1d`, `// after: R04.P5dv`; sealed.

### 5.5 Written problems

Classify four specs: the four of P2dv on a different pair `(r, s)`, so that P2dv's answer is not repeated. wp/VC by hand: a three-assignment method over `int` with one `if`.

## 6. R05

### 6.1 Prediction answers

| item | answer | status |
|---|---|---|
| P3dv (replaced) | expected `D:same,varies V:same,varies` (the solver is deterministic for a fixed input, seed and options, so the resource count repeats; wall time does not), but **to capture**: ten runs per language through `scripts/vcheck --json` on the W1 copy, one at a time; if Verus's `resource_count` is absent or varies at the pin, the captured value is the answer and the card says why | to capture. The earlier P3dv (how many errors two independent false asserts produce) repeated Q07.P7d[a] and Q03.P6dv's error counting (Q's by its homes, PLAN §5.1). Boundary with Q09.P2dv (seeds change outcomes): P3dv fixes the seed and asks about repetition, so the two are distinct. The variance log (30 min) then measures both fields, which is the payoff |
| P4dv | expected `D:ok V:ok` (the fast channel verifies only the named symbol) | to capture |
| P1d, P2v | to design and capture: five slice facts at `0 <= i <= j <= |s|`, e.g. `s[..j][..i] == s[..i]`, `s[..j][i..] == s[i..j]`, `s[i..][..j - i] == s[i..j]`, `s[..i] + s[i..] == s`, `(s[..i] + s[i..j]) == s[..j]`; at least one label must depend on an earlier failing one (the assumed-after-failure effect, Δ38). W1's facts must be different ones |

### 6.2 Holes

| item | intended reference |
|---|---|
| H1 `CatAssocLR` | pick `i` (outer) and `k` (inner, in `s[..i]`); witness `k` for the outer `Cat(a, Cat(b, c))` and `i - k` for the inner, with `s[..i][..k] == s[..k]`, `s[..i][k..] == s[k..i]`, `s[k..][..i - k] == s[k..i]`, `s[k..][i - k..] == s[i..]` |
| H2 `CatAssocRL` | symmetric |
| H3 `StarOne` | the spike's `A1.StarOne` |
| H4 `StarConcat` | the spike's `A1.StarConcat`; the hole is its three `assert`s (the shipped skeleton keeps the case split, the `:|`, the call) |
| H1py `runs_from_log` | `json.loads` per line; `Run(wall_s, resource_count, verdict)` from the `vcheck --json` document's fields as `harness/tests/r/test_r05_variance.py` pins them |
| H2py `variance_summary` | `statistics.fmean`, `statistics.stdev`, CV = sd / mean; `fvh.stats.bootstrap_ci(values, statistics.fmean, seed=seed)` |

The acceptance tests check composition the way Q06's do: they replace `fvh.stats.bootstrap_ci` and check that `variance_summary` calls it (no re-implemented bootstrap).

### 6.3 Agent (obligation prover)

Two lemmas: `Matches(Star(a), u) && Matches(a, v) ==> Matches(Star(a), u + v)` and `Matches(Cat(Star(a), Star(a)), s) ==> Matches(Star(a), s)`; both need a `StarConcat`-like helper by induction, which the agent must find from failing obligations alone.

### 6.4 Cards

C5dv: what repeats across runs and what does not (resource counts vs wall time, Dafny and Verus, with the seed held fixed), and what a single timing licenses; `// after: R05.P3dv`; sealed. (The earlier topic, how many failures a run reports, is Q's.)

## 7. R06

### 7.1 Prediction answers

| item | answer | status |
|---|---|---|
| P1d | `Alt(Cat(Cat(Eps,Star(Chr('a'))),Chr('b')),Empty)` (with the spike's `Deriv`: `Star(Chr('a'))` is nullable, so the `Cat` case is the `Alt`) | by hand from the definition; capture through `pins.py` |
| P2v | `true` (`"ab"` is in `a*b`) | to capture |
| P3dv | expected `D:fail,ok V:fail,ok` | to capture |
| P4d, P5v | expected `FAILS c` (the one-directional invariant is established and preserved, and gives [d]; [c] needs the other direction) | to capture |
| P6dv | expected `D:fail V:fail` (the claim is false: `a := Cat(Chr('x'), Chr('y'))`, `c := 'x'`, `s := "yxy"`; `Star(Deriv(a, 'x'))` matches only strings of `y`s); the question is whether a tool reports `fail` or runs out of resources | to capture |

**Leak checks (R06, revised).** P3dv's lemma is not part of any hole's answer (no hole is about `Star(Chr('a'))` alone). P4d/P5v's specimen holds no `Nullable` and no post-loop fact, so it says nothing about the fact the flagship's paper problem finds. P6dv's claim is not H3's (H3 refutes a `Star`-unfolding claim on the empty string, P6dv asks about a derivative shortcut for stars). **A1b now gives `NullableCorrect`** (with five other facts, and no text saying which item uses which), so the discovery is *which given fact the `Cat` case needs and why it applies*, not a new lemma: the review's resolution (blocker 3). H4's statement names no `Nullable`; its reference uses `NullableCorrect` in the empty-string branch, which a learner meets only after the paper problem (the paper comes before the keyboard). W1 gives the three base cases of the flagship by design. Re-capture every R06 prediction with the shipped imports (the exercise file and its specimens import A1 and A1b).

### 7.2 Holes

| item | intended reference |
|---|---|
| T1 `AllNullable` | a loop with `invariant 0 <= i <= \|rs\| && (b <==> forall j :: 0 <= j < i ==> Nullable(rs[j]))` (or an early exit) |
| H1 `DerivCorrect` | the spike's `A2.DerivCorrect` (50 Dafny proof lines; Verus `lemma_deriv`, 75: `Cat` 38, `Star` 25); the `Cat` case calls A1b's `NullableCorrect(a)` (Verus `lemma_nullable_correct(*a)`). **Measure:** the spike's proofs recurse only on sub-regexes, so `decreases r` suffices in both; a proof that recurses on `Star(a)` needs `decreases r, \|s\|`. S1 closed: no fallback |
| H2 `DerivMatch` | the spike's `A2.DerivMatch`: `invariant 0 <= i <= \|s\|`, `invariant Matches(cur, s[i..]) <==> Matches(r, s)`; after the loop `NullableCorrect(cur); assert s[i..] == [];` (A1b's lemma). Verus: the spike's `matches_vec` (16 proof lines) |
| H3 `StarUnfoldRefuted` | witness `a := Chr('x')`, `s := []`: `Matches(Star(a), [])` by the first disjunct; `Cat(Chr('x'), Star(Chr('x')))` does not match `[]`, since the only split is at 0 and `Chr('x')` does not match `[]`. About 3–5 lines [A] |
| H4 `StarUnfold` | **the weakest hypothesis** `requires s != [] \|\| Nullable(a)` (Verus `s.len() > 0 \|\| nullable(a)`; `s != [] \|\| Matches(a, [])` is equivalent and accepted). Proof: (⇐) always: from the `Cat` split at `i`, if `i == 0` then `s[0..] == s` and `Star(a)` matches `s`; otherwise the split is a `Star` chunk. (⇒) if `s != []`, `Star`'s first chunk `i >= 1` is the `Cat` split; if `s == []`, `Nullable(a)` and A1b's `NullableCorrect(a)` give `Matches(a, [])`, and the split at 0 with `Matches(Star(a), [])`. About 12–16 lines [A]. **Why nothing weaker works:** outside the hypothesis (`s == []` and `!Nullable(a)`) the claim is false, by H3's argument. Stronger repairs the verifier accepts (`requires \|s\| > 0`, `requires Nullable(a)`, `requires a.Eps?`) fail "no stronger one": the review, the rubric and the viva check it |

Dropped by the revision: H5 `DerivStarFree` (12 min; its slot paid for the flagship, and `StarFree` existed only for the S1 fallback, now retired); the earlier H3/H4 (`NaiveCatRefuted`, `CatStep` with `requires !Nullable(a)`), whose repair showed the flagship's `Cat` split in the same file (review, minor). Gate pending for every R06 hole on the shipped files (§1.4). Band [A]: H1 hard in both languages; H4 intermediate.

### 7.3 Checkpoint statements (author-only; the Δ133 rule)

| id | form | statement or prompt | `uses:` | min |
|---|---|---|---|---|
| X1d | statement-shipped | `lemma {:induction false} DerivsAppend(r: Re, u: seq<char>, v: seq<char>) ensures Derivs(r, u + v) == Derivs(Derivs(r, u), v)` (`decreases \|u\|`), with `function Derivs(r: Re, s: seq<char>): Re decreases \|s\| { if \|s\| == 0 then r else Derivs(Deriv(r, s[0]), s[1..]) }` and a copy of `Deriv` as given code in the checkpoint file (bodyless lemma) | lemma-decreases, induction-false | 5.5 |
| X2d | statement-shipped (annotation) | `method SumNodeCounts(rs: seq<Re>) returns (n: nat) ensures n == SumNC(rs)`, with `SumNC` defined from the back (`SumNC(rs[..\|rs\| - 1]) + NodeCount(rs[\|rs\| - 1])`), the loop and its `decreases` given, the invariant and the one slice fact missing | invariant | 5.5 |
| X1v | statement-shipped | `proof fn lemma_derivs_append(r: Re, u: Seq<char>, v: Seq<char>) ensures derivs(r, u + v) == derivs(derivs(r, u), v)` (`decreases u.len()`), `derivs` and `deriv` given in `exit.rs` | lemma-decreases | 5.5 |
| X2v | statement-shipped (annotation) | `fn sum_node_counts(rs: &Vec<Re>) -> (n: u64) requires sum_nc(rs@) <= u64::MAX ensures n == sum_nc(rs@)`, the loop given, the invariant missing | invariant | 5.5 |

References: X1 `if |u| > 0 { assert (u + v)[0] == u[0]; assert (u + v)[1..] == u[1..] + v; DerivsAppend(Deriv(r, u[0]), u[1..], v); } else { assert u + v == v; }` (the recursive call changes the first argument: the statement must hold for every `r`, which is the item's point); Verus the same with `(u + v).drop_first() =~= u.drop_first() + v`. X2 `invariant 0 <= i <= |rs| && n == SumNC(rs[..i])` with `assert rs[..i + 1][..i] == rs[..i];` (Verus also the bound `n <= sum_nc(rs@)` through a monotonicity fact, which the author gives as a given lemma in the checkpoint file). **Shared-code check (F3):** none of these shares code with R02–R05's holes or worked examples, nor with R06's T1 and W2. The nearest earlier shape is R01.H2 `CountCharAppend` (a recursion over the first character of `u + v`), outside F3's range and a different object (an iterated function returning a term, equality of terms, a recursive call that changes another argument). The earlier X1 (`StarFreeBackwards`) was R02.H3 with `Nullable` replaced by `StarFree`, which the review flagged as only weakly unseen. Gate pending for all four.

### 7.4 Agent (decomposer)

Top statement `BackwardsCorrect` (spike `MirrorCorrect`). The reference decomposition (Dafny spike, all verified): `BackwardsStrLength`, `BackwardsStrAppend`, `BackwardsStrInvolution`, `BackwardsInvolution`, `BackwardsSound` (by `decreases r, |s|`, using A1b's `StarOne` and `StarConcat` on the reversed parts), then the equivalence from soundness twice. Under R06's proposed `manual-lemma-induction`, `BackwardsInvolution` and `BackwardsStrLength` need their recursive calls written (they verify empty only under automatic induction), so the agent cannot skip them silently. Verus: pending spike (no `backwards` in the Verus spike); fallback `CatAltDistrib`: two directions, each a split pick and a case on the `Alt`; no helper needed, so the decomposition is shallow and the follow-up then asks for the agent's case tree instead; it needs its own reference before it replaces the Verus statement (PLAN §0).

### 7.5 Cards

C5d (recognise, induction-auto): states Dafny's automatic induction on the default setting and what `{:induction false}` turns off; no prediction. C6dv: `calc` in both languages (Dafny `calc { … }` with step hints; Verus `calc! { (==) … }` with `{ hint }` blocks).

### 7.6 Written problems

The flagship: the paper proof of the `Cat` case, graded on finding that the `Alt` branch's right disjunct needs "`a` is nullable, so `a` matches the empty string", and on naming where that fact comes from (A1b's `NullableCorrect`, given) and why it applies. The matcher's invariant as an IH: state the invariant and prove it by induction on `i`, then say where the post-loop fact needs the same fact.

### 7.7 Minutes (revision)

The review found the flagship under-budgeted (40 per language for 50 and 75 proof lines, plus a re-proof of `NullableCorrect` that A1b now removes). New: H1d 60, H1v 68 (+48). Paid by: H5 dropped (−12), predictions 17 → 14, worked 36 → 30, setup 10 → 8, reading 65 → 60, matcher loop 30 → 24 (its own proof is about 4–6 lines per language once the call is given), H3 2 × 6 → 2 × 5, agent follow-up 25 → 22, the IH paper problem 15 → 10, bench 23 → 20, calib 10 → 9. Total unchanged at 462. Hole minutes D 89 / V 97.

## 8. Disjointness reasoning (PLAN §5)

- **Names checked by hand** against the Q exercise files (every declaration name in `dafny/Q/` and `verus/q/`, listed 2026-10-07) and the Lean R01–R06 exercise files (`LeanLearn0/R0[1-6]*.lean` in the learner checkout, declaration names only; no Lean solution was read). Hits that forced renames: `Size`/`size`, `Rev`/`RevRev`/`RevAppend` (Q), `size`, `reverse`, `reverse_append`, `reverse_reverse`, `mirror_mirror` (Lean). Q's decimal parser (`is_digit`, `parse_digit`, `ParseTwo`, `Digit`, …) moved R01 off digits. Near names kept: Q06's `mid`/`MidBetween` vs R01's `Midpoint` (different keys); Q's `Count`/`count` vs R01's `CountChar` (different keys); Q's `Clip` avoided (no `Clamp` in R).
- **Shape overlaps** (listed, not caught by names): R01.H2 (`CountCharAppend`) and Q's append lemmas (`ToNatAppend`, `LimbSumAppend`): the generic "a recursive measure distributes over `+`" genre, different objects, no renaming transfer; R02.H2/H3 structural lemmas vs Lean's `size_mirror`/`mirror_mirror`: the involution itself (`BackwardsInvolution`) is kept out of the learner's holes (it is an agent helper in R06) for this reason.
- **The Q08.P1dv boundary** (PLAN §8 R9) and its replacement (§4.1 above).
- **W-costs and test-out.** The 347 min of PLAN §1.4 (362 before the review dropped R05's row, which had no T items) are an [A] split of design §8.2's "≈ 119 h with Q-credit" (≈ 6 h; 124.9 − 5.8 = 119.1): R01's 72 min is W2's "≈ 1.2 h"; R11's 30 is W5's; the rest is spread over the other waivers' R homes by the size of the section a Q-credit learner already knows.

- **Lean R07–R16 names (revision).** Declaration names only, from the learner checkout's `LeanLearn0/R07*–R16*.lean` exercise files. Hits on R's planned names: `Step` (Lean R11), `compile`, `compile_correct`, `compile_correct_gen` (Lean R16) → A5's `Advance`, `Emit`, `EmitCorrect`, `EmitSound`, `EmitComplete`, `EmitProg` (Verus `emit`, `emit_into`, `emit_prog`). Near names kept: Lean `Instr` vs R `Inst` (different keys; if DVR0 lists `Instr` as a curated *type*, rule (ii) does not fire on `inst`); Lean `run`, `run_append` vs R `pike_run` (different keys); Lean `check` vs R `CheckDeriv`/`check_deriv` (different keys); Lean R14's `append_assoc` vs R's `CatAssoc` (different keys). Other Lean R07–R16 names (`infer`, `preservation`, `progress`, `Value`, `encode`, `decode`, `Sorted`, `merge`, `insertionSort`, `Vect`, `Monoid`, `constFold`, …) have no R counterpart. DVR0 adds them to `scripts/avoid.curated`.
- **R09's bounds (revision).** The review's first fix (ship the spike's digit-run parser in A3 as given code) is **rejected**: the parser is Q05.H5v's answer renamed (a loop over the digits with checked multiply-and-add, `Overflow` exactly on an all-digit prefix above the machine maximum), so a given copy would put a Q answer in a learner-visible R file (PLAN §2.1 rule 4, both directions). The review's second fix is adopted: single-digit bounds (`{n}`, `{n,}`, `{n,m}` with `0 <= n <= m <= 9`), so no decimal parser exists in R; R01's overflow lesson is harvested instead by the **expansion budget**: the lowered size (`NodeCount(r)` times the number of copies, nested repetitions multiplying) checked against a cap without overflow, by the division idiom (`copies <= CAP / NodeCount(r)`), a different object and idiom from Q05's. R09's holes: the bound checks (`n <= m`, the digit), the budget, the error positions, the lowering's correctness (`RepCorrect` and helpers, from the spike's references). Multi-digit bounds become a catalogued deviation from the `regex` crate (ours: a positioned error at the second digit) for R15. The spike's deviations (9)–(11) about the 1000 cap and `u32` overflow are retired with the cap.
- **Proposed waivers W15–W19 (revision).** W15 stage attribution (Q03.P6dv; Q12's stage specimens) → R13: R13 keeps it on `--log` evidence per fake green. W16 refute → repair → prove (Q15.H2d/H2v) → R06.H3/H4: cost "derive the repair from the counterexample"; R06's object is the `Star`-unfolding claim, whose weakest hypothesis is a disjunction (a stronger lesson than "smallest change"). W17 possible/impossible crate tasks (Q18's Lab 3) → Lab γ: R's impossible kinds differ (below). W18 card contamination audit (Q15's Lab 2) → Lab β. W19 the tracked-map arena (Q14.H5v, Q17.H2v) → R11, unnecessary if the Q lane moves Q14.H5v to a `PPtr` list; R keeps the map arena because the Verus spike proved it end to end (`arena_match` = `matches`).
- **Owner tags against Q10–Q18 (revision).** Every Q10–Q18 prediction row of `QPLAN.md` was read against R's five tags: only Q12.P5d/P6v cross one (later-stage failures; the Q lane's fix). Q13.P1dv vs R01.P3d/P4v and Q09.P2dv vs R05.P3dv are recorded as distinct (PLAN §5.1). In the other direction, R's predictions were read against Q's tags and against Q's genre homes: R04.P5dv's Verus column (hole visibility, Q01.P10dv) and R05.P3dv (error counts, Q07.P7d[a]) were the only crossings, both replaced.

## 9. Leak review of `PLAN.md` (this lane, before hand-off)

Removed or reworded while writing: "a strengthened `requires` breaks callers far away" (R03 record; answered R03.P1d/P2v's shape); "R02's `NullableCorrect` (← the helper the `Cat` case needs)" (R06 record; answered the flagship's written problem); P3dv/P6dv of R06 first drafts (their docstring code would have held H1's `Star` case and H3's claim); R03's P scenarios first used `ClassRange`/`ClassUnion` (hole targets), now `ClassSingle`/`ClassInsert`/`ClassEmpty`; R05.P1d first framed as "a first attempt at `Cat` associativity" (its passing labels would have been H1's facts), now neutral slice facts; R06.P4d's first draft named `Nullable` and "the proof steps as given in H2's reference shape". PLAN states no tool outcome of any prediction: P-items give scenarios and answer forms only, and the R-owned surprises are named, not described.

**Revision round.** Reworded in `PLAN.md` while folding in the spikes and the review: R06's record no longer says the paper proof "reveals the missing helper lemma" or that the decomposition tree shows a "helper lemma found on paper"; A1b's row lists its facts without saying which R06 item uses which; the flagship's minute line gives the band, not the reference sizes; R16's exercises line no longer gives the spike theorem's lemma count; W16's R-object cell no longer names the empty string; Lab γ's impossible kinds moved here (§11); the §5.1 note on Q12 names the crossing, not the stage Q12's specimens answer; §2.5's A1b item no longer describes `CatAssoc`'s behaviour under automatic induction. New text states no prediction outcome: R04.P6dv, R05.P3dv and R06's new items appear with scenarios and answer forms only.

## 10. Plan review: dispositions (R and both-track issues)

| review item | disposition | where |
|---|---|---|
| Blocker 3: R06 needs R02's `NullableCorrect` (and the decomposer R05's `StarOne`/`StarConcat`) with no lawful layer | **applied**: new layer A1b declared by R06, imported by R06–R16, re-supplying `NullableCorrect`, `CatEpsLeft`/`CatEpsRight`, `CatAssoc`, `StarOne`, `StarConcat`; A2 now re-supplies only the class API and the `Deriv` family; F4 updated; the paper problem's discovery stays the `Cat` case's need for `NullableCorrect` | PLAN §2.2–§2.4, §6.6; §7 here |
| Blocker 4 analogue for Lab γ (crate tasks handing the capstone's statements) | **applied** (not raised for R, applied by symmetry): Lab γ's tasks avoid the emitter, simulation and jump threading, and unpack only after R16's statement sha is committed | PLAN §4.3 |
| Major: line-count convention | **applied**: one rule in PLAN §0 (proof lines, exec code excluded, invented statements added); the spike counts already follow it | PLAN §0 |
| Major: fallbacks with no reference carry minutes | **applied**: PLAN §0's fallback rule; R11's arena fallback, R16's jump-threading line and R06.A1v's fallback carry nothing until their four results exist | PLAN §0, §3 R11/R16, §6.6 |
| Major (b): R04.P5dv's Verus column is hole visibility | **applied**: R04.P5d Dafny-only; new R04.P6dv on regex objects | PLAN §6.4; §5.1 here |
| Major (c): R05.P3dv repeats Q07.P7d[a] | **applied**: replaced by a repetition-determinism question; C5dv retargeted | PLAN §6.5; §6 here |
| Major (a): Q12.P5d/P6v cross R's tag | Q lane's; **recorded** and asked (PLAN §8 R18); the owner check was re-run against Q10–Q18 | PLAN §5.1 |
| Major: shared genres without waivers | **applied** as proposed waivers W15–W19 with costs; R06.H3/H4 retargeted to R's own `Star` object; Lab γ's impossible kinds diversified; W19 conditional on the Q lane | PLAN §5.4, §4.3 |
| Major: R09's number parser is Q05's renamed | **applied, with the review's first option rejected** (a given copy in A3 would leak Q05.H5v's answer, rule 4); single-digit bounds and an overflow-free expansion budget instead | PLAN §3 R09, §5.5; §8 here |
| Major: lab validity (Lab 1 analogue) | **applied to Lab α**: task forms must fail under maximal automation, the lab gate refuses added lever attributes, seeded stratified Claude subset, disjoint Qwen seeds per arm | PLAN §4.3 |
| Major: generation settings and per-arm cost | **applied** to α, β, γ: the pre-registration's field list | PLAN §4.3 |
| Major: hidden truth in the loop (Lab 2 analogue) | **applied to Lab β**: no oracle or hidden verdict inside a delivery loop; `roundtrip` on the pinned Qwen, counted | PLAN §4.3 |
| Major: R lab budgets (zero runs/calls, no sentinels, α over 10 GPU-h, Claude total over ≈ 1,700) | **applied**: decomposed arithmetic, proposed registry budgets R12/R15/R16, α at 4,800 Qwen and 100 Claude calls, six-lab Claude total 1,690 | PLAN §4.3, §8 R16/R17 |
| Major: PLAN predates the spikes | **applied**: S1 closed except the Verus decomposer, S2 feasible, S3 closed; A3's re-supplies moved to A1b; A5's opaque `Accepts` and lemmas recorded; Verus trigger fixed; DVR0's reconciliation step written | PLAN §2.2, §2.5; §1.3–§1.4 here |
| Major: R06 and R16 minutes | **applied**: R06's flagship 60 / 68, itemized within 462; R16's correctness split into four 45-min items with layout lemmas given; jump threading gated until spiked | PLAN §6.6, §3 R16; §7.7 here |
| Major: learner-visible hints | **applied** to PLAN's R text (§9 above); the Q items are the Q lane's | PLAN §3 R06, §6.6 |
| Minor: R11's gated 45 minutes and the E0 `let tracked` problem | **applied**: the `Vec` fallback named, both carry minutes only with four results; the gate variant requested | PLAN §3 R11, §8 R15 |
| Minor: R04.H4's open definition | **applied in part**: Dafny depends on QPLAN §30 Q52; the Verus request is **not needed**, because `specfreeze`'s `open_bodies` rule for `uninterp` → `open` is already built (QPLAN §6 Q7, Δ120) | PLAN §8 R11 |
| Minor: R05's test-out row | **applied**: row dropped (347 min) | PLAN §1.4 |
| Minor: S8.vc-generator-soundness home | **applied** as a proposed `gap` (records lane) | PLAN §3 R11, §8 R16 |
| Minor: `fvh_r` CI rule and `roundtrip`'s calls | **applied** | PLAN §4.3 |
| Minor: A5/R16 names against Lean R07–R16 | **applied**: scan done (names only); `Step`, `Compile`, `CompileCorrect` renamed | PLAN §5.5; §8 here |
| Minor: R06.H4d shows the `Cat` split; R06.X1d is R02.H3d renamed | **applied**: H3/H4 retargeted at `Star` unfolding; X1 is now `DerivsAppend` | PLAN §6.6; §7.2–§7.3 here |
| Minor: Lab 1's Claude subset rule (analogue) | **applied** to every R lab (seeded, language-stratified subset) | PLAN §4.3 |
| Q-only items (Q11.H7d/H8d, Q16.H3d, Q18 Lab 3, Q14.H2v, intro minutes, L6, Q14's NL-off order, Q12.P3d, Q15's freeze reference, Q17.H1d, Q16/Q10 evidence, Q10.X1v, Q16's speed test) | not this lane's; untouched | — |

## 11. Band 2–3 notes from the revision (for DVR2 and DVR3)

- **R09.** Bounds are single digits; the expansion budget's reference uses the division idiom; `ClassItems` and `Counted` gain completeness clauses (the spike found that a trivial `Err` body satisfies their specifications). The Verus spike's `lemma_rep_range` (40 lines) and the Dafny `RepCorrect` (14, plus `CopiesSplit` 12 and `UptoCorrect` 38 as invented helpers) are the lowering items' references; the parser's fidelity rests on the oracle (spike V: termination, error position ≤ len and well-formedness are proved, not a grammar theorem); a printer round-trip theorem stays DVR2's choice (spike V's open question).
- **R11.** The arena (`rg_arena`, 14/14) is admitted only after `Arena::get`, `set` and `free_all` can be gate-tested (PLAN §8 R15); until then the `Vec`-backed fallback needs its own reference. `lemma_valid_sound` (25) and `lemma_valid_complete` (56; needs `hi <= usize::MAX`) are the Verus checker items' references; Dafny `CheckSound` (14) verifies empty under automatic induction, so it needs R11's manual-induction option or a lever; `CheckCompleteDirect` (27) is the hard Dafny item.
- **R10.** Given (not holes): `CatCongRight`, `CatCong`, `StarOfEps` (empty bodies verify under every setting). `StarCong` (12) verifies empty under automatic induction: it needs the lever on R10's option. Verus `lemma_mk_alt` is 1 line: a prediction or card candidate, never a minute-budgeted hole.
- **R16.** Items: soundness and completeness, Dafny and Verus, with A5's layout lemmas (Dafny `LayoutAlt/Cat/Star` 27 lines) and one-step lemmas given; Dafny soundness path 55 lines, completeness 46 plus the top theorem 18; Verus soundness 55, completeness 59 plus `lemma_vm_correct` 19. Jump threading: spike V only proved the arena rewrite's model update (`thread_one`), never language preservation, so it is gated (PLAN §3 R16). A Pike lockstep executor exists in Verus (`rg_rexc`: `add_thread` 43, `pike_run` 53, `lemma_closure` 19), not in Dafny; the Dafny mirror's scope is DVR3's.
- **Lab γ's impossible kinds** (author-only; PLAN §4.3 says only that they differ from QPLAN's Lab 3): two tasks whose frozen statement contradicts a frozen differential test against the `regex` crate, drawn from spike V's deviation catalogue (the lazy `?` after a quantifier, a multi-digit counted bound), and two whose frozen statement contradicts a frozen negative test of `rexc`'s CLI or printer. Their expected outcome: no claimed success is correct.
- **Lab β's roundtrip** runs on the pinned Qwen model; its judgments of Qwen's own deliveries are a disclosure item (the same model family on both sides).
