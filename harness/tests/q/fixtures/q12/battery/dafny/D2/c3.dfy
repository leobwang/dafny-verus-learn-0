// Battery goal D2, candidate 3 (a whole file; it stands alone).
module Battery_D2 {
  function CountZeros(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else (if s[0] == 0 then 1 else 0) + CountZeros(s[1..])
  }

  // Zero limbs add up over a concatenation.
  lemma {:induction false} CountZerosAppend(s: seq<nat>, t: seq<nat>)
    ensures CountZeros(s + t) == CountZeros(s) + CountZeros(t)
    decreases |s|
  {
    assume false;
  }
}
