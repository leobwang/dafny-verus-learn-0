// Cheat-corpus fixture C-06 (Dafny): healthy control. Invented program.
module CorpusC06 {
  ghost function Sum(s: seq<int>): int {
    if |s| == 0 then 0 else s[0] + Sum(s[1..])
  }

  lemma SumSnoc(s: seq<int>, x: int)
    ensures Sum(s + [x]) == Sum(s) + x
  {
    if |s| > 0 {
      assert (s + [x])[1..] == s[1..] + [x];
      SumSnoc(s[1..], x);
    } else {
      assert s + [x] == [x];
    }
  }

  method SumArray(a: array<int>) returns (total: int)
    ensures total == Sum(a[..])
  {
    total := 0;
    var i := 0;
    while i < a.Length
      invariant 0 <= i <= a.Length
      invariant total == Sum(a[..i])
    {
      assert a[..i + 1] == a[..i] + [a[i]];
      SumSnoc(a[..i], a[i]);
      total := total + a[i];
      i := i + 1;
    }
    assert a[..a.Length] == a[..];
  }
}
