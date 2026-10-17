/*!
# QG_L5_BigNat — the BigNat spine, layer L5 (PROVIDED, complete)

This file is provided infrastructure, not an exercise: there is nothing to fill
in and nothing here is a hole. It is frozen: no session edits it, and no
module copies it.

Imported by: Q10–Q18. From Q10 on, a module's files that use it import it
beside L1–L4. Its module is QG_L5_BigNat, and each unit that reaches it
includes this file through its dfyconfig.toml.

Do not open this file before you start Q10: it belongs to the practice
tiers, and the files of a tier are opened with its first module.

What it holds: three proved lemmas about the L1 and L2 definitions: a lower
bound on the value of a canonical number (`CanonicalLower`), the positivity of
every power of BASE (`PowPositive`), and what `Normalize` does to a sequence
whose limbs from some position on are all zero (`NormalizeTrim`).
*/
module QG_L5_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // ---------------------------------------------------------------------------
  // Proved lemmas about the L1 and L2 definitions
  // ---------------------------------------------------------------------------

  // A canonical non-empty sequence is at least BASE^(|s| - 1).
  lemma CanonicalLower(s: seq<nat>)
    requires Canonical(s) && |s| > 0
    ensures Pow(|s| - 1) <= ToNat(s)
    decreases |s|
  {
    ToNatHeadTail(s);
    if |s| > 1 {
      assert Canonical(s[1..]);
      CanonicalLower(s[1..]);
    }
  }

  // Every power of BASE is positive.
  lemma PowPositive(n: nat)
    ensures 0 < Pow(n)
    decreases n
  {
    if n > 0 {
      PowPositive(n - 1);
    }
  }

  // If every limb from position n on is zero, and the limb just below n (when
  // there is one) is not, then Normalize keeps exactly the first n limbs.
  lemma NormalizeTrim(s: seq<nat>, n: nat)
    requires n <= |s|
    requires n == 0 || s[n - 1] != 0
    requires forall j | n <= j < |s| :: s[j] == 0
    ensures Normalize(s) == s[..n]
    decreases |s|
  {
    if |s| > n {
      assert s[..|s| - 1][..n] == s[..n];
      NormalizeTrim(s[..|s| - 1], n);
    } else {
      assert s[..n] == s;
    }
  }
}
