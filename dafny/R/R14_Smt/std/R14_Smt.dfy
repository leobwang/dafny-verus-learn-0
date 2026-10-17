/*! R14 — SMT mechanics. Three counted native holes per language.
H1 propagates quantified bounds through an original trace. H2 proves a property
of an honestly recursive opaque definition. H3 keeps exact32bitword behavior.
D H1/H2 explicitly disable induction: maximal automation solves their empty
forms. Preserve these levers and all original domains; do not infer toolchain
correctness from an automation result. The12assertion battery is separate.
*/
// item: R14.C1d write:trigger
// Supply a matching term covering every quantified variable, using R14-owned subjects.
// item: R14.C2d write:fuel
// A fixed unfolding budget is not unbounded induction; preserve the original recursion.
// item: R14.C3d write:bit-vector
// Bit-vector arithmetic and mathematical integer arithmetic have different operations.
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
