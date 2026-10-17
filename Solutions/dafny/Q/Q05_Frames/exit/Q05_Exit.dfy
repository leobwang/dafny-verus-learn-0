/*!
# Q05 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q05_Frames/exit/Q05_Exit.dfy` (author-only;
never learner-visible). Same module, imports, given definitions, statements,
item markers and order as the exit file; each block's body is filled. Silent
under the gate.
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
      its `by method` body: a loop that counts them.

      Reference: a loop from the end, keeping the count of the suffix it has
      read, `c == CountFull(s[i..])`; the assertion `s[i..][1..] == s[i + 1..]`
      lets `CountFull(s[i..])` unfold onto the suffix from `i + 1`. */
  function CountFull(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else (if s[0] == BASE - 1 then 1 else 0) + CountFull(s[1..])
  } by method {
    var c := 0;
    var i := |s|;
    while i > 0
      invariant 0 <= i <= |s|
      invariant c == CountFull(s[i..])
    {
      i := i - 1;
      assert s[i..][1..] == s[i + 1..];
      if s[i] == BASE - 1 {
        c := c + 1;
      }
    }
    assert s[0..] == s;
    return c;
  }

  // item: Q05.X2d S6
  // uses: error-propagation
  // need: method ParseTwo(s: string, k: nat) returns (r: Result<(nat, nat), string>)
  // need: ensures r.Success? <==> (|s[..k]| > 0 && AllDigits(s[..k]) && |s[k..]| > 0 && AllDigits(s[k..]))
  /** **X2.** Split `s` at position `k` and parse both fields with the given
      `ParseField`, propagating the first failure with `:-`.

      Reference: two `:-` steps and a success; `ParseField`'s postcondition
      states exactly when each step succeeds, which is the conjunction the
      postcondition asks for. */
  method ParseTwo(s: string, k: nat) returns (r: Result<(nat, nat), string>)
    requires k <= |s|
    ensures r.Success? <==> (|s[..k]| > 0 && AllDigits(s[..k]) && |s[k..]| > 0 && AllDigits(s[k..]))
  {
    var a :- ParseField(s[..k]);
    var b :- ParseField(s[k..]);
    return Success((a, b));
  }
}
