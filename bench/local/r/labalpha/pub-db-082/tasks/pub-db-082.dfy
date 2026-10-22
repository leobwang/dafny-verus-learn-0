// R12_HINT_SITES: [{"name":"i1"},{"name":"d1","kind":"decreases"},{"name":"a2"},{"name":"a3"},{"name":"a4"},{"name":"a5"},{"name":"a6"},{"name":"a7"},{"name":"a8"},{"name":"a9"},{"name":"a10"}]
// R12_SOURCE_SPANS: [{"symbol":"problem6","start":19,"end":44}]
// R12 public task: dafnybench Prog-Fun-Solutions_tmp_tmp7_gmnz5f_mockExam2_p6.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
// problem 6:
// name:      Gabriele Berardi
// s-number: s4878728
// table:     XXXXX

ghost function f(n: int): int {
  if n <= 0 then 1 else n + f(n-1)*f(n-2)
}

ghost function fSum(n: nat): int {
 // give the body of this function
  // it should return Sum(i: 0<=i < n: f(i))
  if n <= 0 then 0 else f(n-1) + fSum(n-1)
}

method problem6(n:nat) returns (a: int)
ensures a == fSum(n)
{
  a := 0;
  var k := 0;
  var x := 1;
  var y := 2;
  while k < n
  invariant /*R12_HINT:i1*/ true
  decreases /*R12_DECREASES:d1*/ (0 as int)
  {
    assert /*R12_HINT:a2*/ true;
    k := k + 1;
    assert /*R12_HINT:a3*/ true;
    assert /*R12_HINT:a4*/ true;
    a := a + x;
    assert /*R12_HINT:a5*/ true;
    assert /*R12_HINT:a6*/ true;

    x, y := y, k+1 + x*y;    
    assert /*R12_HINT:a7*/ true;
    assert /*R12_HINT:a8*/ true;
    assert /*R12_HINT:a9*/ true;
  }
  assert /*R12_HINT:a10*/ true;
}

