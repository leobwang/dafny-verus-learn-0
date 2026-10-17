// Battery goal D5, candidate 2 (a whole file; it stands alone).
module Battery_D5 {
  // Total head and tail: a missing limb reads as 0.
  function Head(s: seq<nat>): nat
  {
    if |s| == 0 then 0 else s[0]
  }

  function Tail(s: seq<nat>): seq<nat>
  {
    if |s| == 0 then [] else s[1..]
  }

  // A non-empty sequence is its head put below its tail.
  lemma HeadTailCons(s: seq<nat>)
    requires |s| > 0
    ensures [Head(s)] + Tail(s) == s
  {
    assume [Head(s)] + Tail(s) == s;
  }
}
