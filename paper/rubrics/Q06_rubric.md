# Q06 rubric — The machine and the verifier loop

> **Consumers:** `/grade-paper Q06` (B1–B5), `/review-code Q06` (Gate, Code-review focus), and you, after `/contract Q06` (the audit debrief) and after you write `EVAL.md` v0 and `TRUST.md` v0 (their self-review). Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q06 --check` has recorded every Q06 prediction and T1's first try (the test-out is closed book, and C1 below reviews it).

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q06_solutions.tex  sha256 c70fc240a2b30d75e7f94769b6699e3437ce5ec45848757d0b6af0ab7963e367 — the written track's reference (B1–B5)
paper/Q06_problems.tex  sha256 300beedbd92c5698a5786643e900880caaf83be73ae6085f01bdaa846c9e12f3 — the problems these lines grade, with the card's pinned range
Solutions/dafny/Q/Q06_Machine/std/Q06_Machine.dfy  sha256 c34a5001c1c6f02849dc6b64c763672193ab9920891177d51803b79ccab22882 — the Dafny half of the code review
Solutions/verus/q/q06_machine/src/lib.rs  sha256 ff7eef42ba5ef7f875501f2028b6bd52e3b73b59858a6acdfba102502cea6119 — the Verus half of the code review
Solutions/harness/q/fvh_q/q06_stats.py  sha256 6e3a77e0413c1ff3b74428971b65b0b8546f38308cd948a6f4695ece34a207ff — the Python half of the code review
Solutions/dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy  sha256 bdec8a0f8a9901ca3892cbe3cf4d2335a1dba3b90d1f8e476e5ea85018dc49a6 — the reference delivery behind the audit debrief

## Verifier anchors

Every probe goes in `instructor/scratch/`, one job at a time; the output is pasted verbatim. Verifier probes run through `scripts/vcheck`. The statistics of B1, B2 and B4 are recomputed by an executable check in the course's third language: the probe below, run by the harness's own Python on the pinned lock, `uv run --directory harness python3 ../instructor/scratch/probe_stats.py B<n>`. It calls the frozen `fvh.stats` for the end values and recomputes each step from the formula the problems file prints. Grading by eye is not recomputation.

- **Probes A–D** (B1–B4, one file). Write `instructor/scratch/probe_stats.py`, fill the `LEARNER_<problem>` table of the problem you grade with the numbers exactly as the answer writes them (`None` where it gives none; rates as decimals), and run it with that problem's label:

  ```python
  # Probes A-D (Q06 B1-B4): your numbers against a recomputation, step by step.
  # Fill the LEARNER_<problem> table of the problem you check, with the numbers
  # exactly as the answer writes them (None where it gives none), then run from
  # the checkout root, one problem at a time:
  #     uv run --directory harness python3 ../instructor/scratch/probe_stats.py B1
  # Each step is recomputed twice: "carried" from YOUR earlier values (a step that
  # differs there is where an error entered) and "fresh" from the problem's
  # numbers (a step that agrees with carried but not with fresh inherited an
  # earlier error). The last lines are fvh.stats on the same inputs.
  import math
  import sys

  sys.path.insert(0, ".")  # uv run --directory harness runs in harness/, where fvh lives
  from fvh import stats  # noqa: E402

  TOL = 0.002  # three decimals, with rounding carried through

  # --- B1: 17 of 20, z = 1.96 ------------------------------------------------------------
  LEARNER_B1 = {           # <- your B1 numbers
      "p": None, "z2_over_n": None, "denominator": None, "centre": None,
      "under_root": None, "half_width": None, "lo": None, "hi": None,
      "wald_lo": None, "wald_hi": None,
      "factor": None,      # (c): the growth factor of n you claim halves the width
  }

  # --- B2: n = 5 samples per task, k = 2 ---------------------------------------------------
  LEARNER_B2 = {           # <- your B2 numbers
      "t1": None, "t2": None, "t3": None, "pass2": None, "pass1": None, "plugin_t2": None,
  }

  # --- B3: the four tasks' records (from the problem's table) -----------------------------
  LEARNER_B3 = {           # <- your B3 (a) numbers
      "pass_rate": None, "success_share_of_records": None, "solved_at_some_attempt": None,
  }

  # --- B4: the 2x2 table on 30 tasks -------------------------------------------------------
  LEARNER_B4 = {           # <- your B4 numbers
      "rate_a": None, "rate_b": None, "b": None, "c": None, "p": None,
  }


  def report(rows):
      """rows: (step, yours, carried, fresh). Returns the number of steps where an
      error entered."""
      entered = 0
      print(f"{'step':<26}{'yours':>12}{'carried':>12}{'fresh':>12}  verdict")
      for step, yours, car, fr in rows:
          if yours is None:
              print(f"{step:<26}{'-':>12}{'-':>12}{'-':>12}  not given")
              continue
          if abs(yours - car) > TOL:
              verdict = "ERROR ENTERS HERE"
              entered += 1
          elif abs(yours - fr) > TOL:
              verdict = "inherited"
          else:
              verdict = "ok"
          print(f"{step:<26}{yours:>12.5f}{car:>12.5f}{fr:>12.5f}  {verdict}")
      return entered


  def b1():
      K, N, Z = 17, 20, 1.96
      L = LEARNER_B1

      def mine(key, value):
          return L[key] if L.get(key) is not None else value

      p = K / N
      z2n = Z * Z / N
      den = 1 + z2n
      centre = (p + z2n / 2) / den
      under = p * (1 - p) / N + z2n / (4 * N)
      hw = Z * math.sqrt(under) / den
      wald = Z * math.sqrt(p * (1 - p) / N)
      fresh = {"p": p, "z2_over_n": z2n, "denominator": den, "centre": centre,
               "under_root": under, "half_width": hw, "lo": centre - hw, "hi": centre + hw,
               "wald_lo": p - wald, "wald_hi": p + wald}
      lp, lz = mine("p", p), mine("z2_over_n", z2n)
      lden, lunder = mine("denominator", den), mine("under_root", under)
      lc, lhw = mine("centre", centre), mine("half_width", hw)
      lwald = Z * math.sqrt(lp * (1 - lp) / N)
      carried = {"p": K / N, "z2_over_n": Z * Z / N, "denominator": 1 + lz,
                 "centre": (lp + lz / 2) / lden, "under_root": lp * (1 - lp) / N + lz / (4 * N),
                 "half_width": Z * math.sqrt(lunder) / lden, "lo": lc - lhw, "hi": lc + lhw,
                 "wald_lo": lp - lwald, "wald_hi": lp + lwald}
      bad = report([(k, L[k], carried[k], fresh[k]) for k in fresh])
      print("fvh.stats.wilson_interval(17, 20) =", stats.wilson_interval(K, N))
      f = L.get("factor")
      if f is not None:
          lo1, hi1 = stats.wilson_interval(K, N)
          lo2, hi2 = stats.wilson_interval(round(K * f), round(N * f))
          print(f"(c) width at n = {N}: {hi1 - lo1:.4f}; at n = {round(N * f)} "
                f"({round(K * f)} successes): {hi2 - lo2:.4f}; ratio {(hi2 - lo2) / (hi1 - lo1):.3f}")
      return bad


  def b2():
      NS, K = 5, 2
      C = {"t1": 0, "t2": 2, "t3": 4}
      L = LEARNER_B2
      rows, fresh_vals, mine_vals = [], [], []
      for t, c in C.items():
          num, den = math.comb(NS - c, K), math.comb(NS, K)
          val = 1.0 if NS - c < K else 1 - num / den
          if L[t] is not None:
              print(f"{t}: c = {c}: C({NS - c}, {K}) = {num}, C({NS}, {K}) = {den}")
          rows.append((t, L[t], val, val))
          fresh_vals.append(val)
          mine_vals.append(L[t] if L[t] is not None else val)
      p2 = sum(fresh_vals) / len(fresh_vals)
      p1 = sum(c / NS for c in C.values()) / len(C)
      rows.append(("pass2 (mean)", L["pass2"], sum(mine_vals) / len(mine_vals), p2))
      rows.append(("pass1 (mean)", L["pass1"], p1, p1))
      plug = 1 - (1 - C["t2"] / NS) ** K
      rows.append(("plug-in, t2", L["plugin_t2"], plug, plug))
      bad = report(rows)
      print("fvh.stats.pass_at_k:", {t: stats.pass_at_k(NS, c, K) for t, c in C.items()},
            "pass@1:", {t: stats.pass_at_k(NS, c, 1) for t, c in C.items()})
      return bad


  def b3():
      records = {"t1": ["fail", "fail", "success"], "t2": ["success"],
                 "t3": ["fail", "success"], "t4": ["fail", "fail", "fail"]}
      L = LEARNER_B3
      first = sum(r[0] == "success" for r in records.values()) / len(records)
      flat = [x for r in records.values() for x in r]
      share = flat.count("success") / len(flat)
      some = sum("success" in r for r in records.values()) / len(records)
      print(f"tasks {len(records)}, records {len(flat)}")
      return report([("pass_rate", L["pass_rate"], first, first),
                     ("success_share_of_records", L["success_share_of_records"], share, share),
                     ("solved_at_some_attempt", L["solved_at_some_attempt"], some, some)])


  def b4():
      both, a_only, b_only, neither = 14, 1, 10, 5
      n = both + a_only + b_only + neither
      L = LEARNER_B4
      ra, rb = (both + a_only) / n, (both + b_only) / n
      b, c = a_only, b_only
      lb = L["b"] if L["b"] is not None else b
      lc = L["c"] if L["c"] is not None else c

      def exact(x, y, show):
          m = x + y
          terms = [math.comb(m, i) for i in range(min(x, y) + 1)]
          if show:
              print(f"b = {x}, c = {y}: C({m}, i) for i <= {min(x, y)}: {terms}; 2^{m} = {2 ** m}")
          return min(1.0, 2 * sum(terms) / 2 ** m)

      bad = report([("rate_a", L["rate_a"], ra, ra), ("rate_b", L["rate_b"], rb, rb),
                    ("b", L["b"], b, b), ("c", L["c"], c, c),
                    ("p", L["p"], exact(int(lb), int(lc), L["p"] is not None),
                     exact(b, c, False))])
      print(f"fvh.stats.mcnemar({b}, {c}) =", stats.mcnemar(b, c))
      big = 140 + a_only + b_only + neither
      print(f"(c) with 140 both: rates {(140 + a_only) / big:.4f} and {(140 + b_only) / big:.4f}; "
            f"fvh.stats.mcnemar({b}, {c}) =", stats.mcnemar(b, c))
      return bad


  if __name__ == "__main__":
      which = sys.argv[1] if len(sys.argv) > 1 else ""
      run = {"B1": b1, "B2": b2, "B3": b3, "B4": b4}.get(which.upper())
      if run is None:
          sys.exit("usage: uv run --directory harness python3 ../instructor/scratch/probe_stats.py B1|B2|B3|B4")
      sys.exit(1 if run() else 0)
  ```

  Reading the output: each step's row shows your number, the step recomputed from your own earlier numbers (`carried`) and from the problem's numbers (`fresh`). `ERROR ENTERS HERE` marks the step whose operation is wrong: that row, quoted, is the exhibited instance. `inherited` marks a step done right on a wrong earlier value: it is not a second flaw. `ok` rows agree within 0.002, which absorbs rounding to three decimals. The probe exits 1 when an error entered. Its last lines run `fvh.stats` on the same inputs; `fvh.stats` uses the exact normal quantile, which agrees with the problems' `z = 1.96` to the third decimal.
- **Probe E** (B5, the card pin). `sed -n '672,699p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B5 prints. Run it before grading any field.
- **Probe F** (Code-review focus C1–C4, a dead step). Copy the declaration under review, with the module's imports and the given definitions it uses, into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`, delete the one line in question, and run `scripts/vcheck --module Q06 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Not verified: it is needed. For a `reveal`, the same recipe with the reveal moved into an `assert … by` around the one fact that needs the body (Probe F′): verified means the wider scope was not needed.
- **Probe G** (Code-review focus C4, the suites). `scripts/vcheck --test dafny/Q/Q06_Machine/std` and `scripts/vcheck --test verus/q/q06_machine` run the H4 suites and the cards' tests. Every test passes, and the planted candidate's test is among them.
- **Probe H** (the audit debrief D4, a leaf's usefulness). Copy the delivered agent file to `instructor/scratch/probe.dfy`, add inside its module one lemma that calls each leaf once on concrete arguments, and run `scripts/vcheck --module Q06 instructor/scratch/probe.dfy`. A call that verifies shows that the leaf's `requires` can hold. A call that does not verify is a verdict of kind 2, not a refutation: the finding needs Probe H′, a lemma in the same file whose `ensures` is the negation of the leaf's `requires`, over the leaf's parameters, which verifies (a verified refutation: no argument can ever meet it).

## B1 — A pass rate and its interval (hand-calculation; dimension: recomputation)

### recomputation
- **RC.a** — each step of (a) is written and names its formula (the problem lists the steps). A missing step whose later numbers are right is a gap (3). A score ≤2 quotes the Probe A row marked `ERROR ENTERS HERE`, with its `yours` and `carried` values; a row marked `inherited` is never a second flaw.
- **RC.b** — the interval and width of (a) agree with Probe A's `lo` and `hi` rows. If every row of (a) reads `ok`, (a) is correct, whatever rounding was used: do not invent a flaw.
- **RC.c** — (b)'s Wald bounds agree with Probe A's `wald_lo` and `wald_hi` rows, and the property named is one that those recomputed bounds break. A property claimed broken that the recomputed bounds keep scores ≤2, with the bounds pasted. The shape difference named holds of the two recomputed intervals (read both pairs of rows).
- **RC.d** — (c) states a factor and a reason. Probe A's `(c)` line, run on that factor, must show a width ratio between 0.45 and 0.55; a factor whose ratio falls outside scores ≤2, the line pasted. A reason that names how the width depends on n is enough; a reason that is false of the formula (quoted beside the formula of the problems file) is a gap at 3 when the factor itself checks.

## B2 — pass@k from its definition (hand-calculation; dimension: recomputation)

### recomputation
- **RC.e** — each task's pass@2 shows both binomial coefficients and the case rule (the problem's convention for `n − c < k`). A score ≤2 quotes Probe B's row marked `ERROR ENTERS HERE` and the probe's line of binomials for that task.
- **RC.f** — (b)'s two figures are means of per-task values, as the problem defines them. A mean that differs from the mean of the answer's own per-task values is exhibited by the `carried` column; one built from pooled counts is exhibited the same way.
- **RC.g** — (c)'s plug-in value agrees with Probe B's row, the direction (above or below) agrees with the recomputed pair, and the assumption named is one the plug-in formula makes and the definition does not. A claim that reverses the two scores ≤2, quoting it beside the two formulas of the problems file.

