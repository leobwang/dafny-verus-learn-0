// Battery goal D4, candidate 1 (a whole file; it stands alone).
module Battery_D4 {
  function CountZeros(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else (if s[0] == 0 then 1 else 0) + CountZeros(s[1..])
  }

  // No more zero limbs than limbs.
  lemma {:induction false} CountZerosBound(s: seq<nat>)
    ensures CountZeros(s) <= |s|
    decreases |s|
  {
  }
}
