/*!
# QG_L6_BigNat — the BigNat spine, layer L6 (PROVIDED, complete)

This file is provided infrastructure, not an exercise: there is nothing to fill
in and nothing here is a hole. It is frozen: no session edits it, and no
module copies it.

Imported by: Q13–Q18. From Q13 on, a module's files that use it import it
beside L1–L5. Its module is QG_L6_BigNat, and each unit that reaches it
includes this file through its dfyconfig.toml.

Do not open this file before you start Q13: it belongs to the intermediate
practice tier, and the files of a tier are opened with its first module.

What it holds: two proved lemmas, that `FromNat` gives canonical limbs
(`FromNatCanonical`) and that normalized addition is canonical with the sum
of the values (`NormalizeAddCorrect`), and one specification, subtraction
by value (`Sub`), with no algorithm: it is ghost, so no compiled code can
call it.
*/
module {:disableNonlinearArithmetic} QG_L6_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat

  // ---------------------------------------------------------------------------
  // Proved lemmas about the L2 and L4 definitions
  // ---------------------------------------------------------------------------

  // FromNat gives canonical limbs.
  lemma FromNatCanonical(n: nat)
    ensures Canonical(FromNat(n))
    decreases n
  {
    FromNatCorrect(n);
    if n > 0 {
      FromNatCanonical(n / BASE);
      if n / BASE == 0 {
        assert FromNat(n / BASE) == [];
        assert n % BASE == n;
      }
    }
  }

  // Normalized addition is canonical, with the sum of the values.
  lemma NormalizeAddCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Canonical(Normalize(Add(a, b))) && ToNat(Normalize(Add(a, b))) == ToNat(a) + ToNat(b)
  {
    AddCorrect(a, b);
    NormalizeCanonical(Add(a, b));
    NormalizeToNat(Add(a, b));
  }

  // ---------------------------------------------------------------------------
  // A specification
  // ---------------------------------------------------------------------------

  // Subtraction, by value: what a subtraction routine must compute. No
  // algorithm, and no lemma about it.
  ghost function Sub(a: seq<nat>, b: seq<nat>): seq<nat>
    requires Valid(a) && Valid(b) && ToNat(a) >= ToNat(b)
  {
    FromNat(ToNat(a) - ToNat(b))
  }
}
