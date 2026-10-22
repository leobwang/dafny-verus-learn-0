// Topic (e) dev task pd-d109-q32d (Q32, public; QPLAN §34.4, D76).
// Source: dafnybench Clover_below_zero.dfy (Apache-2.0 (DafnyBench)); the set's hints_removed form, unchanged.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
method below_zero(operations: seq<int>) returns (s:array<int>, result:bool)
  ensures s.Length == |operations| + 1
  ensures s[0]==0
  ensures forall i :: 0 <= i < s.Length-1 ==> s[i+1]==s[i]+operations[i]
  ensures result == true ==> (exists i :: 1 <= i <= |operations| && s[i] < 0)
  ensures result == false ==> forall i :: 0 <= i < s.Length ==> s[i] >= 0
{
  result := false;
  s := new int[|operations| + 1];
  var i := 0;
  s[i] := 0;
  while i < s.Length
  {
    if i>0{
      s[i] := s[i - 1] + operations[i - 1];
    }
    i := i + 1;
  }
  i:=0;
  while i < s.Length
  {
    if s[i] < 0 {
      result := true;
      return;
    }
    i := i + 1;
  }
}
