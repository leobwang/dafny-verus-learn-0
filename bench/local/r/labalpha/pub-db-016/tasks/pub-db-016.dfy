// R12_HINT_SITES: [{"name":"i1","identifiers":["Pow","a","k","n","pow","x","y"]},{"name":"i2","identifiers":["Pow","a","k","n","pow","x","y"]},{"name":"a3","identifiers":["Pow","a","k","n","pow","x","y"]},{"name":"a4","identifiers":["Pow","a","k","n","pow","x","y"]},{"name":"a5","identifiers":["Pow","a","k","n","pow","x","y"]},{"name":"a6","identifiers":["Pow","a","k","n","pow","x","y"]},{"name":"a7","identifiers":["Pow","a","k","n","pow","x","y"]},{"name":"a8","identifiers":["Pow","a","k","n","pow","x","y"]}]
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
    decreases n-k
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
