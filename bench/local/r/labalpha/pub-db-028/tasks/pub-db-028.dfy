// R12_HINT_SITES: [{"name":"i1","identifiers":["Length","MaxArray","a","array","i","j","max"]},{"name":"i2","identifiers":["Length","MaxArray","a","array","i","j","max"]},{"name":"i3","identifiers":["Length","MaxArray","a","array","i","j","max"]}]
// R12_SOURCE_SPANS: [{"symbol":"MaxArray","start":4,"end":21}]
// R12 public task: dafnybench dafny-exercise_tmp_tmpouftptir_maxArray.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method MaxArray(a: array<int>) returns (max:int)
requires a.Length > 0
ensures forall i :: 0 <= i < a.Length ==> a[i] <= max
ensures exists i :: 0 <= i < a.Length && a[i] == max
{
	var i: nat := 1;
	max := a[0];
	while i < a.Length
	invariant /*R12_HINT:i1*/ true
	invariant /*R12_HINT:i2*/ true
	invariant /*R12_HINT:i3*/ true
	{
		if (a[i] > max) {
			max := a[i];
		}
		i := i + 1;
	}
}

method Main() {
	var arr : array<int> := new int[][-11,2,42,-4];
	var res := MaxArray(arr);
	assert arr[0] == -11 && arr[1] == 2 && arr[2] == 42 && arr[3] == -4;
	assert res == 42;
}

