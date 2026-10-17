// Cheat-corpus fixture C-04 (Dafny): the frozen abstract statement module. Invented program.
abstract module CorpusC04Spec {
  function Count(s: seq<bool>): nat {
    if |s| == 0 then 0 else (if s[0] then 1 else 0) + Count(s[1..])
  }

  lemma CountBound(s: seq<bool>)
    ensures Count(s) <= |s|
}
