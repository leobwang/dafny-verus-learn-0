// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"d1","kind":"decreases"},{"name":"a3"},{"name":"a4"},{"name":"a5"},{"name":"a6"},{"name":"a7"},{"name":"a8"}]
// R12_SOURCE_SPANS: [{"symbol":"Pow","start":8,"end":32}]
// R12 public task: dafnybench Prog-Fun-Solutions_tmp_tmp7_gmnz5f_extra_pow.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
ghost function pow(a: int, e: nat): int {
    if e == 0 then 1 else a*pow(a, e-1)
}

method Pow(a: nat, n: nat) returns (y: nat)
ensures y == pow(a, n)
{

    var x:nat := 1;
    var k:nat := 0;
    while k < n
    invariant /*R12_HINT:i1*/ true
    invariant /*R12_HINT:i2*/ true
    decreases /*R12_DECREASES:d1*/ (0 as int)
    {
        assert /*R12_HINT:a3*/ true;
        x := a*x;
        assert /*R12_HINT:a4*/ true;
        assert /*R12_HINT:a5*/ true;
         
        k := k + 1;
        assert /*R12_HINT:a6*/ true;

    }
    assert /*R12_HINT:a7*/ true;
    y := x;
    assert /*R12_HINT:a8*/ true;

}
