# Q09 rubric — Internals III: brittleness, forensics, gate core

> **Consumers:** `/grade-paper Q09` (B1–B4), `/review-code Q09` (Gate, Code-review focus), and you, after `/contract Q09` (the audit debrief), after you write contract v1 and after you write `EVAL.md` v1 (their self-reviews). Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q09 --check` has recorded every Q09 prediction (the ten forensic deliveries included) and T1's first try (the test-out is closed book, and C3 below reviews it).

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q09_solutions.tex  sha256 03a96f23be42e3a79f4cc5c081f06a80c5b20175671c19916736ac03c5c5ad81 — the written track's reference (B1–B4)
paper/Q09_problems.tex  sha256 5a57b3eafb918b007324a77058abd1f23c14b4b8e0118e667c36eb845c3985cb — the problems these lines grade, with the card's pinned range
Solutions/dafny/Q/Q09_InternalsIII/std/Q09_InternalsIII.dfy  sha256 874dbba6802ec3830ffa4970a1d01a4e075481ade1ab00e9c2cadf3d5120c330 — the Dafny half of the code review (the repair item)
Solutions/dafny/Q/Q09_InternalsIII/std/Q09_Triggers.dfy  sha256 78989250a7fe3576d45cb8837cd9e56352543924a2d12b7d50e453956afdb6ae — the Dafny test-out of the code review
Solutions/verus/q/q09_internals_iii/src/lib.rs  sha256 e2108e24f39b91baa16271c83bacb71e76bef8e05021fd03278934a938db6dce — the Verus half of the code review
Solutions/harness/q/fvh_q/gate/core.py  sha256 a781a7217c4bf42f73b32151acd404db69870c7043ebe5b7152c07e4998fef5e — the Python half of the code review (the gate core)
Solutions/dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy  sha256 44c69fe7deaa1ceb95ac03219fddcccb5bcdd0c28bcc9cca5b7a6c0783486d46 — the reference delivery behind the audit debrief, Dafny
Solutions/verus/q/q09_internals_iii/src/agent.rs  sha256 b7d494775f8251a78f8db7fe6bc38c3ea3d5041b14722b4876810c0706362ba5 — the reference delivery behind the audit debrief, Verus

## Verifier anchors

Every probe goes in `instructor/scratch/`, one job at a time; the output is pasted verbatim. Verifier probes run through `scripts/vcheck`, `scripts/vaudit` and `scripts/specfreeze`. The statistics of B1 and B2 are recomputed by an executable check in the course's third language: the probe below, run by the harness's own Python on the pinned lock, `uv run --directory harness python3 ../instructor/scratch/probe_stats.py B<n>`. It calls the frozen `fvh.stats` for the end values and recomputes each step from the formula the problems file prints. Grading by eye is not recomputation.

- **Probes A–B** (B1, B2, one file). Write `instructor/scratch/probe_stats.py`, fill the `LEARNER_<problem>` table of the problem you grade with the numbers exactly as the answer writes them (`None` where it gives none; rates as decimals, counts as plain numbers), and run it with that problem's label:

  ```python
  # Probes A-B (Q09 B1, B2): your numbers against a recomputation, step by step.
  # Fill the LEARNER_<problem> table of the problem you check, with the numbers
  # exactly as the answer writes them (None where it gives none), then run from
  # the checkout root, one problem at a time:
  #     uv run --directory harness python3 ../instructor/scratch/probe_stats.py B1
  # Each step is recomputed twice: "carried" from YOUR earlier values (a step that
  # differs there is where an error entered) and "fresh" from the problem's
  # numbers (a step that agrees with carried but not with fresh inherited an
  # earlier error). The last lines are fvh.stats on the problem's inputs.
  import math
  import sys

  sys.path.insert(0, ".")  # uv run --directory harness runs in harness/, where fvh lives
  from fvh import stats  # noqa: E402

  # --- B1: n = 40 tasks per arm, p0 = 0.3, z_a = 1.96, z_b = 0.8416 ------------------------
  LEARNER_B1 = {           # <- your B1 numbers
      "p0q0": None, "var_term": None, "root": None, "z_sum": None, "delta1": None,      # (a)
      "p1": None, "pbar": None, "root_a": None, "root_b": None, "n_at_delta1": None,   # (b)
      "mde": None, "n_at_mde": None,                                                   # (b)
      "n_at_10pp": None,                                                               # (c)
  }

  # --- B2: the 4.12.1 rows 38400, 45900, 66300; EVAL v1 with 17 of 22 stable ---------------
  LEARNER_B2 = {           # <- your B2 numbers
      "mean": None, "sum_sq_dev": None, "variance": None, "sd": None, "cv": None,      # (a)
      "wilson_lo": None, "wilson_hi": None,                                            # (c)
  }

  REL = 0.002   # relative tolerance: three significant figures, with rounding carried through


  def close(a, b):
      return abs(a - b) <= REL * max(1.0, abs(b))


  def report(rows):
      """rows: (step, yours, carried, fresh). Returns the number of steps where an
      error entered."""
      entered = 0
      print(f"{'step':<14}{'yours':>16}{'carried':>16}{'fresh':>16}  verdict")
      for step, yours, car, fr in rows:
          if yours is None:
              print(f"{step:<14}{'-':>16}{'-':>16}{'-':>16}  not given")
              continue
          if not close(yours, car):
              verdict = "ERROR ENTERS HERE"
              entered += 1
          elif not close(yours, fr):
              verdict = "inherited"
          else:
              verdict = "ok"
          print(f"{step:<14}{yours:>16.6g}{car:>16.6g}{fr:>16.6g}  {verdict}")
      return entered


  def n_required(delta, p0, za, zb):
      """The two-proportion sample-size formula the problem prints (tasks per arm)."""
      p1 = p0 + delta
      pbar = (p0 + p1) / 2
      ra = math.sqrt(2 * pbar * (1 - pbar))
      rb = math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))
      return p1, pbar, ra, rb, (za * ra + zb * rb) ** 2 / delta ** 2


  def b1():
      N, P0, ZA, ZB = 40, 0.3, 1.96, 0.8416
      L = LEARNER_B1

      def mine(key, value):
          return L[key] if L.get(key) is not None else value

      # fresh: from the problem's numbers
      pq = P0 * (1 - P0)
      var = 2 * pq / N
      root = math.sqrt(var)
      zs = ZA + ZB
      d1 = zs * root
      p1, pbar, ra, rb, nd1 = n_required(d1, P0, ZA, ZB)
      mde = stats.mde_two_proportions(N, P0)
      nm = n_required(mde, P0, ZA, ZB)[4]
      n10 = n_required(0.10, P0, ZA, ZB)[4]
      fresh = {"p0q0": pq, "var_term": var, "root": root, "z_sum": zs, "delta1": d1,
               "p1": p1, "pbar": pbar, "root_a": ra, "root_b": rb, "n_at_delta1": nd1,
               "mde": mde, "n_at_mde": nm, "n_at_10pp": n10}
      # carried: each step from the learner's own earlier values
      lpq, lvar, lroot, lzs = mine("p0q0", pq), mine("var_term", var), mine("root", root), mine("z_sum", zs)
      ld1 = mine("delta1", d1)
      lp1, lpbar = mine("p1", P0 + ld1), mine("pbar", (P0 + mine("p1", P0 + ld1)) / 2)
      lra, lrb = mine("root_a", math.sqrt(2 * lpbar * (1 - lpbar))), mine("root_b", rb)
      lmde = mine("mde", mde)
      carried = {"p0q0": pq, "var_term": 2 * lpq / N, "root": math.sqrt(lvar), "z_sum": ZA + ZB,
                 "delta1": lzs * lroot, "p1": P0 + ld1, "pbar": (P0 + lp1) / 2,
                 "root_a": math.sqrt(2 * lpbar * (1 - lpbar)),
                 "root_b": math.sqrt(P0 * (1 - P0) + lp1 * (1 - lp1)),
                 "n_at_delta1": (ZA * lra + ZB * lrb) ** 2 / ld1 ** 2,
                 "mde": mde, "n_at_mde": n_required(lmde, P0, ZA, ZB)[4], "n_at_10pp": n10}
      bad = report([(k, L[k], carried[k], fresh[k]) for k in fresh])
      print(f"fvh.stats.mde_two_proportions({N}, {P0}) =", mde)
      print(f"fvh.stats.mde_two_proportions({N}, {P0}, paired=True) =",
            stats.mde_two_proportions(N, P0, paired=True))
      print(f"n at delta1 = {nd1:.2f}; n at the fvh.stats value = {nm:.2f}; n at 0.10 = {n10:.2f} "
            "(the problem's formula, z_a = 1.96, z_b = 0.8416)")
      return bad


  def b2():
      ROWS = [38400, 45900, 66300]
      K, N = 17, 22
      L = LEARNER_B2

      def mine(key, value):
          return L[key] if L.get(key) is not None else value

      mean = sum(ROWS) / len(ROWS)
      ssd = sum((x - mean) ** 2 for x in ROWS)
      var = ssd / len(ROWS)
      sd = math.sqrt(var)
      cv = sd / mean
      lo, hi = stats.wilson_interval(K, N)
      fresh = {"mean": mean, "sum_sq_dev": ssd, "variance": var, "sd": sd, "cv": cv,
               "wilson_lo": lo, "wilson_hi": hi}
      lmean = mine("mean", mean)
      lssd, lvar, lsd = mine("sum_sq_dev", ssd), mine("variance", var), mine("sd", sd)
      carried = {"mean": mean, "sum_sq_dev": sum((x - lmean) ** 2 for x in ROWS),
                 "variance": lssd / len(ROWS), "sd": math.sqrt(lvar), "cv": lsd / lmean,
                 "wilson_lo": lo, "wilson_hi": hi}
      bad = report([(k, L[k], carried[k], fresh[k]) for k in fresh])
      print(f"deviations from the mean: {[round(x - mean, 2) for x in ROWS]}")
      print(f"CV {cv:.4f}: {'above' if cv > 0.20 else 'not above'} the 20% flag "
            "(population standard deviation over one solver's rows, as scripts/vcheck computes it)")
      print(f"fvh.stats.wilson_interval({K}, {N}) =", (lo, hi))
      return bad


  if __name__ == "__main__":
      which = sys.argv[1] if len(sys.argv) > 1 else ""
      run = {"B1": b1, "B2": b2}.get(which.upper())
      if run is None:
          sys.exit("usage: uv run --directory harness python3 ../instructor/scratch/probe_stats.py B1|B2")
      sys.exit(1 if run() else 0)
  ```

  Reading the output: each step's row shows your number, the step recomputed from your own earlier numbers (`carried`) and from the problem's numbers (`fresh`). `ERROR ENTERS HERE` marks the step whose operation is wrong: that row, quoted, is the exhibited instance. `inherited` marks a step done right on a wrong earlier value: it is not a second flaw. `ok` rows agree within a relative 0.2 %, which absorbs the problems' four significant figures. The probe exits 1 when an error entered. Its last lines run `fvh.stats` on the problem's inputs, and B1's last line evaluates the problem's sample-size formula at three values of `δ`, so a check by substitution can be compared with it.
- **Probe C** (B3, re-running a `DIAGNOSIS` row). Run each row's command as the row writes it, from the checkout root. `scripts/vcheck` and `scripts/vaudit` refuse a delivery whose first try is not recorded (H5); if they refuse, stop B3 and say so in one line. A row whose catch rests on a copy (a swapped conclusion, an added test, a sampled call) is rebuilt from the lines the answer says the copy changed: a Dafny delivery stands alone, so its copy runs as `instructor/scratch/probe.dfy` under `scripts/vcheck --gate instructor/scratch/probe.dfy`; a Verus delivery imports the given layers, so its copy runs as `instructor/scratch/probe.rs` under `scripts/vcheck --module Q09 instructor/scratch/probe.rs` (add `--gate` for the gate's form). A copy whose catch is `scripts/vcheck --test` on a Verus delivery cannot run from `instructor/scratch/` (`--test` takes a file, not a module probe, and a scratch file does not see the layers): grade that row on its pasted output, say so in the report, and do not mark it down for that. A sweep row re-runs as `scripts/vcheck --brittleness --solvers <delivery>` (Dafny) or `scripts/vcheck --brittleness <delivery>` (Verus). A companion the deliveries ship (a frozen statement, a witness caller) is named by its own path.
- **Probe D** (B4, the card pin). `sed -n '2852,2873p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B4 prints. Run it before grading any field.
- **Probe E** (Code-review focus C1–C3, a dead step). Copy the declaration under review, with its module's imports and its module attribute (the trigger file's module turns nonlinear arithmetic off for itself; copy that attribute onto the probe's module), into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`, delete the one line or block in question, and run `scripts/vcheck --module Q09 instructor/scratch/probe.<ext>`. Verified without it: the line is dead. Not verified: it is needed. A Verus probe imports the four layer crates as the exercise file does.
- **Probe F** (Code-review focus C1–C3, stability). `scripts/vcheck --brittleness --solvers dafny/Q/Q09_InternalsIII/std` and `scripts/vcheck --brittleness verus/q/q09_internals_iii`: the summary line ends with `stable`. A `differs` line names each symbol whose verdict varies.
- **Probe G** (Code-review focus C4–C5, the gate core). `scripts/vcheck --gate harness/q/fvh_q/gate/core.py` runs the frozen acceptance tests; it exits 0 and prints only the summary line when every test passes. The live run over the corpus's Q half (`cd harness && PYTHONPATH=q uv run python -m fvh_q.gate.core --half Q`, on the host, one instrument at a time, about five minutes) is the learner's own check, not an anchor: paste its last lines when the review cites it.
- **Probe H** (the audit debrief D4, nothing leans on a false lemma). Copy the delivered agent file to `instructor/scratch/probe.dfy` (or `.rs`), delete the declaration of each lemma the report names as false (keep its refutation), and run `scripts/vcheck --module Q09 instructor/scratch/probe.<ext>`. Verified with 0 holes: no other proof calls it. A resolution error naming the deleted lemma: a proof leans on it, at the line printed.

