module R09_CursorPrototype {
 import P = R09_ParserPrototype
 import opened RG_A3_Syntax
 class EffectCursorR09 {
  var text:seq<char>
  var position:nat
  constructor(input:seq<char>,start:nat)
   requires start<=|input|
   ensures text==input && position==start
  {text:=input;position:=start;}
 }
 method ReadBoundR09(c:char,pos:nat,len:nat) returns (res:Res<nat>)
  requires pos<=len
  ensures res.Ok? ==> BoundChar(c) && res.value==BoundVal(c)
  ensures res.Err? ==> !BoundChar(c) && res.pos==pos
 {
  if !BoundChar(c) {res:=Err(pos,"expected a bound '0'..'9'");}
  else {res:=Ok(BoundVal(c));}
 }
 method ReadBoundCursorR09(cur:EffectCursorR09) returns (res:Res<nat>)
  requires cur.position<|cur.text|
  modifies cur
  ensures cur.text==old(cur.text)
  ensures cur.position==old(cur.position)+1
  ensures res.Ok? ==> BoundChar(cur.text[old(cur.position)]) && res.value==BoundVal(cur.text[old(cur.position)])
  ensures res.Err? ==> !BoundChar(cur.text[old(cur.position)]) && res.pos==old(cur.position)
 {
  var start:=cur.position;
  cur.position:=start+1;
  var n :- ReadBoundR09(cur.text[start],start,|cur.text|);
  res:=Ok(n);
 }
 method CountedCursorR09(cur:EffectCursorR09,a:Syn) returns (res:Res<Syn>)
  requires cur.position<|cur.text| && cur.text[cur.position]=='{'
  requires WF(a,|cur.text|) && a.hi==cur.position && a.lo<cur.position
  modifies cur
  ensures cur.text==old(cur.text)
  ensures old(cur.position)<=cur.position<=|cur.text|
  ensures res.Ok? ==> WF(res.value,|cur.text|) && res.value.lo==a.lo && res.value.hi==cur.position && old(cur.position)<cur.position
  ensures res.Err? ==> cur.position==old(cur.position) && res.pos<=|cur.text|
  ensures forall n:nat,m:nat,k:nat :: CountedAt(cur.text,old(cur.position),n,m,k) ==> res==Ok(SRep(a,n,m,a.lo,k)) && cur.position==k
 {
  var start:=cur.position;
  var pair :- P.Counted(cur.text,a,start);
  cur.position:=pair.1;
  res:=Ok(pair.0);
 }
}