## B3 — Why a pass rate counts first attempts (concept; dimension: correctness)

### correctness
- **CO.a** — (a)'s three numbers agree with Probe C's rows (it counts the problem's table). A number that differs scores ≤2, the row quoted.
- **CO.b** — (b) names a mechanism, not a convention: what the unit of the estimate is, why the records of one task are not independent samples, and what counting every record does to `n` and to the interval. Try to counterexample each claim. A claim that two of the three numbers coincide, or that the other two numbers measure the same thing as the pass rate, is refuted by Probe C's rows on this very table: score ≤2 with the rows quoted. An answer with no mechanism is a gap (3).
- **CO.c** — (c) names what a reader needs before comparing the figure: at least the attempt budget and whether the attempts are independent samples or retries after a failure. One of the two missing is a gap (3). A claim that the figure is comparable as it stands with a first-attempt rate scores ≤2, exhibited by Probe C's rows (the two numbers on one table).

## B4 — A paired comparison (hand-calculation; dimension: recomputation)

### recomputation
- **RC.h** — (a)'s rates, `b` and `c` agree with Probe D's rows, and the informative tasks named are exactly the discordant ones. A claim that the concordant tasks inform the comparison scores ≤2 only with the recomputation of (c), which shows the test unmoved.
- **RC.i** — (b) writes each binomial term and the doubling, and the p-value agrees with Probe D's `p` row (`ERROR ENTERS HERE` quoted, with the probe's line of terms, for a score ≤2). The decision at α = 0.05 follows the answer's own p-value; a decision that contradicts it is a flaw, quoted.
- **RC.j** — (c) says what moves and what does not, in agreement with Probe D's `(c)` line. A claim that the p-value changes scores ≤2, the line pasted.

