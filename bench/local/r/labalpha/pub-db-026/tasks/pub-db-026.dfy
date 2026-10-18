// R12_HINT_SITES: [{"name":"i1","identifiers":["Busca","Length","T","a","array","i","r","x"]},{"name":"i2","identifiers":["Busca","Length","T","a","array","i","r","x"]}]
// R12_SOURCE_SPANS: [{"symbol":"Busca","start":4,"end":20}]
// R12 public task: dafnybench t1_MF_tmp_tmpi_sqie4j_exemplos_colecoes_arrays_ex5.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method Busca<T(==)>(a:array<T>, x:T) returns (r:int)
  ensures 0 <= r ==> r < a.Length && a[r] == x
  ensures r < 0 ==> forall i :: 0 <= i < a.Length ==> a[i] != x
{
    r :=0;
    while r < a.Length
      invariant /*R12_HINT:i1*/ true
      invariant /*R12_HINT:i2*/ true
    {
        if a[r]==x
        {
            return;
        }
        r := r +  1;
    }
    r := -1;
}
