# L7 notes (DV5c L7 lane, as built)

> **Author-only.** The build record of layer L7: its files, its exact public API, the gate,
> audit and stability results, the probes behind them, and where the build differs from the
> plan. It names Q16-Q18 reference material only by appendix. Never quote, paraphrase or
> link any of it from a learner-visible file. The plan is `QPLAN.md` §19.1, §19.4-§19.7 and
> `Solutions/plans/Q10-Q18-author-notes.md` §1, A.5 (superseded by C.2) and A.6; this file
> records what was built on 2026-10-11 (authoring worktree at 5e5d3ee plus uncommitted
> changes) and where it differs.

Every result below was captured on the pins (Dafny 4.11.0, Verus 0.2026.09.27.3cf1832)
through the course wrappers (`scripts/vcheck`, `scripts/vaudit`), one solver job at a time,
under the wrappers' caps (Dafny 8 GB, Verus 16 GB), each inside `systemd-run --user --scope
-p MemoryMax=16G -p MemorySwapMax=0` (the lane's share). `free -g` showed 98-99 GB available
before every batch (31 GB needed); no job was killed. `DVL_SCRATCH=/tmp/dvl0-dv5c-l7/scratch`.
Logs and probes are archived under `~/.cache/dafny-verus-learn-0/author-probes/dv5c/l7/`
(`l7-final.txt`, `brit-d.txt`, `brit-v.txt`, `probe/`, `verus-probe/`, `ci-static.log`).

## 1. Files

| file | content | sha256 (as left) |
|---|---|---|
| `dafny/given/Q/QG_L7_BigNat.dfy` | `module {:disableNonlinearArithmetic} QG_L7_BigNat`, opens L1-L6; compiled `Shift`, ghost `MulAcc`, ghost `Times`; no lemma | `6f51ccc2345cfdcfd839e04c01213ceeb92d7420de72168b71b5728b8c8ecde5` |
| `verus/given/qg_bignat_l7/Cargo.toml` | package `qg_bignat_l7`; vstd pin and `qg_bignat_l1`-`l6` path deps; `build = false`; `verify = true` | `8d66f88153938e8282d2e02c2ee0610a23fba913abe9c833478b47030def53ab` |
| `verus/given/qg_bignat_l7/src/lib.rs` | `pub use qg_bignat_l6::*;`, `pub mod api; pub use api::*;`; private `lemma_sub_lift`, `pub fn big_sub`, `pub fn to_u64` | `1c2bddd4b7cfd874d2a4cb23c28ed37ed313692b283e5d176a7ec9bb92bf6376` |
| `verus/given/qg_bignat_l7/src/api.rs` | `pub trait BigNatCore: NatLike` (`minus`, `to_word`) and `impl BigNatCore for BigNat` | `c570ff153b6cfcbab29c31bd45d5c8891766dc7f84be24017015799db962b08a` |
| `MODULES.toml`, Q16's record (still `planned`) | one line: `imports = { "dafny/given/Q/QG_L7_BigNat.dfy" = "std", "verus/given/qg_bignat_l7/src/lib.rs" = "arithmetic", "verus/given/qg_bignat_l7/src/api.rs" = "arithmetic" }` | — |

Both layer files are frozen (guard rule 2f covers `*/given/**`), hold no hole, test, assume,
axiom or external code, and carry no pin or trust entry, as L1-L6. No twin (a layer has
none). `verus/Cargo.toml` is generated: `gen_units.py` adds `given/qg_bignat_l7` to the
workspace when the first of Q16-Q18 leaves `planned` (verified in the scratch copy: with Q16
armed, the generated workspace lists it). `vcheck` and `vaudit` call Verus per crate, so the
crate gates and audits without being a workspace member.

## 2. The public API (what Q16-Q18 import)

**Dafny**, `import opened QG_L7_BigNat` (beside L1-L6; std unit, `includes` glob
`../../../given/Q/QG_L7_*.dfy`):

```dafny
function Shift(s: seq<nat>, k: nat): seq<nat>                                   // compiled
ghost function MulAcc(a: seq<nat>, b: seq<nat>, acc: seq<nat>, k: nat): seq<nat> // decreases |b|
ghost function Times(a: seq<nat>, b: seq<nat>): seq<nat>                         // MulAcc(a, b, [], 0)
```

No `requires` on any of the three. Definitions as C.2 (`Shift` = `seq(k, _ => 0) + s`;
`MulAcc` = `acc` on empty `b`, else `MulAcc(a, b[1..], Add(acc, Shift(MulLimb(a, b[0]), k)),
k + 1)`; `Add` and `MulLimb` are L4's sequence functions). No lemma about any of them.

**Verus**, `use qg_bignat_l7::*;` (brings every L1-L6 name and `BigNatCore`; the crate lists
`qg_bignat_l1`-`l7` as dependencies; import tier `arithmetic`):

```rust
pub fn big_sub(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires a.wf(), b.wf(), a.to_nat() >= b.to_nat(),
    ensures r.wf(), r.to_nat() == a.to_nat() - b.to_nat();

pub fn to_u64(a: &BigNat) -> (r: Option<u64>)
    requires a.wf(),
    ensures r is Some <==> a.to_nat() < BASE,
            r is Some ==> r->0 as nat == a.to_nat();

// src/api.rs (re-exported at the crate root)
pub trait BigNatCore: NatLike {
    fn minus(&self, other: &Self) -> (r: Self)
        requires self.valid(), other.valid(), self.value() >= other.value(),
        ensures r.valid(), r.value() == self.value() - other.value();
    fn to_word(&self) -> (r: Option<u64>)
        requires self.valid(),
        ensures r is Some <==> self.value() < BASE,
                r is Some ==> r->0 as nat == self.value();
}
impl BigNatCore for BigNat { /* minus = big_sub, to_word = to_u64 */ }
```

`NatLike` (L4) supplies `valid`, `value`, `zero`, `from_word`, `plus`, `times_word`,
`compare`; `BigNat`'s `NatLike` impl is L4's. `lemma_sub_lift` is private to the crate (not
callable from Q16-Q18; probed, §4).

## 3. Results on the built files

| check | Dafny `QG_L7_BigNat.dfy` | Verus `qg_bignat_l7` |
|---|---|---|
| `vcheck --gate` | verified, 133 verified, 0 holes, 0 errors (the L1-L7 chain; L6's file alone gates at 130) | verified, 6 verified, 0 holes, 0 errors |
| `vaudit` (learner mode) | 0 findings | 0 findings |
| `vaudit --mode given` | 0 findings | 0 findings |
| `vaudit --check-trust` | — | 7 given crates, 0 trust entries, 0 findings |
| `vcheck --brittleness` | `--solvers`: 4.12.1 and 4.14.1 × seeds 1-3 all verified, `stable`; 114 symbols, widest spread L1's `ToNatAppendZero` (CV 13.9%, 4.14.1), nothing of L7's above it | seeds 1-3 verified, `stable`; 5 symbols, widest `to_u64` 17,779-22,300 (CV 9.4%) |
| module options | `{:disableNonlinearArithmetic}` (QPLAN §19.4); the only module in its file; std tier | `arithmetic` tier (uses `vstd::arithmetic::mul`) |

Static checks on the real tree: `check_course_map.py` OK (49 modules; imports 125 files) and
`--only vocab` OK; `gen_units.py --check` OK (31 units; the workspace unchanged while Q16-Q18
are planned); `avoid.sh` OK (0 hits); the leak-pattern verifier (README) OK over 15 modules,
1,482 public files, with three `exempt:` lines for `verus/given/qg_bignat_l7/src/lib.rs`
(one Q10 pattern, two Q13 patterns: L7 re-supplies those two answers, Δ130, rule 2's
exemption). `ci.sh --job coexist` PASS. `ci.sh --job static`: see §6.

Names: none of `Shift`, `MulAcc`, `Times`, `big_sub`, `to_u64`, `lemma_sub_lift`,
`BigNatCore`, `minus`, `to_word`, `api` is declared in L1-L6 (grep over both languages).

## 4. Probes (scratch copy `/tmp/dvl0-dv5c-l7/root`, Q16 set to `authoring` with its imports)

All in Q16's context (`scripts/vcheck --module Q16 <probe>`, the L1-L7 chain, Q16's unit
options), or as Q16's probe crate.

| probe | result | confirms |
|---|---|---|
| `wire.dfy`: L1-L7 opened with `Std.Arithmetic.Mul`, `Std.Arithmetic.DivMod`, `Std.Wrappers`; a compiled method calling `Shift`, a ghost function calling `Times`, an empty-body lemma `Times(a, []) == []` | verified, 135 | no name clash with the Std modules Q16-Q18 open; `Shift` compiled |
| `ref_a17.dfy`: author notes A.17 (Q16's Dafny references) with L6 added to its imports | verified, 137 | C.2's "137 after C.1" on the built layer |
| `plain_h1d.dfy`: A.17 with `MulCorrect`'s plain-induction body (§8.2) | failed, 136 verified, 2 errors: "a postcondition could not be proved on this return path", one per conjunct | the hard-tier rule's "plain statement known to fail" on the built layer |
| `ghost_times.dfy`: A.17 with `MulLoop`'s body `r := Times(a, b); MulCorrect(a, b);` | failed at resolve: "a call to a ghost function is allowed only in specification contexts" | blocker 2's fix holds: no compiled shortcut through `Times` |
| Verus probe crate: A.18 (Q16's Verus references) plus `wire.rs` (globs of `vstd::prelude`, `arithmetic::{mul, div_mod, power, power2, logarithm, overflow}`, `bits`, `seq_lib`, `cell`, then `qg_bignat_l7::*`; calls `big_sub`, `to_u64`, `BigNat::zero`, `plus`, `minus`, `to_word`, and a generic `fn<T: BigNatCore>`) | verified, 12 | A.18 verifies over the built L7; no clash with those vstd modules; the trait is usable generically |
| the same crate with a module calling `lemma_sub_lift` | failed at resolve: "cannot find function `lemma_sub_lift` in this scope" | the helper is private |
| the same crate with a false `assert(d.to_nat() == a.to_nat())` after `big_sub` | failed, 12 verified, 1 error "assertion failed" | the probe modules are really compiled and checked |
| **first form** (`pub fn sub`, as QPLAN and A.6 name it): `wire.rs` calling `sub(a, b)` | failed at resolve: `error[E0659]: sub is ambiguous` — "could refer to the function imported here: `use vstd::prelude::*;`", "could also refer to the function imported here: `use qg_bignat_l7::*;`" (`probe/verus-wire-sub-ambiguous.txt`) | the reason for the rename (§5) |

## 5. What in A.5 / A.6 (and QPLAN §19.4) did not hold, and the other deviations

1. **`sub` collides with `vstd::prelude::*`** (§4, last row). Every Q16-Q18 file starts
   with `use vstd::prelude::*;`, so a glob import of L7 made every call `sub(a, b)` a
   resolve error (E0659). Q13.H1v never met it because Q13 declares `sub` locally (a local
   item shadows a glob). Built as **`big_sub`**, after L4's `big_add`, which avoids vstd's
   `add` the same way (Δ157). `BigNatCore::minus` (a method, never ambiguous) is unchanged.
   QPLAN §19.1 rule 1, §19.4, §19.5 and §19.6 point 4 still say `sub`. **Needs confirmation**
   (the lane's report lists it as a decision).
2. **`lemma_sub_lift` is private**, where A.6 made it `pub`. QPLAN §19.4 lists only `sub`
   and `to_u64`, and §19.1 rule 1 has a layer re-supply only what a later item or layer
   calls; no Q16-Q18 design calls the lift.
3. **L7 Dafny opens L1-L6** (QPLAN §19.4: "imports L1-L6"); C.2's candidate opened L1, L2
   and L4 only. Verification is unchanged (A.17 verifies either way); the gate count is 133.
4. **Bodies.** `big_sub`'s body is C.5's (= Q13's twin) with its two one-statement proof
   blocks on three lines each, as A.6 wrote them, and without the twin's `// did:` and
   `// reference-only` markers (no given layer carries them); `to_u64`'s is Q10's twin
   verbatim. Comments and headers are neutral (Δ110: no item id, tier lever, measure or
   broadcast mechanism); the Dafny header names no property of `Shift` (the shift lemma is a
   statement the Q16 learner writes under F-H1d).
