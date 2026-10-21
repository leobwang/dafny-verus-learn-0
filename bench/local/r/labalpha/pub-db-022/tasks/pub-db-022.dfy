// R12_HINT_SITES: [{"name":"d1","kind":"decreases"},{"name":"i1"},{"name":"i2"},{"name":"i3"},{"name":"i4"}]
// R12_SOURCE_SPANS: [{"symbol":"partition","start":10,"end":41}]
// R12 public task: dafnybench MIEIC_mfes_tmp_tmpq3ho7nve_exams_mt2_19_p5.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
type T = int // example

 // Partitions a nonempty array 'a', by reordering the elements in the array,
// so that elements smaller than a chosen pivot are placed to the left of the
// pivot, and values greater or equal than the pivot are placed to the right of 
// the pivot. Returns the pivot position.
method partition(a: array<T>) returns(pivotPos: int) 
    requires a.Length > 0
    ensures 0 <= pivotPos < a.Length
    ensures forall i :: 0 <= i < pivotPos ==> a[i] < a[pivotPos]
    ensures forall i :: pivotPos < i < a.Length ==> a[i] >= a[pivotPos]
    ensures multiset(a[..]) == multiset(old(a[..]))
    modifies a
{
    pivotPos := a.Length - 1; // chooses pivot at end of array 
    var i := 0;  // index that separates values smaller than pivot (0 to i-1), 
                 // and values greater or equal than pivot (i to j-1) 
    var j := 0;  // index to scan the array
 
    // Scan the array and move elements as needed
    while  j < a.Length-1 
        decreases /*R12_DECREASES:d1*/ (0 as int)
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
        invariant /*R12_HINT:i3*/ true
        invariant /*R12_HINT:i4*/ true
    {
      if a[j] < a[pivotPos] {
        a[i], a[j] := a[j], a[i];
        i := i + 1;
      }
      j := j+1;
    }
 
    // Swap pivot to the 'mid' of the array
    a[a.Length-1], a[i] := a[i], a[a.Length-1];
    pivotPos := i;  
}
