// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"i3"},{"name":"i4"},{"name":"i5"},{"name":"i6"},{"name":"i7"},{"name":"i8"}]
// R12_SOURCE_SPANS: [{"symbol":"SelectionSort","start":6,"end":46}]
// R12 public task: dafnybench Dafny_Verify_tmp_tmphq7j0row_dataset_detailed_examples_SelectionSort.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
// Works by dividing the input list into two parts: sorted and unsorted. At the beginning, 
// the sorted part is empty and the unsorted part contains all the elements.
method SelectionSort(a: array<int>)
  modifies a
  // Ensures the final array is sorted in ascending order
  ensures forall i,j :: 0 <= i < j < a.Length ==> a[i] <= a[j]
  // Ensures that the final array has the same elements as the initial array
  ensures multiset(a[..]) == old(multiset(a[..]))
{
  var n := 0;
  while n != a.Length
    // Ensures that n is always within the bounds of the array
    invariant /*R12_HINT:i1*/ true
    // Guarantees that the portion of the array up to index n is sorted
    invariant /*R12_HINT:i2*/ true
    // Guarantees that all elements before n are less than or equal to elements after and at n
    invariant /*R12_HINT:i3*/ true
    // Ensures that the array still contains the same elements as the initial array
    invariant /*R12_HINT:i4*/ true
  {
    var mindex, m := n, n;
    while m != a.Length
      // Ensures that mindex is always within the bounds of the array
      invariant /*R12_HINT:i5*/ true
      invariant /*R12_HINT:i6*/ true
      // Ensures that a[mindex] is the smallest element from a[n] to a[m-1]
      invariant /*R12_HINT:i7*/ true
      // Ensures that the array still contains the same elements as the initial array
      invariant /*R12_HINT:i8*/ true
    {
      if a[m] < a[mindex] {
        mindex := m;
      }
      m := m + 1;
    }
    // Swaps the first element of the unsorted array with the current smallest element
    // in the unsorted part if it is smaller
    if a[mindex] < a[n] {
      a[mindex], a[n] := a[n], a[mindex];
    }
    n := n + 1;
  }  
}
