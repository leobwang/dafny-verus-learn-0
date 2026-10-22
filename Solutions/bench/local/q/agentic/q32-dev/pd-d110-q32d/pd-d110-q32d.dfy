// Topic (e) dev task pd-d110-q32d (Q32, public; QPLAN §34.4, D76).
// Source: dafnybench dafny-synthesis_task_id_62.dfy (Apache-2.0 (DafnyBench)); the set's hints_removed form, unchanged.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
method FindSmallest(s: array<int>) returns (min: int)
  requires s.Length > 0
  ensures forall i :: 0 <= i < s.Length ==> min <= s[i]
  ensures exists i :: 0 <= i < s.Length && min == s[i]
{
  min := s[0];
  for i := 1 to s.Length
    invariant 0 <= i <= s.Length
    invariant forall k :: 0 <= k < i ==> min <= s[k]
    invariant exists k :: 0 <= k < i && min == s[k]
  {
    if s[i] < min
    {
      min := s[i];
    }
  }
}