## The --post pass

Q06's written pair holds no informal-proof-first problem, so there is no blueprint to diff against your proofs: `/grade-paper Q06 --post` has nothing to re-score and writes no `paper-post` row. No `--report` pass either: Q06 has no lab, and `EVAL.md` v0 is your report, reviewed by you (the last section below).

## B5 — Paper card 02.4 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe E prints the hash B5 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled: task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact, each answering its own question. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with the pinned range (`cheatsheets.md` lines 672–699). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain (a run count, an interval, a cap, a cost) scores ≤2 only by naming the field and the quoted absence: the range lines that state the setup or the results without it.
- **CF.e** — figures stay attached to what the range attaches them to: a rate, a count, a time or a cost given for the wrong model, setting (hands-off or hands-on), system or aggregate contradicts the table or sentence it comes from, and CF.c applies. An interval the learner computes from a rate and its task count is their own arithmetic, not a card claim: it is correct when it says what it covers (sampling over tasks, not run-to-run variation).
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short; a field need not cover every fact the range offers. The card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.

## Gate

The mechanical preconditions of `/review-code Q06`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck --module Q06` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q06_Machine/std`, `scripts/vcheck --gate verus/q/q06_machine` and `scripts/vcheck --gate harness/q/fvh_q/q06_stats.py` each exit 0 and print only the summary line. After the contract run, `scripts/vcheck --gate dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy` does too.
- **A3 — audit, pinned.** `scripts/vaudit dafny/Q/Q06_Machine/std`, `scripts/vaudit verus/q/q06_machine` and `scripts/vaudit harness/q/fvh_q/q06_stats.py` report no finding; after the contract run, `scripts/vaudit --compare expected/Q06_AgentProver.audit dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy` reports no difference.
- **A4 — the suites run.** `scripts/vcheck --test dafny/Q/Q06_Machine/std` and `scripts/vcheck --test verus/q/q06_machine` pass every test, H4's uncommented suites included (Probe G).
- **A5 — slots, first tries, shipped lines, budgets.** `scripts/firsttry.sh Q06 --report --strict` exits 0: every slot filled, recorded and enabled, every shipped check uncommented, every property-test run passing, and its `budget` field 0 (no resource attribute charged to a budget item's block, the exit files' blocks included once they are repaired).
- **A6 — statements unchanged.** `scripts/specfreeze --check Q06` reports no finding.
- **A7 — diagnosis fixtures stay out.** The obligation specimens `specimens/Q06/P3d.dfy.specimen` and `specimens/Q06/P4v.rs.specimen` are predictions, covered by A5 alone; the card demos under `specimens/Q06/card-*` are red by design (their failures are pinned) and are never finished or reviewed. A2 and A3 skip all of them. No brittleness gate applies at this bar.

