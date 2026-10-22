// Topic (e) dev task pd-d104-q32d (Q32, public; QPLAN §34.4, D76).
// Source: dafnybench Clover_online_max.dfy (Apache-2.0 (DafnyBench)); the set's hints_removed form, unchanged.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
method onlineMax(a: array<int>, x: int) returns (ghost m:int, p:int)
  requires 1<=x<a.Length
  requires a.Length!=0
  ensures x<=p<a.Length
  ensures forall i::0<=i<x==> a[i]<=m
  ensures exists i::0<=i<x && a[i]==m
  ensures x<=p<a.Length-1 ==> (forall i::0<=i<p ==> a[i]<a[p])
  ensures (forall i::x<=i<a.Length && a[i]<=m) ==> p==a.Length-1
{
  p:= 0;
  var best := a[0];
  var i:=1;
  while i<x
    invariant 0<=i<=x
    invariant forall j::0<=j<i==> a[j]<=best
    invariant exists j::0<=j<i && a[j]==best
  {
    if a[i]>best{
      best:=a[i];
    }
    i:=i+1;
  }
  m:=best;
  i:=x;
  while i<a.Length
    invariant x<=i<=a.Length
    invariant forall j::x<=j<i ==> a[j]<=m
  {
    if a[i]>best{
      p:=i;
      return;
    }
    i:=i+1;
  }
  p:=a.Length-1;

}

