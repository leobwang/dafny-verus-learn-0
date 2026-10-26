# Lab α: notes beside the frozen frame

This file is not part of Lab α's frame. `STRATUM.toml` and `FREEZE.toml` are the frozen pre-registration: `FREEZE.toml` pins `STRATUM.toml` by sha256, and FREEZE's own sha256 is registered by the R12 pre-registration. Neither file is edited after the freeze. Nothing pins this file. Corrections to the frame's descriptive text are recorded here instead.

## R08 module paths after D92 (2026-10-25, DELTAS Δ310)

The R08 clusters' `source` strings in `STRATUM.toml` name the R08 reference as it stood when the corpus was admitted. D92 later moved the Dafny lemmas out of the engine modules: the engines became refinements the learner writes. The lemmas and their statements are unchanged. Only the module that holds each lemma changed.

| cluster | `source` names (frozen) | the lemma now lives at |
|---|---|---|
| `r08-ranges-class-law` | `R08_RangeStarEngine.RangesClassLaw` (R08.H1d) | `R08_RangeStarClassFact.RangesClassLaw` (R08.H1d) |
| `r08-parts-law` | `R08_AltSetEngine.PartsLaw` (R08.H2d) | `R08_AltSetLaws.PartsLaw` (R08.H2d) |
| `r08-alt-feed-law` | `R08_AltSetEngine.AltFeedLaw` (R08.H3d) | `R08_AltSetLaws.AltFeedLaw` (R08.H3d) |
| `r08-alt-final-law` | `R08_AltSetEngine.AltFinalLaw` (R08.H4d) | `R08_AltSetFinalFact.AltFinalLaw` (R08.H4d) |

The Verus names are unchanged: `lemma_ranges_set_law`, `lemma_parts_law`, `lemma_alt_feed_law` and `lemma_alt_final_law` are free functions in both versions.

The task forms `r08-alt-feed-law-d` and `r08-alt-final-law-d` still contain the pre-D92 given alternative-set engine, including its start law. Since D92 the learner writes that start law in R08.H4. The forms stay as admitted, under the declared later-tier overlap (DELTAS Δ294): Lab α comes after R08.
