/*!
# QG_L1_BigNat — the BigNat spine, layer L1 (PROVIDED, complete)

This file is provided infrastructure, not an exercise: there is nothing to fill
in and nothing here is a hole. It is frozen: no session edits it, and no
module copies it.

Imported by: Q01–Q18. Q01's files import this layer alone; from Q02 on, a
module's files import it beside the later layers of their chain. Its module
is QG_L1_BigNat, and each unit's dfyconfig.toml includes this file.

What it holds: the limb representation (a little-endian `seq<nat>`, least
significant limb first), the base `BASE`, the value `ToNat`, the limb-range
predicate `Valid`, the power `Pow`, the total helpers `Head`, `Tail` and
`Drop`, and one worked lemma. Layer L2 (QG_L2_BigNat.dfy) adds the helper
lemmas and the intro-tier definitions.
*/
module QG_L1_BigNat {

  // The limb base, 2^64, written as a literal.
  const BASE: nat := 18446744073709551616

  // Every limb is a digit in base 2^64.
  predicate Valid(s: seq<nat>)
  {
    forall i | 0 <= i < |s| :: s[i] < BASE
  }

  // The value of a limb sequence, least significant limb first:
  // s[0] + BASE * (the value of the remaining limbs).
  function ToNat(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + BASE * ToNat(s[1..])
  }

  // BASE^n, by repeated multiplication by BASE.
  function Pow(n: nat): nat
    decreases n
  {
    if n == 0 then 1 else BASE * Pow(n - 1)
  }

  // Total head and tail: a missing limb reads as 0.
  function Head(s: seq<nat>): nat
  {
    if |s| == 0 then 0 else s[0]
  }

  function Tail(s: seq<nat>): seq<nat>
  {
    if |s| == 0 then [] else s[1..]
  }

  // The suffix from position i; empty once i passes the end.
  function Drop(s: seq<nat>, i: nat): seq<nat>
  {
    if i >= |s| then [] else s[i..]
  }

  // The worked lemma: a zero limb appended at the most significant end does
  // not change the value.
  lemma ToNatAppendZero(s: seq<nat>)
    ensures ToNat(s + [0]) == ToNat(s)
    decreases |s|
  {
    if |s| == 0 {
      assert s + [0] == [0];
    } else {
      assert (s + [0])[1..] == s[1..] + [0];
      ToNatAppendZero(s[1..]);
    }
  }
}
