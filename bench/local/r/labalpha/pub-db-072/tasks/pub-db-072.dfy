// R12_HINT_SITES: [{"name":"i1","identifiers":["calcSum","i","n","s","sum"]},{"name":"i2","identifiers":["calcSum","i","n","s","sum"]}]
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
        decreases n - i
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
    {
        i := i + 1;
        s := s + i;
    }
}
