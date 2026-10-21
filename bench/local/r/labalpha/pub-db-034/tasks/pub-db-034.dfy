// R12_HINT_SITES: [{"name":"d1","kind":"decreases"},{"name":"i1"},{"name":"i2"},{"name":"i3"}]
// R12_SOURCE_SPANS: [{"symbol":"CountLessThan","start":4,"end":26}]
// R12 public task: dafnybench Clover_count_lessthan.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method CountLessThan(numbers: set<int>, threshold: int) returns (count: int)
  ensures count == |set i | i in numbers && i < threshold|
{
  count := 0;
  var shrink := numbers;
  var grow := {};
  while |shrink | > 0
    decreases /*R12_DECREASES:d1*/ (0 as int)
    invariant /*R12_HINT:i1*/ true
    invariant /*R12_HINT:i2*/ true
    invariant /*R12_HINT:i3*/ true
  {
    var i: int :| i in shrink;
    shrink := shrink - {i};
    var grow' := grow+{i};
    assert (set i | i in grow' && i < threshold) ==
           (set i | i in grow && i < threshold )+ if i < threshold then {i} else {};
    grow := grow + {i};
    if i < threshold {
      count := count + 1;
    }
  }
}
