// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"i3"},{"name":"i4"}]
// R12_SOURCE_SPANS: [{"symbol":"selectionSort","start":18,"end":35}]
// R12 public task: dafnybench feup-mfes_tmp_tmp6_a1y5a5_examples_SelectionSort.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
/* 
* Formal verification of the selection sort algorithm with Dafny.
* FEUP, MIEIC, MFES, 2020/21.
*/

// Checks if array 'a' is sorted between positions 'from' (inclusive) and 'to' (exclusive).
predicate isSorted(a: array<real>, from: nat, to: nat)
  requires 0 <= from <= to <= a.Length
  reads a
{
    forall i, j :: from <= i < j < to ==> a[i] <= a[j] 
}

// Sorts array 'a' using the selection sort algorithm.
method selectionSort(a: array<real>)
  modifies a
  ensures isSorted(a, 0, a.Length) 
  ensures multiset(a[..]) == multiset(old(a[..]))
{
    var i := 0; 
    while i < a.Length - 1 
      invariant /*R12_HINT:i1*/ true
      invariant /*R12_HINT:i2*/ true
      invariant /*R12_HINT:i3*/ true
      invariant /*R12_HINT:i4*/ true
    {
        var j := findMin(a, i, a.Length);
        a[i], a[j] := a[j], a[i];
        i := i + 1;
    }

}

// Finds the position of a miminum value in non-empty subarray 'a' between positions 
// 'from' (inclusive) and 'to' (exclusive)
method findMin(a: array<real>, from: nat, to: nat) returns(index: nat)
  requires 0 <= from < to <= a.Length
  ensures from <= index < to
  ensures forall k :: from <= k < to ==> a[k] >= a[index]
{
    var i := from + 1;
    index := from; // position of min up to position i (excluded)
    while i < to
      decreases a.Length - i
      invariant from <= index < i <= to
      invariant forall k :: from <= k < i ==> a[k] >= a[index]  
    {
        if a[i] < a[index] {
            index := i;
        }
        i := i + 1;
    }
}

method testSelectionSort() {
  var a := new real[5] [9.0, 4.0, 6.0, 3.0, 8.0];
  assert a[..] == [9.0, 4.0, 6.0, 3.0, 8.0]; // to help Dafny ...
  selectionSort(a);
  assert a[..] == [3.0, 4.0, 6.0, 8.0, 9.0];
}

method testFindMin() {
  var a := new real[5] [9.0, 5.0, 6.0, 4.0, 8.0];
  var m := findMin(a, 0, 5);
  assert a[3] == 4.0; // to help Dafny ... 
  assert m == 3;
}
