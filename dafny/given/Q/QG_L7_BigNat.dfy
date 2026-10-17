/*!
# QG_L7_BigNat — the BigNat spine, layer L7 (PROVIDED, complete)

This file is provided infrastructure, not an exercise: there is nothing to fill
in and nothing here is a hole. It is frozen: no session edits it, and no
module copies it.

Imported by: Q16–Q18. From Q16 on, a module's files that use it import it
beside L1–L6. Its module is QG_L7_BigNat, and each unit that reaches it
includes this file through its dfyconfig.toml.

Do not open this file before you start Q16: it belongs to the hard practice
tier, and the files of a tier are opened with its first module.

What it holds: three definitions and no lemma. `Shift` puts k zero limbs below
a sequence. `MulAcc` is the schoolbook multiplication row by row: for each
limb of `b`, from the low limb, it adds the row `MulLimb(a, <limb>)`, shifted
by the limb's position, into an accumulator. `Times` starts it from the empty
accumulator at position 0. `MulAcc` and `Times` are ghost, so no compiled
code can call them.
*/
module {:disableNonlinearArithmetic} QG_L7_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened QG_L6_BigNat

  // ---------------------------------------------------------------------------
  // The schoolbook definitions
  // ---------------------------------------------------------------------------

  // k zero limbs below s.
  function Shift(s: seq<nat>, k: nat): seq<nat>
  {
    seq(k, _ => 0) + s
  }

  // One MulLimb row per limb of b, from the low limb: the row of b[0] is
  // shifted by k and added into acc, then the rest of b continues at k + 1.
  ghost function MulAcc(a: seq<nat>, b: seq<nat>, acc: seq<nat>, k: nat): seq<nat>
    decreases |b|
  {
    if |b| == 0 then acc else MulAcc(a, b[1..], Add(acc, Shift(MulLimb(a, b[0]), k)), k + 1)
  }

  // The schoolbook product: every row, from the empty accumulator at position 0.
  ghost function Times(a: seq<nat>, b: seq<nat>): seq<nat>
  {
    MulAcc(a, b, [], 0)
  }
}
