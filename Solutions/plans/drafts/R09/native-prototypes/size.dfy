module R09_SizePrototype {
 import opened RG_A1_Re
 import opened RG_A3_Syntax
 ghost function RangeNodesR09(lo:char,hi:char):nat
  requires lo<=hi && (hi as int)<ClassMax
 {2*((hi as int)-(lo as int))+1}
 ghost function ClassNodesR09(xs:seq<RG_A2_Deriv.CRange>):nat
  requires ClassLowered(xs)
  decreases xs
 {if xs==[] then 1 else 1+RangeNodesR09(xs[0].lo,xs[0].hi)+ClassNodesR09(xs[1..])}
 ghost function LoweringNodesR09(t:Syn,len:nat):nat
  requires WF(t,len)
  decreases t
 {
  match t
  case SEps(_,_) => 1
  case SChr(_,_,_) => 1
  case SClass(cc,_,_) => ClassNodesR09(cc)
  case SAlt(a,b,_,_) => 1+LoweringNodesR09(a,len)+LoweringNodesR09(b,len)
  case SCat(a,b,_,_) => 1+LoweringNodesR09(a,len)+LoweringNodesR09(b,len)
  case SStar(a,_,_) => 1+LoweringNodesR09(a,len)
  case SPlus(a,_,_) => 2+2*LoweringNodesR09(a,len)
  case SOpt(a,_,_) => 2+LoweringNodesR09(a,len)
  case SGroup(a,_,_) => LoweringNodesR09(a,len)
  case SRep(a,n,m,_,_) => 3+n*(LoweringNodesR09(a,len)+1)+(m-n)*(LoweringNodesR09(a,len)+3)
 }
 lemma CopiesNodesR09(r:Re,k:nat)
  ensures NodeCount(Copies(r,k))==1+k*(NodeCount(r)+1)
  decreases k
 {if k>0 {CopiesNodesR09(r,k-1);}}
 lemma OptionalNodesR09(r:Re,k:nat)
  ensures NodeCount(CopiesUpTo(r,k))==1+k*(NodeCount(r)+3)
  decreases k
 {if k>0 {OptionalNodesR09(r,k-1);}}
 lemma RangeNodesCorrectR09(lo:char,hi:char)
  requires lo<=hi && (hi as int)<ClassMax
  ensures NodeCount(RangeRe(lo,hi))==RangeNodesR09(lo,hi)
  decreases hi as int-lo as int
 {if lo<hi {RangeNodesCorrectR09((lo as int+1) as char,hi);}}
 lemma ClassNodesCorrectR09(xs:seq<RG_A2_Deriv.CRange>)
  requires ClassLowered(xs)
  ensures NodeCount(ClassToRe(xs))==ClassNodesR09(xs)
  decreases xs
 {if xs!=[] {RangeNodesCorrectR09(xs[0].lo,xs[0].hi);ClassNodesCorrectR09(xs[1..]);}}
 lemma LoweringNodesCorrectR09(t:Syn,len:nat)
  requires WF(t,len)
  ensures NodeCount(Lower(t,len))==LoweringNodesR09(t,len)
  decreases t
 {
  match t
  case SEps(_,_) =>
  case SChr(_,_,_) =>
  case SClass(cc,_,_) => ClassNodesCorrectR09(cc);
  case SAlt(a,b,_,_) => LoweringNodesCorrectR09(a,len);LoweringNodesCorrectR09(b,len);
  case SCat(a,b,_,_) => LoweringNodesCorrectR09(a,len);LoweringNodesCorrectR09(b,len);
  case SStar(a,_,_) => LoweringNodesCorrectR09(a,len);
  case SPlus(a,_,_) => LoweringNodesCorrectR09(a,len);
  case SOpt(a,_,_) => LoweringNodesCorrectR09(a,len);
  case SGroup(a,_,_) => LoweringNodesCorrectR09(a,len);
  case SRep(a,n,m,_,_) =>
   LoweringNodesCorrectR09(a,len);
   CopiesNodesR09(Lower(a,len),n);
   OptionalNodesR09(Lower(a,len),m-n);
 }
}
