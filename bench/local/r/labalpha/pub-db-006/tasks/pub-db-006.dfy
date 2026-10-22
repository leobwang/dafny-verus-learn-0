// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"i3"},{"name":"i4"},{"name":"i5"}]
// R12_SOURCE_SPANS: [{"symbol":"Getmini","start":4,"end":36}]
// R12 public task: dafnybench SENG2011_tmp_tmpgk5jq85q_exam_ex2.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
method Getmini(a:array<int>) returns(mini:nat) 
requires a.Length > 0
ensures 0 <= mini < a.Length // mini is an index of a
ensures forall x :: 0 <= x < a.Length ==> a[mini] <= a[x] // a[mini] is the minimum value
ensures forall x :: 0 <= x < mini ==> a[mini] < a[x] // a[mini] is the first min
{
    // find mini
    var min:int := a[0];
    var i:int := 0;
    while i < a.Length
    invariant /*R12_HINT:i1*/ true
    invariant /*R12_HINT:i2*/ true
    invariant /*R12_HINT:i3*/ true
    {
        if a[i] < min {
            min := a[i];
        }
        i := i + 1;
    }

    //assert min in a[..]; // min is in a -> it will be found by this loop
    // find first occurance
    var k:int := 0;
    while k < a.Length 
    invariant /*R12_HINT:i4*/ true
    invariant /*R12_HINT:i5*/ true
    {
        if a[k] == min {
            return k;
        }
        k := k + 1;
    }
}

/*
method check() {
    var data := new int[][9,5,42,5,5]; // minimum 5 first at index 1
var mini := Getmini(data);
//print mini;
assert mini==1;

}
*/