## Code-review focus — band: "proof-shape"

- **C1 — triggers fired on purpose (T1d, T1v, H1d, H1v).** The assertion that switches a quantified hypothesis on names a term of its trigger's shape, and you can say which term and why. An extra instance or assertion that Probe F shows dead is a finding at this bar; without that evidence, do not invent a flaw.
- **C2 — reveals scoped as narrowly as the proof allows (H2d, H2v).** A `reveal` sits where the body is needed. A wider scope is a finding only when Probe F′ verifies the narrower one; each value step after it is needed (Probe F). If every line is needed and no narrower reveal verifies, do not invent a flaw.
- **C3 — budget items fit by supplying facts (H3d, H3v).** No resource attribute anywhere in either file (A5's `budget` field is the anchor); every library call and assertion is needed (Probe F); no quantified step whose instances feed its own trigger is left in the proof. If the proof verifies at the pinned limit and every line is needed, do not invent a flaw.
- **C4 — checkers say what they checked (H4d, H4v).** The two-sided postcondition stands (A6); the loop invariant states what holds of every sample before the index; the early exit carries its witness; the suite runs a correct and a planted candidate and passes (Probe G). A checker that the verifier accepts and the suite exercises is correct: a finding here is about clarity, cited at `file:line`.
- **C5 — the Python composes, never re-derives (H5py–H7py).** No interval or estimator formula appears in your file: H6py and H7py call `fvh.stats` (the acceptance tests check the calls), each as its docstring says; `ValueError` for an empty arm; H5py takes each record field from one key or one argument. A re-derived formula is a finding even when its numbers agree, because statistics code lives only in the core. If the gate (A2) passes and the file holds no formula of its own, do not invent a flaw.
- **C6 — intent stays in the shipped contracts.** Q06's statements ship frozen; A6 is the anchor. The freeze does not see Dafny's `opaque` modifier, so read the declaration of every given opaque function in the files under review: each still reads `opaque function`. A changed `requires`, `ensures`, check line or opacity is a finding at grade 1, whatever the verifier says.
- **C7 — names and dead code.** Any name you introduced says what it holds; no commented-out experiments and no unused helpers in your own lines. Prediction slots and their answers stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding.

## Audit debrief — after /contract Q06

Questions for you, after the contract run. Each is settled by the transcript, the artifact or a command, and none has a secret answer.
- **D1 — did the statements stay yours?** `scripts/specfreeze --against research/q06_skeleton.dfy dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy` reports no change.
- **D2 — did the diff stay in the leaves' bodies?** `git diff -U0 -- dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy`, against your committed skeleton: every hunk is inside a leaf's body; no statement, attribute, doc comment or line of the top lemma's proof changed, and no lemma, function or method was added. An attribute on a leaf (an induction attribute, a resource attribute) is a breach even when the gate accepts it.
- **D3 — is the delivery green and audit-clean?** Run the contract's gate and `--compare` lines yourself (A2 and A3's agent forms) and compare them with the contractor's last report of them.
- **D4 — is each leaf useful?** Probe H on every leaf. Record, per leaf, the concrete call that verified, or the verified refutation of Probe H′. A leaf with neither is open: say why its `requires` can hold, or write a better call.
- **D5 — did the contractor re-verify after every edit?** Count the `scripts/vcheck` runs between edits in the transcript; name any stacked edits.
- **D6 — which leaf took longest, and why?** From the transcript's attempts and times: write it in the agent file's `AUDIT` block, with the failing message the contractor met most.
- **D7 — what did no instrument see?** The gate, the freeze and the audit each checked something; name one property of your skeleton that none of them checked (the chapter's dashboard section names the kind), and how you checked it instead.
- **D8 — which moment earns a rule?** Name one transcript moment (a stacked edit, a statement it tried to touch, a lemma it tried to add, an attribute) that deserves a rule in your next contract version, and write it in the rule format of `CLAUDE.md`'s contract slot.

## EVAL.md v0 and TRUST.md v0 — your own review

No skill grades these files: both are yours, written by hand (chapter §7). These questions are for you once both sections exist; each is settled by the file and a command, and none has a secret answer.
- **D9 — does EVAL.md v0 hold the five items?** The claim with its population, the metric with its estimator, `n` with the interval and the exclusions with their count, the cost, and the disclosure line (chapter §7's list).
- **D10 — does every number recompute?** Re-run, from a fresh shell, the commands the report names, and compare each number in the section with their output. A number they do not regenerate is a finding against your own report: fix the report or the command.
- **D11 — are the exclusions honest?** Only first tries enter the rate (rows of kind `predict`); every other row of your calibration files is counted as an exclusion, by kind. Recount them in the files.
- **D12 — does the disclosure say who did what?** Who made the predictions, which sessions tutored or graded, and anything you saw before committing. A sentence that would be false of your transcripts is a finding.
- **D13 — is each TRUST.md entry falsifiable?** Per language: the front end, the solver and its version, the standard library's trusted parts, the course wrappers and the given layers, each with one line on what would make a green run wrong. For the standard library's trusted parts, cite how you know they are trusted (a source location, a document, a command): the audit's report is not where they appear.
- **D14 — do Tested and Escape hatches match the files?** Tested lists the suites and what they sampled (Probe G's runs); Escape hatches says "none" only with the A3 runs that show it, pasted.
