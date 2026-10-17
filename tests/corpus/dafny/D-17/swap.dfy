// Cheat-corpus fixture D-17 (Dafny): the conclusion swapped for false. Invented program.
module CorpusD17 {
  predicate Ordered3(s: seq<int>) {
    |s| == 3 && s[0] <= s[1] <= s[2] && s[2] < s[0]
  }

  method Middle(s: seq<int>) returns (m: int)
    requires Ordered3(s)
    ensures false
  {
    m := s[1];
  }
}
