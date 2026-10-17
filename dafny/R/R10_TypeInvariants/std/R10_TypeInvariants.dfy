/*! R10 — Invariants in types. Frozen A1–A4 interfaces.
The packet carries a normal regex with erased node-count evidence.
H1 accepts precisely normal inputs; H2 rebuilds packet evidence; H3 proves
normal fixed points; H4 supplies compiled normalization for the ghost model.
Shape, exact normalization, and language preservation are separate promises.
Commit predictions before enabling checks. Original statements stay frozen.
*/
module R10_TypeInvariants {
 import opened RG_A1_Re
 import opened RG_A4_Norm
 // item: R10.W1d
 datatype CountPacketR10 = CountPacketR10(expr:NormRe,ghost count:nat)
 type TypedPacketR10 = p:CountPacketR10 | p.count==NodeCount(p.expr) witness CountPacketR10(Empty,1)
 datatype PacketChoiceR10 = NoPacketR10 | HasPacketR10(packet:TypedPacketR10)
 // item: R10.H1d
// pair: R10.H1v
// uses: subset-type, by-method, ghost
function TryPacketR10(r:Re):PacketChoiceR10 {
  if Normal(r) then HasPacketR10(CountPacketR10(r,NodeCount(r))) else NoPacketR10
 } by method { assume false; }
 // item: R10.H2d
// pair: R10.H2v
// uses: subset-type, by-method, ghost
function CatPacketR10(a:TypedPacketR10,b:TypedPacketR10):TypedPacketR10 {
  CountPacketR10(MkCat(a.expr,b.expr),NodeCount(MkCat(a.expr,b.expr)))
 } by method { assume false; }
 // item: R10.H3d
// pair: R10.H3v
lemma {:induction false} NormalFixedR10(r:NormRe)
  ensures Norm(r)==r
  decreases r
 { assume false; }
 lemma {:induction false} NormIdempotentR10(r:Re)
  ensures Norm(Norm(r))==Norm(r)
 {NormalFixedR10(Norm(r));}
 // item: R10.H4d
// pair: R10.H4v
function NormalizePacketR10(r:Re):TypedPacketR10
  decreases r
 {CountPacketR10(Norm(r),NodeCount(Norm(r)))}
 by method { assume false; }
 // item: R10.W2d
 function RuntimeShapeR10(r:Re):bool {Normal(r)}
 // item: R10.W3d
 lemma ReplaceRightR10(a:Re,b1:Re,b2:Re,s:seq<char>)
  requires forall t :: Matches(b1,t)<==>Matches(b2,t)
  ensures Matches(Cat(a,b1),s)<==>Matches(Cat(a,b2),s)
 {CatCongRight(a,b1,b2,s);}
}

// item: R10.P3dv verdict
// Runtime option then precondition-only call. D:<x>,<y> V:<x>,<y>.
// SLOT: CHECK P3dv
// item: R10.P5dv verdict
// Shape-only output then original language promise. D:<x>,<y> V:<x>,<y>.
// SLOT: CHECK P5dv

