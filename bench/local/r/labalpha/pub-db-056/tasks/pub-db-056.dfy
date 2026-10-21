// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"i3"},{"name":"i4"},{"name":"i5"}]
// R12_SOURCE_SPANS: [{"symbol":"appendArray","start":4,"end":28}]
// R12 public task: dafnybench dafny-exercise_tmp_tmpouftptir_appendArray.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method appendArray(a: array<int>, b: array<int>) returns (c: array<int>)
ensures c.Length == a.Length + b.Length
ensures forall i :: 0 <= i < a.Length ==> a[i] == c[i]
ensures forall i :: 0 <= i < b.Length ==> b[i] == c[a.Length + i]
{
	c := new int[a.Length + b.Length];
	
	var i := 0;
	while i < a.Length
	invariant /*R12_HINT:i1*/ true
	invariant /*R12_HINT:i2*/ true
	{
		c[i] := a[i];
		i := i + 1;
	}
	
	while i < b.Length + a.Length
	invariant /*R12_HINT:i3*/ true
	invariant /*R12_HINT:i4*/ true
	invariant /*R12_HINT:i5*/ true
	{
		c[i] := b[i - a.Length];
		i := i + 1;
	}
}

