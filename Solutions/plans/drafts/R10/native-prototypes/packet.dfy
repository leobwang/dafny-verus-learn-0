module R10_PacketPrototype {
 import opened RG_A1_Re
 import opened RG_A4_Norm
 datatype CountPacketR10 = CountPacketR10(expr:NormRe,ghost count:nat)
 type TypedPacketR10 = p:CountPacketR10 | p.count==NodeCount(p.expr) witness CountPacketR10(Empty,1)
 datatype PacketChoiceR10 = NoPacketR10 | HasPacketR10(packet:TypedPacketR10)
 function TryPacketR10(r:Re):PacketChoiceR10 {
  if Normal(r) then HasPacketR10(CountPacketR10(r,NodeCount(r))) else NoPacketR10
 } by method {
  if Normal(r) {
   ghost var measured:=NodeCount(r);
   return HasPacketR10(CountPacketR10(r,measured));
  } else {return NoPacketR10;}
 }
 function CatPacketR10(a:TypedPacketR10,b:TypedPacketR10):TypedPacketR10 {
  CountPacketR10(MkCat(a.expr,b.expr),NodeCount(MkCat(a.expr,b.expr)))
 } by method {
  var raw:=MkCat(a.expr,b.expr);
  ghost var cached:=if a.expr==Empty || b.expr==Empty then 1
   else if a.expr==Eps then b.count else if b.expr==Eps then a.count else 1+a.count+b.count;
  return CountPacketR10(raw,cached);
 }
 lemma {:induction false} NormalFixedR10(r:NormRe)
  ensures Norm(r)==r
  decreases r
 {
  match r
  case Alt(a,b) => NormalFixedR10(a);NormalFixedR10(b);
  case Cat(a,b) => NormalFixedR10(a);NormalFixedR10(b);
  case Star(a) => NormalFixedR10(a);
  case _ =>
 }
 lemma {:induction false} NormIdempotentR10(r:Re)
  ensures Norm(Norm(r))==Norm(r)
 {NormalFixedR10(Norm(r));}
 function NormalizePacketR10(r:Re):TypedPacketR10
  decreases r
 {CountPacketR10(Norm(r),NodeCount(Norm(r)))}
 by method {
  match r
  case Empty => var p:=TryPacketR10(r);assert p.HasPacketR10?;return p.packet;
  case Eps => var p:=TryPacketR10(r);assert p.HasPacketR10?;return p.packet;
  case Chr(_) => var p:=TryPacketR10(r);assert p.HasPacketR10?;return p.packet;
  case Alt(a,b) =>
   var left:=NormalizePacketR10(a);var right:=NormalizePacketR10(b);
   var raw:=MkAlt(left.expr,right.expr);
   ghost var cached:=NodeCount(raw);
   return CountPacketR10(raw,cached);
  case Cat(a,b) =>
   var left:=NormalizePacketR10(a);var right:=NormalizePacketR10(b);
   return CatPacketR10(left,right);
  case Star(a) =>
   var child:=NormalizePacketR10(a);var raw:=MkStar(child.expr);
   ghost var cached:=NodeCount(raw);
   return CountPacketR10(raw,cached);
 }
}
