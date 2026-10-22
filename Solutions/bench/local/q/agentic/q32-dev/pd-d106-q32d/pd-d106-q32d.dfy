// Topic (e) dev task pd-d106-q32d (Q32, public; QPLAN §34.4, D76).
// Source: dafnybench Clover_selectionsort.dfy (Apache-2.0 (DafnyBench)); the set's hints_removed form, unchanged.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
method SelectionSort(a: array<int>)
  modifies a
  ensures forall i,j :: 0 <= i < j < a.Length ==> a[i] <= a[j]
  ensures multiset(a[..]) == old(multiset(a[..]))
{
  var n:= 0;
  while n != a.Length
    invariant 0 <= n <= a.Length
    invariant forall i, j :: 0 <= i < n <= j < a.Length ==> a[i] <= a[j]
    invariant forall i,j :: 0 <= i < j < n ==> a[i] <= a[j]
    invariant multiset(a[..]) == old(multiset(a[..]))
  {
    var mindex, m := n, n+1;
    while m != a.Length
      invariant n <= mindex < m <= a.Length
      invariant forall i :: n <= i < m ==> a[mindex] <= a[i]
    {
      if a[m] < a[mindex] {
        mindex := m;
      }
      m := m+1;
    }
    a[n], a[mindex] := a[mindex], a[n];
    n := n+1;
  }
}
