// R12_HINT_SITES: [{"name":"d1","kind":"decreases"},{"name":"i1"},{"name":"i2"}]
// R12_SOURCE_SPANS: [{"symbol":"Fatorial","start":9,"end":23}]
// R12 public task: dafnybench Metodos_Formais_tmp_tmpql2hwcsh_Invariantes_fatorial2.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
function Fat(n:nat):nat
{
    if n == 0 then 1 else n*Fat(n-1)
}

method Fatorial(n:nat) returns (f:nat)
ensures f == Fat(n)
{
    f := 1;
    var i := 1;
    while i <= n
        decreases /*R12_DECREASES:d1*/ (0 as int)
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
    {
        f := f * i;
        i := i + 1;
    }
    return f;
}

// i | n | variante
// 1 | 3 | 2
// 2 | 3 | 1
// 3 | 3 | 0
// 4 | 3 | -1
// variante = n - i
// então é usado o decreases n-1
