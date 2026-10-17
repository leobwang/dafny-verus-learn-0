/*!
# Q07 — the port's Dafny checks (given-only check unit)

This file holds the Dafny side of Q07's D→V port (the Verus port is
verus/q/q07_internals_i/src/port.rs, H7–H9). It imports only the given spine
layers L1–L3, so it compiles and runs while the exercise files still have
holes, and it holds no item and no slot: both tests are given. Run them with

    scripts/vcheck --test dafny/checks/Q07_checks.dfy

`scripts/vcheck --test` prints one PASSED or FAILED line per test, not what a
test prints: with `--json` added, the test run's printed lines are in the
file `stdout.txt` of the directory its `raw_dir` field names.

- `SampleRun` runs L2's `FromNat` on the port's sample and `expect`s each
  result: the same rows as the port's differential suite at the end of
  src/port.rs, which runs them against your port compiled by Verus.
- `MutantEvaluation` (open it after H7 verifies) computes, for each of the
  three mutants of src/port.rs's MUTANTS block, the Dafny output that matches
  the mutant's output on each sample row, and prints that output's `Valid`
  and `ToNat` beside the row's input. It `expect`s nothing: whether the Dafny
  contract (`FromNatCorrect`: `Valid`, and the value) accepts each output is
  for you to read off the printed lines, into the FIDELITY block of
  src/port.rs.
*/
module Q07_Checks {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat

  // The port's sample: six inputs below 2^128.
  function Sample(): seq<nat>
  {
    [0, 5, BASE - 1, BASE + 7, 3 * BASE + 2, BASE * BASE - 1]
  }

  @Test
  method SampleRun() {
    expect FromNat(0) == [];
    expect FromNat(5) == [5];
    expect FromNat(BASE - 1) == [BASE - 1];
    expect FromNat(BASE + 7) == [7, 1];
    expect FromNat(3 * BASE + 2) == [2, 3];
    expect FromNat(BASE * BASE - 1) == [BASE - 1, BASE - 1];
  }

  // The Dafny outputs that match the mutants' outputs on the sample's rows,
  // each written from FromNat's own result.
  // M1: both limbs, whatever their values.
  function M1(x: nat): seq<nat>
  {
    [x % BASE, x / BASE % BASE]
  }

  // M2: the high limb first, then the low limb.
  function M2(x: nat): seq<nat>
  {
    if |FromNat(x)| == 2 then [FromNat(x)[1], FromNat(x)[0]] else FromNat(x)
  }

  // M3: the high limb taken from x shifted right by 63 bits (and cut to 64
  // bits, as a cast to u64 cuts it).
  function M3(x: nat): seq<nat>
  {
    if x / (BASE / 2) % BASE == 0 then FromNat(x) else [x % BASE, x / (BASE / 2) % BASE]
  }

  method Show(name: string, x: nat, r: seq<nat>) {
    print name, " input ", x, ": Valid ", Valid(r), ", ToNat ", ToNat(r), "\n";
  }

  @Test
  method MutantEvaluation() {
    var xs := Sample();
    var i := 0;
    while i < |xs|
      invariant 0 <= i <= |xs|
      decreases |xs| - i
    {
      Show("M1", xs[i], M1(xs[i]));
      Show("M2", xs[i], M2(xs[i]));
      Show("M3", xs[i], M3(xs[i]));
      i := i + 1;
    }
  }
}
