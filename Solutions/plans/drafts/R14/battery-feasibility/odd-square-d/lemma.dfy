module R14_Mechanics {
 ghost function PrefixMassR14(s:seq<int>):int
  decreases |s|
 {if s==[] then 0 else s[0]+PrefixMassR14(s[1..])}
 // item: R14.H1d
 // pair: R14.H1v
 lemma {:induction false} PrefixCapR14(s:seq<int>,cap:nat)
  requires forall i | 0<=i<|s| :: 0<=s[i]<=cap
  ensures 0<=PrefixMassR14(s)<=|s|*cap
  decreases |s|
 {// did: propagate the original bound through the exact tail indices.
  if |s|>0 {
   var tail:=s[1..];
   forall i | 0<=i<|tail|
    ensures 0<=tail[i]<=cap
   {assert tail[i]==s[i+1];}
   PrefixCapR14(tail,cap);
  }}
 opaque function OddTraceR14(n:nat):nat
  decreases n
 {if n==0 then 0 else OddTraceR14(n-1)+2*n-1}
 // item: R14.H2d
 // pair: R14.H2v
 lemma {:induction false} OddSquareR14(n:nat)
  ensures OddTraceR14(n)==n*n
  decreases n
 {// did: unfold the honest recursive trace and justify the smaller call.
  reveal OddTraceR14();
  if n>0 {
   OddSquareR14(n-1);
   assert n*n==(n-1)*(n-1)+2*n-1;
  }}
 // item: R14.H3d
 // pair: R14.H3v
 method ClearLowBitR14(x:bv32) returns(out:bv32)
  requires x>0
  ensures out==(x&(x-1)) && out<x
 {// did: compute the exact lower-bit clearing operation on the original word.
  out:=x&(x-1);}
}

module R14_BatteryCell {import opened R14_Mechanics
 lemma {:induction false} BatteryCellR14(n:nat)
 
 ensures OddTraceR14(n)==n*n
 {
 OddSquareR14(n);
 }
}
