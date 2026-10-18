# Lab alpha pilot draw (DVR4 plan section 3.6; the user's D52) — pre-registered rule

Written 2026-10-18 before any pilot cluster is drawn and before any model call on the corpus.

1. **Pool.** The admitted clusters of `bench/local/r/labalpha/STRATUM.toml` (schema 2) at draw
   time: every cluster whose family record says `admitted` and whose tasks all carry a schema-2
   ADMISSION.json with the seven controls true, bound to the form's bytes. The draw records the
   pool as two sorted id lists (regex, public) and the sha256 of their JSON (`pool_sha256`).
2. **Eligibility.** Regex clusters with exactly two tasks (one Dafny, one Verus form), so the
   pilot keeps its registered arithmetic (3 x 2 + 2 = 8 tasks, 4 arms, 3 repeats, B = 10:
   960 Qwen calls); a cluster with more forms (r06-deriv-correct, four tasks) is not
   pilot-eligible and stays in the confirmatory pool. Public clusters split by language.
3. **Draw.** `random.Random("R12-labalpha-pilot-20261018:regex").sample(sorted_regex, 3)`;
   `random.Random("R12-labalpha-pilot-20261018:public-dafny").choice(sorted_public_dafny)` and
   `random.Random("R12-labalpha-pilot-20261018:public-verus").choice(sorted_public_verus)`.
4. **Record.** The five clusters get `role = "pilot"` in the stratum before the first pilot model
   call; they are excluded from the confirmatory sample (the freeze refuses any overlap).
5. **No redraw.** A drawn cluster is kept whatever the pilot shows; the pilot may revise only what
   section 3.6 allows (the hint-site granularity of forms, or B; never K downward, the estimand or
   the test).
