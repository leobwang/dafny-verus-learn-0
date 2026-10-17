# Author notes for the DV0 BigNat spikes

> **Author-only. Never quote, paraphrase or link these pairings in a learner-visible file.** Learner-visible means everything outside `Solutions/` and the author archive, including `VERSIONS.md`, `docs/design/*` and `CLAUDE.md`. The pairings below answer predicts and give away proof strategy. Learner-visible files say only "closes with a single prover choice" or "see the author notes".

Written 2026-10-03 from the DV0 adversarial review (leak findings). Archive paths are relative to `~/.cache/dafny-verus-learn-0/author-probes/`. Source lines are in `Solutions/spikes/verus/qg_bignat_x/src/lib.rs` as of this date.

## 1. Verus prover-choice items (DELTAS Δ49; DV0-REPORT §5.3)

Gate modes: NL = the empty proof plus one whole-goal `assert … by (nonlinear_arith)`; BV = the same with `by (bit_vector)`. All other empty-proof modes (E0, E0H, E1, E2, EC, EM) fail for both items.

| item | proof lines | NL | BV | reference proof | planned home |
|---|---|---|---|---|---|
| `lemma_limb_product_bound` | 5 | verifies 3/3 | verifies 3/3 | one `by (nonlinear_arith)` assert (line 150) | Q04 `nonlinear-arith` predict or card |
| `lemma_digit_split` | 2 | fails 3/3 | verifies 3/3 | two `by (bit_vector)` asserts (lines 163–164) | Q07 `bit-vector` predict or card |

- **Predict design note:** at the pin, `lemma_limb_product_bound` closes under **both** provers. A "which prover?" predict on it must either accept both answers or ask "which provers close it?". `lemma_digit_split` closes only with `bit_vector`.
- `split_u128` (exec, 3 proof lines; all gate modes fail) is the Q07 exec client of `lemma_digit_split`. `run3/summary/bands.json` groups them as "Q07 bit-vector site" (5 proof lines, intro band).
- Evidence: `spike-verus/run3/summary/table-rl2.txt`, `gate-rl2.json` (NL rows), `gate-rl2-EC-BV.json` (BV rows), `bands.json` (homes "Q04 nonlinear-arith site" and "Q07 bit-vector site").

## 2. `to_u64` and the opaque-`weight` lever (DELTAS Δ48)

- While L3 `weight` was transparent, `broadcast use group_bignat_bounds` alone closed the empty proof of `qg_bignat_x::to_u64`: E1, E2 and EC all verified, 3/3 seeds, while E0, E0H and TRIV failed. Evidence: `spike-verus/run3/pre-lever-transparent-weight/NOTE.txt`, and its `summary/gate-rl2.json` and `gate-rl2-EC-BV.json`.
- With `weight` opaque, every mode fails 3/3 (`run3/summary/table-rl2.txt`). The shipped proof of `to_u64` calls two of the group's lemmas explicitly and reveals `weight` (source lines 36–38).

## 3. Q13 `sub` line band (DELTAS Δ53; DV0-REPORT §5.4)

- As shipped, `sub` + `lemma_sub_lift` is 38 proof lines, in the intermediate band 15–45 (`spike-verus/run3/summary/bands.json`). The shipped `sub` uses `broadcast use group_bignat_bounds;` (line 97).
- Before the "sub trim" it measured 47, above the band (`spike-verus/run3/final-v1-before-sub-trim/summary/bands.json`). The Verus spike lane reported that the trim replaced explicit bound-lemma calls with that `broadcast use`. So Q13's band status depends on whether the learner reaches for the L3 group.

## 4. Archive copies of spike sources

The author probe archive holds copies of the spike sources: the inputs of the Verus gate variants and reference runs under `spike-verus/`. The archive is the spec §7.1 "author probe archive" (`~/.cache/<course>/**`), which the fourth canonical deny rule makes unreadable in study mode, so these copies are acceptable (DELTAS rules, orchestrator decision of 2026-10-03).

## Std near-answers (Δ35)
- `Std.Arithmetic.LittleEndianNat` instantiates at `BASE = 2^64` in a two-line refinement; its `SeqAdd`/`SeqSub` with their correctness lemmas are near-answers for the Dafny L4 `Add` and L5 `Sub` items (spike `spike-dafny/std-le-shortcut`). The std-tier import allowlist therefore excludes it from BigNat files unless an item uses it deliberately as search-then-name.
