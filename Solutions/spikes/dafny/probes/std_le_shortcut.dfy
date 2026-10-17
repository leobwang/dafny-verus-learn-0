// Design-impact probe (author-only): how far does the standard library's
// Std.Arithmetic.LittleEndianNat take a std-tier learner on the BigNat spine?
// Verify with QG_L1_BigNat.dfy and QG_L2_BigNat.dfy, --standard-libraries.

// 1. The library module instantiated at the literal BASE = 2^64.
module LE64 refines Std.Arithmetic.LittleEndianNat {
  function BASE(): nat { 18446744073709551616 }
}

module StdShortcut {
  import opened QG_L1_BigNat
  import QG_L2_BigNat
  import LE64

  // 2. FromNat round trip for the library's numeral: one library call.
  lemma LibRoundTrip(n: nat)
    ensures LE64.ToNatRight(LE64.FromNat(n)) == n
  {
    LE64.LemmaNatSeqNat(n);
  }

  // 3. The bridge from the spine's ToNat to the library's ToNatRight.
  lemma {:induction false} ToNatIsToNatRight(s: seq<LE64.digit>)
    ensures ToNat(s) == LE64.ToNatRight(s)
  {
    if |s| > 0 {
      ToNatIsToNatRight(s[1..]);
    }
  }

  // 4. The bridge from the spine's FromNat to the library's FromNat.
  lemma {:induction false} FromNatIsLibFromNat(n: nat)
    ensures QG_L2_BigNat.FromNat(n) == LE64.FromNat(n)
    decreases n
  {
    if n > 0 {
      FromNatIsLibFromNat(n / BASE);
    }
  }

  // 5. The spine's FromNat value fact (an L2 hole target) through the library.
  lemma {:induction false} FromNatValueViaLib(n: nat)
    ensures ToNat(QG_L2_BigNat.FromNat(n)) == n
  {
    FromNatIsLibFromNat(n);
    ToNatIsToNatRight(LE64.FromNat(n));
    LE64.LemmaNatSeqNat(n);
  }
}
