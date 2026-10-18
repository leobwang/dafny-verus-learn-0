// R12_HINT_SITES: [{"name":"i1","identifiers":["SumAndAverage","average","i","n","real","sum"]},{"name":"i2","identifiers":["SumAndAverage","average","i","n","real","sum"]}]
// R12_SOURCE_SPANS: [{"symbol":"SumAndAverage","start":4,"end":17}]
// R12 public task: dafnybench dafny-synthesis_task_id_599.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method SumAndAverage(n: int) returns (sum: int, average: real)
    requires n > 0
    ensures sum == n * (n + 1) / 2
    ensures average == sum as real / n as real
{
    sum := 0;
    for i := 1 to n + 1
    invariant /*R12_HINT:i1*/ true
    invariant /*R12_HINT:i2*/ true
    {
        sum := sum + i;
    }
    average := sum as real / n as real;
}