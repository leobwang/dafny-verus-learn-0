// R12_HINT_SITES: [{"name":"d1","kind":"decreases"},{"name":"i1"},{"name":"i2"}]
// R12_SOURCE_SPANS: [{"symbol":"sum","start":9,"end":22}]
// R12 public task: dafnybench MFES_2021_tmp_tmpuljn8zd9_FCUL_Exercises_8_sum.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
function calcSum(n: nat) : nat 
{   
    n * (n - 1) / 2
}

method sum(n: nat) returns(s: nat)
    ensures s == calcSum(n + 1)
{
    s := 0;
    var i := 0;
    while i < n 
        decreases /*R12_DECREASES:d1*/ (0 as int)
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
    {
        i := i + 1;
        s := s + i;
    }
}
