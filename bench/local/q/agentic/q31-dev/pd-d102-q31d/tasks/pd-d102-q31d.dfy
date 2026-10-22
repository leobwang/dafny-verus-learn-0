// Topic (e) dev task pd-d102-q31d (Q31, public; QPLAN §33.4, D76).
// Source: dafnybench Clover_linear_search2.dfy (Apache-2.0 (DafnyBench)); the set's hints_removed form, unchanged.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
method LinearSearch(a: array<int>, e: int) returns (n:int)
  requires exists i::0<=i<a.Length && a[i]==e
  ensures 0<=n<a.Length && a[n]==e
  ensures forall k :: 0 <= k < n ==> a[k]!=e

{
  n :=0;
  while n!=a.Length
  {
    if e==a[n]{
      return;
    }
    n:=n+1;
  }
}
