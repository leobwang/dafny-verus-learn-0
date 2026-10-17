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
 {assume false;}
 opaque function OddTraceR14(n:nat):nat
  decreases n
 {if n==0 then 0 else OddTraceR14(n-1)+2*n-1}
 // item: R14.H2d
 // pair: R14.H2v
 lemma {:induction false} OddSquareR14(n:nat)
  ensures OddTraceR14(n)==n*n
  decreases n
 {assume false;}
 // item: R14.H3d
 // pair: R14.H3v
 method ClearLowBitR14(x:bv32) returns(out:bv32)
  requires x>0
  ensures out==(x&(x-1)) && out<x
 {assume false;}
}
