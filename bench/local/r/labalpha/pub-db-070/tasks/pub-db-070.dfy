// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"i3"},{"name":"d1","kind":"decreases"},{"name":"i4"},{"name":"i5"},{"name":"i6"},{"name":"i7"},{"name":"i8"},{"name":"i9"},{"name":"d2","kind":"decreases"}]
// R12_SOURCE_SPANS: [{"symbol":"BubbleSort","start":21,"end":55}]
// R12 public task: dafnybench Dafny-programs_tmp_tmpnso9eu7u_Algorithms + sorting_bubble-sort.dfy (Apache-2.0 (set licence; per-file upstream licence not recorded)); proof annotations moved into hint sites.
/*
Bubble Sort is the simplest sorting algorithm that works by 
repeatedly swapping the adjacent elements if they are in wrong order.
*/

predicate sorted_between(A:array<int>, from:int, to:int)
    reads A
{
    forall i, j :: 0 <= i <= j < A.Length && from <= i <= j <= to ==> A[i] <= A[j]
}

predicate sorted(A:array<int>)
    reads A
{
    sorted_between(A, 0, A.Length-1)
}

method BubbleSort(A:array<int>)
    modifies A
    ensures sorted(A)
    ensures multiset(A[..]) == multiset(old(A[..]))
{
    var N := A.Length;
    var i := N-1;
    while 0 < i
        invariant /*R12_HINT:i1*/ true
        invariant /*R12_HINT:i2*/ true
        invariant /*R12_HINT:i3*/ true
        decreases /*R12_DECREASES:d1*/ (0 as int)
    {
        print A[..], "\n";
        var j := 0;
        while j < i
            invariant /*R12_HINT:i4*/ true
            invariant /*R12_HINT:i5*/ true
            invariant /*R12_HINT:i6*/ true
            invariant /*R12_HINT:i7*/ true
            invariant /*R12_HINT:i8*/ true
            invariant /*R12_HINT:i9*/ true
            decreases /*R12_DECREASES:d2*/ (0 as int)
        {
            if A[j] > A[j+1]
            {
                A[j], A[j+1] := A[j+1], A[j];
                print A[..], "\n";
            }
            j := j+1;
        } 
        i := i-1;
        print "\n";
    }
}

method Main() {
    var A := new int[10];
    A[0], A[1], A[2], A[3], A[4], A[5], A[6], A[7], A[8], A[9] := 2, 4, 6, 15, 3, 19, 17, 16, 18, 1;
    BubbleSort(A);
    print A[..];
}

/* Explanation:

invariant forall n, m :: 0 <= n <= i <m <N ==> A [n] <= A [m]
     // A is ordered for each pair of elements such that
     // the first element belongs to the left partition of i
     // and the second element belongs to the right partition of i

invariant forall n :: 0 <= n <= j ==> A [n] <= A [j]
     // There is a variable defined by the value that the array takes at position j
     // Therefore, each value that the array takes for all elements from 0 to j
     // They are less than or equal to the value of the variable
*/
