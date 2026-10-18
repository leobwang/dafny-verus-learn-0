// R12_HINT_SITES: [{"name":"i1","identifiers":["Length","LinearSearch","P","T","a","array","i","n"]},{"name":"i2","identifiers":["Length","LinearSearch","P","T","a","array","i","n"]}]
// R12_SOURCE_SPANS: [{"symbol":"LinearSearch","start":4,"end":19}]
// R12 public task: dafnybench Dafny_Verify_tmp_tmphq7j0row_Generated_Code_LinearSearch.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method LinearSearch<T>(a: array<T>, P: T -> bool) returns (n: int)
    ensures 0 <= n <= a.Length
    ensures n == a.Length || P(a[n])
    ensures forall i :: 0 <= i < n ==> !P(a[i])
{
    n := 0;
    while n != a.Length
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
    {
        if P(a[n]) {
            return;
        }
        n := n + 1;
    }
}
