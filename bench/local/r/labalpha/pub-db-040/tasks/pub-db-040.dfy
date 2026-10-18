// R12_HINT_SITES: [{"name":"i1","identifiers":["Length","SelectionSort","a","array","i","j","m","mindex","multiset","n","old"]},{"name":"i2","identifiers":["Length","SelectionSort","a","array","i","j","m","mindex","multiset","n","old"]},{"name":"i3","identifiers":["Length","SelectionSort","a","array","i","j","m","mindex","multiset","n","old"]},{"name":"i4","identifiers":["Length","SelectionSort","a","array","i","j","m","mindex","multiset","n","old"]},{"name":"i5","identifiers":["Length","SelectionSort","a","array","i","j","m","mindex","multiset","n","old"]},{"name":"i6","identifiers":["Length","SelectionSort","a","array","i","j","m","mindex","multiset","n","old"]},{"name":"i7","identifiers":["Length","SelectionSort","a","array","i","j","m","mindex","multiset","n","old"]},{"name":"i8","identifiers":["Length","SelectionSort","a","array","i","j","m","mindex","multiset","n","old"]}]
// R12_SOURCE_SPANS: [{"symbol":"SelectionSort","start":4,"end":33}]
// R12 public task: dafnybench Dafny_Verify_tmp_tmphq7j0row_Test_Cases_solved_1_select.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method SelectionSort(a: array<int>)
  modifies a
  ensures forall i,j :: 0 <= i < j < a.Length ==> a[i] <= a[j]
  ensures multiset(a[..]) == old(multiset(a[..]))
{
  var n := 0;
  while n != a.Length
    invariant /*R12_HINT:i1*/ true
    invariant /*R12_HINT:i2*/ true
    invariant /*R12_HINT:i3*/ true
    invariant /*R12_HINT:i4*/ true
  {
    var mindex, m := n, n;
    while m != a.Length
      invariant /*R12_HINT:i5*/ true
      invariant /*R12_HINT:i6*/ true
      invariant /*R12_HINT:i7*/ true
      invariant /*R12_HINT:i8*/ true
    {
      if a[m] < a[mindex] {
        mindex := m;
      }
      m := m + 1;
    }
    if a[mindex] < a[n] {
      a[mindex], a[n] := a[n], a[mindex];
    }
    n := n + 1;
  }  
}
