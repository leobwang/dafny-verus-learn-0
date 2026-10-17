/*!
# Q05 — exit, Dafny half (closed book)

Closed book: keep the chapter, the exercise files, later modules' files,
search tools and /tutor closed. At most the given spine (dafny/given/Q/) may
be open.

This file ships with exactly 2 holes (X1, X2); the Verus half
(verus/q/q05_frames/src/exit.rs) ships with 2 holes. Score both halves in one
sitting with

    scripts/firsttry.sh Q05 --exit

Threshold: 3 of the 4 exit items, with at least 1 of the 2 in each language.
The first full run (every block attempted) is the score; repair every block
afterwards, after which the strict gate covers this file too. This file is in
no build: work it with `scripts/vcheck dafny/Q/Q05_Frames/exit/Q05_Exit.dfy`.
*/
module Q05_Exit {
  import opened QG_L1_BigNat
  import opened Std.Wrappers

  // Given (not items): the decimal-digit predicate and a field parser, for X2.
  predicate AllDigits(s: string)
  {
    forall i | 0 <= i < |s| :: '0' <= s[i] <= '9'
  }

  // Parse one non-empty field of decimal digits; it succeeds exactly when the
  // field is non-empty and every character is a digit.
  method ParseField(t: string) returns (r: Result<nat, string>)
    ensures r.Success? <==> (|t| > 0 && AllDigits(t))
  {
    if |t| == 0 {
      return Failure("empty");
    }
    var v: nat := 0;
    var i := 0;
    while i < |t|
      invariant 0 <= i <= |t|
      invariant AllDigits(t[..i])
    {
      if !('0' <= t[i] <= '9') {
        return Failure("not a digit");
      }
      v := v * 10 + (t[i] as nat - '0' as nat);
      i := i + 1;
    }
    assert t[..|t|] == t;
    return Success(v);
  }

  // item: Q05.X1d S7
  // uses: by-method
  // need: function CountFull(s: seq<nat>): nat
  // need: if |s| == 0 then 0 else (if s[0] == BASE - 1 then 1 else 0) + CountFull(s[1..])
  /** **X1.** `CountFull(s)` counts the limbs of `s` equal to `BASE - 1`. Write
      its `by method` body: a loop that counts them. */
  function CountFull(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else (if s[0] == BASE - 1 then 1 else 0) + CountFull(s[1..])
  } by method {
    assume false;  // HOLE: delete this line and write the method body
  }

  // item: Q05.X2d S6
  // uses: error-propagation
  // need: method ParseTwo(s: string, k: nat) returns (r: Result<(nat, nat), string>)
  // need: ensures r.Success? <==> (|s[..k]| > 0 && AllDigits(s[..k]) && |s[k..]| > 0 && AllDigits(s[k..]))
  /** **X2.** Split `s` at position `k` and parse both fields with the given
      `ParseField`, propagating the first failure with `:-`. */
  method ParseTwo(s: string, k: nat) returns (r: Result<(nat, nat), string>)
    requires k <= |s|
    ensures r.Success? <==> (|s[..k]| > 0 && AllDigits(s[..k]) && |s[k..]| > 0 && AllDigits(s[k..]))
  {
    assume false;  // HOLE: delete this line and implement
  }
}
