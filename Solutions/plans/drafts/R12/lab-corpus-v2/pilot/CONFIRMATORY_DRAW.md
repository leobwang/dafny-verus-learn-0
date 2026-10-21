# Lab alpha confirmatory composition (the user's D54) — pre-registered rule

Written 2026-10-19 before the draw and before any confirmatory call (none is ever an author call).

1. **Pool.** The admitted clusters of `bench/local/r/labalpha/STRATUM.toml` (schema 2) at the
   freeze, sealed ones included, minus the five pilot clusters. The draw records the pool's two
   sorted id lists and the sha256 of their JSON.
2. **Regex.** Every non-pilot regex cluster is confirmatory (D54).
3. **Public fill.** K = 80. With n_regex regex clusters, 80 - n_regex public clusters are drawn by
   `random.Random("R12-labalpha-confirmatory-20261019:public").sample(sorted_public, 80 - n_regex)`.
4. **Descriptive subset** (plan section 3.7, the other two regimes): 12 regex and 8 public
   confirmatory clusters, `random.Random("R12-labalpha-confirmatory-20261019:descriptive-regex")
   .sample(sorted_confirmatory_regex, 12)` and `…:descriptive-public").sample(sorted_confirmatory_public, 8)`.
5. **Record.** The roles go into the stratum (confirmatory, descriptive flags; the rest unassigned)
   and the lists, seeds and pool hash into `bench/local/r/labalpha/FREEZE.toml`; the simulation cell
   of the drawn composition (`Solutions/plans/labalpha_power_sim.py cell`) with its output and the
   script's sha256 goes into the freeze too.
6. **No redraw.** The composition is fixed whatever any later admission brings.
