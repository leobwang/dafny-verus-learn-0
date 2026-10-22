// R12_HINT_SITES: [{"name":"i1"},{"name":"d1","kind":"decreases"}]
// R12_SOURCE_SPANS: [{"symbol":"Eval","start":4,"end":18}]
// R12 public task: dafnybench se2011_tmp_tmp71eb82zt_ass1_ex4.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method Eval(x:int) returns (r:int)		// do not change
requires x >= 0
ensures r == x*x
{ 										// do not change
var y:int := x; 						// do not change
var z:int := 0; 						// do not change
while y>0 								// do not change
invariant /*R12_HINT:i1*/ true
decreases /*R12_DECREASES:d1*/ (0 as int)
{ 										// do not change
z := z + x; 							// do not change
y := y - 1; 							// do not change
} 										// do not change
return z; 								// do not change
} 										// do not change