## B1 — The minimum detectable effect, by hand (hand-calculation; dimension: recomputation)

### recomputation
- **RC.a** — each step of (a) and (b) is written and names its formula (the problem lists the steps). A missing step whose later numbers are right is a gap (3). A score ≤2 quotes the Probe A row marked `ERROR ENTERS HERE`, with its `yours` and `carried` values; a row marked `inherited` is never a second flaw.
- **RC.b** — (b)'s detectability judgement follows from the answer's own `n(δ₁)` compared with 40; a judgement that contradicts the answer's own number is a flaw, quoted beside it. If every row of (a) and (b) reads `ok`, (a) and (b) are correct, whatever rounding was used: do not invent a flaw.
- **RC.c** — (b)'s `fvh.stats` value agrees with Probe A's `fvh.stats.mde_two_proportions(40, 0.3)` line, and the substitution check agrees with the `n_at_mde` row (it should land on the problem's `n`). A value that differs scores ≤2 with the probe line pasted.
- **RC.d** — (c)'s `n(0.10)` agrees with Probe A's `n_at_10pp` row. The two sentences say what a pre-registration of that lab states or changes before the run. Try to counterexample them: a sentence that treats a null result at this `n` as evidence of no difference, or that proposes changing the design after seeing results, scores ≤2, quoted beside Probe A's numbers. An answer with a correct number and no consequence is a gap (3).
- **RC.e** — (d)'s value agrees with Probe A's `paired=True` line, and its reason names a mechanism that the function's docstring supports. A reason that is false of the docstring (quoted beside it) scores ≤2; a reason that names no mechanism is a gap (3).

## B2 — Brittleness statistics (hand-calculation; dimensions: recomputation, correctness)

### recomputation
- **RC.f** — (a)'s steps agree with Probe B's rows. A score ≤2 quotes the row marked `ERROR ENTERS HERE`; the problem fixes the divisor and the rows to use, so a step that uses another is that row. The flag decision follows the answer's own CV against 20 %.
- **RC.g** — (c)'s interval agrees with Probe B's `fvh.stats.wilson_interval(17, 22)` line. The claim sentence carries `n`, the interval and a disclosure line; one of the three missing is a gap (3); a sentence whose numbers contradict the probe's line scores ≤2, the line pasted.

### correctness
- **CO.a** — (b)'s stability decision, the row it names and its two reasons hold of the problem's table and of chapter section 3.1's rule. Try to counterexample each: a decision that rests on the CV rather than on the verdicts, a row named that does not decide, or a reason for not pooling that is false of how `scripts/vcheck` computes a spread, scores ≤2, quoted beside the table row or the chapter's rule it contradicts. If the decision and both reasons survive, the part scores ≥3: do not invent a flaw.

## B3 — The forensic DIAGNOSIS (concept; dimension: correctness)

### correctness
- **CO.b** — (a) holds a row for each of the ten deliveries, each with the five columns filled. A missing row or column is a gap (3), not a flaw.
- **CO.c** — every catch reproduces: Probe C on the row's command (or its rebuilt copy) prints what the row says it printed. A row whose command, re-run, prints something else scores ≤2, with the re-run output pasted beside the row. The one instrument with no command is reading the statement: its evidence is the claim's line and the delivered statement's line, quoted side by side, and it holds when the gap it names is in those lines. A row that writes a reading of a tool ("the audit would flag it") instead of the tool's output is a gap (3) when the claim reproduces, a flaw when Probe C refutes it.
- **CO.d** — no two rows that catch a delivery name the same instrument (the form's rule 3; the instruments are the chapter's list). Two catching rows with one instrument score ≤2, the two rows quoted. Rows that catch nothing name no instrument as their catch.
- **CO.e** — no delivery that every instrument passes is accused. A row that accuses a delivery scores ≤2 only with the exhibit: Probe C on the row's own instrument printing a pass, pasted beside the row. A row's species-level reading that Probe C cannot settle either way is a gap (3), never a flaw.
- **CO.f** — the three judgement columns are consistent with the row's own evidence: a statement called untrue, a proof called invalid or a statement called less than its claim each points at something the row's output or a quoted line of the delivery shows. Try to counterexample each; a column that the delivery's own text contradicts scores ≤2, the line quoted with its number.
- **CO.g** — (b)'s second instrument catches the same delivery: Probe C on it prints a catch. A second instrument that, run, does not catch it scores ≤2 with its output pasted; "none would" is correct only when the answer's reason survives an honest attempt with the chapter's list. (c) lists, for each delivery the table calls healthy, instruments that were run, with their lines; a line that Probe C does not reproduce scores ≤2.

## The --post pass

Q09's written pair holds no informal-proof-first problem, so there is no blueprint to diff against your proofs: `/grade-paper Q09 --post` has nothing to re-score and writes no `paper-post` row. No `--report` pass either: Q09 has no lab, and `EVAL.md` v1 is your report, reviewed by you (the last section below).

## B4 — Paper card 07.2 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe D prints the hash B4 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled: task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact, each answering its own question. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with the pinned range (`cheatsheets.md` lines 2852–2873). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain (a run count, an interval, a cap, a cost, a release) scores ≤2 only by naming the field and the quoted absence: the range lines that state the setup or the results without it.
- **CF.e** — figures stay attached to what the range attaches them to: a count, a time or a cost given for the wrong run, model or target contradicts the table row or sentence it comes from, and CF.c applies. A claim the range itself reports as overturned (by its audit) is not the run's result: stating it as one contradicts the row that reports the audit.
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short; a field need not cover every fact the range offers. The card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.

## Gate

The mechanical preconditions of `/review-code Q09`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck --module Q09` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q09_InternalsIII/std`, `scripts/vcheck --gate verus/q/q09_internals_iii` and `scripts/vcheck --gate harness/q/fvh_q/gate/core.py` each exit 0 and print only the summary line. The agent files are not held to zero holes: after the contract run each is checked by its CONTRACT's own lines (the debrief's D2–D5).
- **A3 — audit.** `scripts/vaudit dafny/Q/Q09_InternalsIII/std`, `scripts/vaudit verus/q/q09_internals_iii` and `scripts/vaudit harness/q/fvh_q/gate/core.py` report no finding. No agent file has an `.audit` pin: a correct delivery leaves findings the CONTRACT counts (D5).
- **A4 — stability and forms.** Probe F prints `stable` for both units; no resource attribute appears anywhere in either unit.
- **A5 — slots, first tries, forms, budgets.** `scripts/firsttry.sh Q09 --report --strict` exits 0: every slot filled, recorded and enabled (the ten forensic switches included), every item's `form:` met (its `stable` sweeps included), and its `budget` field 0 (no resource attribute charged to an item's block, the exit files' blocks included once they are repaired).
- **A6 — statements unchanged.** `scripts/specfreeze --check Q09` reports no finding; it covers the gate core too, the four holes' signatures and the given parts (its dataclasses, `render` and `main`), as well as the proof, exit and agent files' statements.
- **A7 — diagnosis fixtures stay out.** The forensic deliveries `specimens/Q09/P6d.dfy.specimen` … `P15v.rs.specimen` and their two companions are evidence, not exercises: they are predictions and `DIAGNOSIS` rows (A5, B3), never repaired, finished or reviewed. The card demos under `specimens/Q09/card-*` are red by design (their failures are pinned). A2, A3 and A4 skip all of them, and so does every C line below. Any copy you made of a delivery is deleted once its row is written.

