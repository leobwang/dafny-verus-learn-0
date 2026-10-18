// R12_HINT_SITES: [{"name":"i1","identifiers":["Length","a","array","c","i","ii","remove_front"]},{"name":"i2","identifiers":["Length","a","array","c","i","ii","remove_front"]}]
// R12_SOURCE_SPANS: [{"symbol":"remove_front","start":4,"end":17}]
// R12 public task: dafnybench Clover_remove_front.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method remove_front(a:array<int>) returns (c:array<int>)
  requires a.Length>0
  ensures  a[1..] == c[..]
{
  c := new int[a.Length-1];
  var i:= 1;
  while (i < a.Length)
    invariant /*R12_HINT:i1*/ true
    invariant /*R12_HINT:i2*/ true
  {
    c[i-1] := a[i];
    i:=i+1;
  }
}
