/*!
# Q07 — the port's Dafny checks (Reference Solution)

Hole-free reference for `dafny/checks/Q07_checks.dfy` (author-only): the
check unit ships complete (no item, no slot), so the twin is the same file.
`SampleRun` passes; `MutantEvaluation` prints, for the sample rows, `Valid`
true for every mutant output, the right value for every M1 output, and a wrong
value for M2 on 2^64 + 7 and 3 * 2^64 + 2 and for M3 on 2^64 - 1, 2^64 + 7 and
3 * 2^64 + 2: the Dafny contract accepts M1 and rejects M2 and M3. Silent under
the gate.
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