## Code-review focus — band: "library-conventions"

- **C1 — library facts called by name (H1d).** Each nonlinear step of the repair is a named library fact (or a short `assert` it supports), and you can say what each contributes. A call that Probe E shows dead is a finding at this bar; without that evidence, do not invent a flaw. No resource attribute, no blanket import or option added to make it fit (A4, A5).
- **C2 — splits on purpose (H1v).** Each `nonlinear_arith` step carries its own `requires`, names only the facts it needs, and is small; the item's form counts the steps. A `requires` clause that Probe E shows unneeded is a finding; a step that Probe E shows dead is a finding. If every step and clause is needed and Probe F prints `stable`, do not invent a flaw.
- **C3 — triggers on purpose (T1d, T1v).** The quantified step names its trigger explicitly, the trigger is a term that no instance of the step creates, and you can say which term of the proof fires it. Run Probe E on the quantified step and record what it shows: needed, or dead. A dead step is an observation at this bar, never a finding by itself (the items' `trigger` form checks presence, QPLAN §17.11); it becomes a finding only where your own comment or `EXPLAIN-BACK` says the proof rests on it. A trigger whose instances feed it again (the shape §3.4 repairs) is a finding, exhibited by a Probe F row that differs or runs out.
- **C4 — the gate composes the core and never reads a label (H3py–H5py).** `classify` and `gate` take no label and branch on nothing but instrument results and the delivery's files; every instrument runs through `fvh.tools.run` looked up at call time; the companions come from the delivery's files, either by the public layout written out or by composing `fvh.tools.command` (both are accepted); a killed, timed-out or refused run is never a `PASS`; `corpus_report` takes its interval from `fvh.stats`. Probe G is the anchor: a passing suite with none of these breaches has nothing to find. A re-derived interval formula, or an instrument re-implemented in your file, is a finding even when the tests pass, because statistics and instruments live only in the core.
- **C5 — completeness checks say what they check (H2py).** One reason per failing check, in the docstring's order, and `[]` only for a document a gate may trust. If Probe G passes and each reason names its field, do not invent a flaw.
- **C6 — intent stays in the shipped contracts.** Q09's statements ship frozen; A6 is the anchor. A changed `requires`, `ensures`, signature or given Python part is a finding at grade 1, whatever the verifier or the tests say.
- **C7 — names and dead code.** Any name you introduced says what it holds; no commented-out experiments and no unused helpers in your own lines. Prediction slots and their answers stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding, and so is a forensic delivery's slot.

## Audit debrief — after /contract Q09

Questions for you, after the two contract runs (one per agent file). Each is settled by the transcript, the artifact or a command, and none has a secret answer.
- **D1 — did your diagnosis come first?** `git log -- research/q09_bank.dfy research/q09_bank.rs` and the agent files' `DIAGNOSIS` blocks: the snapshot and the filled block were committed before the run started (the transcript's first message is later than the commit).
- **D2 — are the holes exactly the lemmas the report names false?** `scripts/vcheck --json <agent file>`: the `holes` list holds one entry per lemma the contractor's report names false, at that lemma (Dafny: its `ensures` line; Verus: its labelled assume line), and no other; every other lemma's `per_symbol` entry is `verified` (Dafny) or `no-error` (Verus).
- **D3 — is each named lemma refuted, and did the statements stay yours?** Each named lemma has a lemma under `REFUTATIONS` whose `per_symbol` entry (D2's run) is `verified` or `no-error`, and `scripts/specfreeze --against research/q09_bank.dfy dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy` (Verus: `research/q09_bank.rs` against `verus/q/q09_internals_iii/src/agent.rs`) reports no change. A refutation that only restates the lemma's statement with a `requires` added is not one: its `ensures` is the negation of the lemma's claim on concrete values.
- **D4 — does anything lean on a false lemma?** Probe H on each delivered file. A proof that calls a lemma the report names false verifies and proves nothing; record any line Probe H prints.
- **D5 — is the audit exactly the expected one?** `scripts/vaudit <agent file>` (learner mode, the CONTRACT's) reports exactly one finding per lemma named false, of a hole kind, on that lemma's line, and no other finding. Compare it with the contractor's last report of the same line.
- **D6 — did the diff stay in bodies and REFUTATIONS?** `git diff -U0 -- <agent file>` against the committed bank: every hunk is inside a lemma's body or the `REFUTATIONS` section; no statement, attribute or comment of `BANK` changed, and no helper was added outside `REFUTATIONS`.
- **D7 — who was right, you or the contractor?** Compare your `DIAGNOSIS` block with the delivery: for each lemma, whose call held, settled by the proof that verifies or the refutation that verifies. Where you disagreed, write in `AUDIT` what you had missed or what it had.
- **D8 — did it weaken, restate, assume or re-verify?** From the transcript: any edit that added a `requires`, changed an `ensures`, added an `assume`, an axiom or a resource attribute; and the number of `scripts/vcheck` runs between edits (name any stacked edits). Each moment goes into `AUDIT` with its place in the transcript.
- **D9 — which moment earns a rule?** Name one transcript moment, of this run or of a Q04–Q08 run, that deserves a rule in contract v1, and write it in the rule format of `CLAUDE.md`'s contract slot.

## Contract v1 — your own review

No skill grades contract v1: it is yours, written by hand with no AI session (chapter §10). These questions are for you once `### Q-v1 — Q09, <date>` exists below the learner marker of `CLAUDE.md`; each is settled by the file, the transcripts and a command, and none has a secret answer.
- **D10 — is each rule earned?** Each of the 3–6 numbered rules names the transcript moment it was earned by (run, file, and the moment), and the moment is in that transcript.
- **D11 — is each rule checkable?** Each rule says how it is checked: a command a third party can run, an audit line, or only a reader. A rule that claims a command which, run, does not check what the rule says is a finding against your own contract.
- **D12 — does "Done means" re-run?** Run the "Done means" line from a fresh shell on one of your Q09 agent files: it gives the same answer the transcript's final state should.
- **D13 — does v1 relax nothing?** Read v1 beside v0 and the fallback rules: where two disagree, the stricter one is the one a run must follow, and v1 says so.

## EVAL.md v1 — your own review

No skill grades this file: it is yours, written by hand (chapter §7). These questions are for you once the `Q-v1` section exists; each is settled by the file and a command, and none has a secret answer.
- **D14 — does the section hold the six items?** The claim with its population, the metric with its estimator, `n` with the measurement command, the exclusions, the cost, and the disclosure line (chapter §7's list).
- **D15 — does every number recompute?** Re-run, from a fresh shell, the sweeps the section names and `fvh.stats.wilson_interval` on its counts, and compare each number in the section with their output. A number they do not regenerate is a finding against your own report: fix the report or the command.
- **D16 — is the population honest?** `n` counts every hole you filled in Q04–Q09's Dafny files (exits included if the claim says so), and a resource-limit hit counts as unstable. Recount them from the files.
- **D17 — does the disclosure say what the interval covers?** The interval treats your proofs as a sample of proofs you write, on one machine, one solver pair and three seeds; a sentence that claims more (another machine, other solvers, other authors) is a finding.
