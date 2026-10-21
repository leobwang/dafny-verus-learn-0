// R12_HINT_SITES: [{"name":"i1"},{"name":"d1","kind":"decreases"}]
// R12_SOURCE_SPANS: [{"symbol":"Quotient","start":4,"end":18}]
// R12 public task: dafnybench Clover_quotient.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method Quotient(x: nat, y:nat) returns (r:int, q:int)
  requires y != 0
  ensures q * y + r == x && 0 <= r < y && 0 <= q
{
  r:=x;
  q:=0;
  while y<=r
    invariant /*R12_HINT:i1*/ true
    decreases /*R12_DECREASES:d1*/ (0 as int)
  {
    r:=r-y;
    q:=q+1;

  }
}