5. **`api.rs` is re-exported** (`pub use api::*;`), so `use qg_bignat_l7::*;` brings
   `BigNatCore` as it brings every lower layer's names; A.6 had `pub mod api;` alone, which
   would have needed `use qg_bignat_l7::api::*;`.
6. **`api.rs` needs its own import-tier line**: `check_course_map` refuses an undeclared
   given file ("undeclared course file escapes the tier check — declare it in its module's
   [module.imports] (a given layer: its first module's)"). QPLAN §26.6 already lists the
   three lines; this lane wrote them on Q16's planned record (a planned module may declare
   them: the checker passes), so that the tree's course map stays green before Q16 is armed.

Everything else in A.5/C.2 and A.6 held on the built files: the definitions and
specifications are verbatim, the gate counts match (Dafny 133 over L1-L7; Verus 6, A.6's
"6 verified"), Verus `to_u64`'s CV is the same 9.4%, and C.2's three Q16 probes reproduce.

## 6. Interactions found

- **`scripts/test_course_map.py`, two armed cases** ("armed: --only import-tiers" and "tiers:
  a prelude file may use the calc! macro") pin `import-tiers: 35 files` and now see 38: the
  three L7 lines sit on Q16's record while Q16 is `planned`, and the fixture's `plan_real`
  empties the imports (and `module_trees` drops the layer files) only of real modules past
  planned. This resolves itself the moment the Q16 lane arms Q16 (then Q16 is in
  `_real_later`). If Q16 stays planned at integration, the one-line fix is to let
  `_real_later` also return a planned Q module after Q04 whose `imports` is non-empty.
- The other `ci.sh --job static` failures in the shared tree at the time of the run belong
  to other lanes' uncommitted work: `check_single_route.py` (`harness/fvh/batch.py:9` names
  `opencode`) and `chapter_lint --all` (one problem each in Q13's and Q14's chapters).

## 7. DELTAS-ready text (for the records lane)

> ### Δ2xx · Layer L7 as built; Verus subtraction is `big_sub` — adopted (DV5c, 2026-10-11)
> - **Status:** the hard practice tier's layer, on Δ185's and Δ195's model, built before
>   Q16-Q18 are armed. Like Δ160-Δ205, it names no answer; the detail is in
>   `Solutions/plans/L7-notes.md`.
> - **Change:**
>   - **L7, Dafny:** `dafny/given/Q/QG_L7_BigNat.dfy`, `module {:disableNonlinearArithmetic}
>     QG_L7_BigNat` (std tier; opens L1-L6), with QPLAN §19.4's three definitions (`Shift`
>     compiled; `MulAcc`, `Times` ghost) and no lemma.
>   - **L7, Verus:** the crate `verus/given/qg_bignat_l7` (vstd and L1-L6; `build = false`,
>     `verify = true`; arithmetic tier): `src/lib.rs` with `big_sub` and `to_u64`, and
>     `src/api.rs` with `BigNatCore` and its `BigNat` impl, re-exported, so
>     `use qg_bignat_l7::*;` brings every L1-L7 name. The borrow-lift helper is private.
>   - **The rename.** QPLAN §19.4's `sub` is built as `big_sub`: a glob import of the layer
>     beside `use vstd::prelude::*;` made `sub` ambiguous with vstd's (E0659, probed), as
>     `add` was for L4 (Δ157). QPLAN §19.1 rule 1, §19.4, §19.5 and §19.6 read `big_sub`.
>   - **Registry.** Q16's record (still planned) declares the three L7 files' import tiers
>     (QPLAN §26.6's lines); `gen_units.py` adds the crate to the workspace when a module of
>     Q16-Q18 is armed.
>   - Both files are frozen (rule 2f), hold no hole, test, assume, axiom or external code,
>     and carry no pin or trust entry.
> - **Why:** the L7 lane's runs (16 GB scope, one job at a time): `vcheck --gate` 133
>   (Dafny, the L1-L7 chain) and 6 (Verus); `vaudit` 0 findings in learner and given mode;
>   `vaudit --check-trust` 7 crates, 0 entries, 0 findings; `--brittleness` stable (Dafny
>   both bundled Z3s × seeds 1-3, widest CV 13.9% on an L1 symbol; Verus seeds 1-3, CV
>   9.4%); probes in Q16's context: the plan's Q16 references verify over the built layer
>   (Dafny 137, Verus 12), the plain H1d attempt fails, a compiled call of `Times` fails at
>   resolve, no clash with the Std or vstd modules Q16-Q18 open; `check_course_map`,
>   `gen_units --check`, `avoid.sh`, the leak verifier and `ci.sh --job coexist` clean.
> - **Touches:** Δ130, Δ157, Δ173, Δ185, Δ195; QPLAN §19.1, §19.4-§19.6, §26.6; the files
>   above; `MODULES.toml` (Q16's imports).
> - **Owner:** this round's L7 lane.
> - **Open** (owner, severity): the orchestrator: confirm the rename (minor); the Q16 lane:
>   arming Q16 clears `test_course_map`'s two import-tier counts (§6).
