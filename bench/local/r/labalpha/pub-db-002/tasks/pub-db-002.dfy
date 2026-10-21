// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"i3"}]
// R12_SOURCE_SPANS: [{"symbol":"double_array_elements","start":4,"end":18}]
// R12 public task: dafnybench Clover_double_array_elements.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method double_array_elements(s: array<int>)
  modifies s
  ensures forall i :: 0 <= i < s.Length ==> s[i] == 2 * old(s[i])
{
  var i:= 0;
  while (i < s.Length)
    invariant /*R12_HINT:i1*/ true
    invariant /*R12_HINT:i2*/ true
    invariant /*R12_HINT:i3*/ true

  {
    s[i] :=  2 * s[i];
    i := i + 1;
  }
}