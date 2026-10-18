// Reference Solution.
/*! R09 — Effects. Frozen A1/A1b/A2/A3; finite scalar-position parser.
Six holes per language: T1 cursor read, H1 counted suffix, H2 class body,
H3 bounded expansion cost, H4 repetition interval proof, H5 cursor update.
Complete infrastructure checks the logical tree-node cap before allocating
expanded regexes. Positions count Unicode scalars, classes are below 0xD800,
finite counts are one character. Class ranges are A2's u32 code-point ranges,
read through A2's accessor ClassRanges. Zero copies skip an unused oversized child.
Native proofs and finite compiled differential checks are separate evidence.
Live Claude/calibration remains recorded D45 debt, never a pass.
*/
module R09_Size {
 import opened RG_A1_Re
 import opened RG_A3_Syntax
 ghost function RangeNodesR09(lo: RG_A2_Deriv.Cp, hi: RG_A2_Deriv.Cp): nat
  requires lo <= hi && (hi as int) < ClassMax
 {
  2 * ((hi as int) - (lo as int)) + 1
 }
 ghost function ClassNodesR09(xs: seq<RG_A2_Deriv.CRange>): nat
  requires RangesLowered(xs)
  decreases xs
 {
  if xs == [] then 1 else 1 + RangeNodesR09(xs[0].lo, xs[0].hi) + ClassNodesR09(xs[1..])
 }
 ghost function LoweringNodesR09(t:Syn,len:nat):nat
  requires WF(t,len)
  decreases t
 {
  match t
  case SEps(_,_) => 1
  case SChr(_,_,_) => 1
  case SClass(cc,_,_) => ClassNodesR09(RG_A2_Deriv.ClassRanges(cc))
  case SAlt(a,b,_,_) => 1+LoweringNodesR09(a,len)+LoweringNodesR09(b,len)
  case SCat(a,b,_,_) => 1+LoweringNodesR09(a,len)+LoweringNodesR09(b,len)
  case SStar(a,_,_) => 1+LoweringNodesR09(a,len)
  case SPlus(a,_,_) => 2+2*LoweringNodesR09(a,len)
  case SOpt(a,_,_) => 2+LoweringNodesR09(a,len)
  case SGroup(a,_,_) => LoweringNodesR09(a,len)
  case SRep(a,n,m,_,_) => RepNodesR09(LoweringNodesR09(a,len),n,m)
 }
 // The logical size of a counted repetition whose child has c nodes.
 ghost function RepNodesR09(c: nat, n: nat, m: nat): nat
  requires n <= m
 {
  3 + n * (c + 1) + (m - n) * (c + 3)
 }
 lemma CopiesNodesR09(r:Re,k:nat)
  ensures NodeCount(Copies(r,k))==1+k*(NodeCount(r)+1)
  decreases k
 {if k>0 {CopiesNodesR09(r,k-1);}}
 lemma OptionalNodesR09(r:Re,k:nat)
  ensures NodeCount(CopiesUpTo(r,k))==1+k*(NodeCount(r)+3)
  decreases k
 {if k>0 {OptionalNodesR09(r,k-1);}}
 lemma RangeNodesCorrectR09(lo: RG_A2_Deriv.Cp, hi: RG_A2_Deriv.Cp)
  requires lo <= hi && (hi as int) < ClassMax
  ensures NodeCount(RangeRe(lo, hi)) == RangeNodesR09(lo, hi)
  decreases hi as int - lo as int
 {
  if lo < hi {
   RangeNodesCorrectR09(lo + 1, hi);
  }
 }
 lemma ClassNodesCorrectR09(xs: seq<RG_A2_Deriv.CRange>)
  requires RangesLowered(xs)
  ensures NodeCount(RangesToRe(xs)) == ClassNodesR09(xs)
  decreases xs
 {
  if xs != [] {
   RangeNodesCorrectR09(xs[0].lo, xs[0].hi);
   ClassNodesCorrectR09(xs[1..]);
  }
 }
 lemma LoweringNodesCorrectR09(t:Syn,len:nat)
  requires WF(t,len)
  ensures NodeCount(Lower(t,len))==LoweringNodesR09(t,len)
  decreases t
 {
  match t
  case SEps(_,_) =>
  case SChr(_,_,_) =>
  case SClass(cc,_,_) => ClassNodesCorrectR09(RG_A2_Deriv.ClassRanges(cc));
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
module R09_ParserMirror {
 import opened RG_A1_Re
 import opened RG_A3_Syntax
 import opened R09_Size
 import P = R09_Parser
 // These are the existing parser's guarantees, not a complete grammar model.
 ghost predicate OriginalContractR09(s:seq<char>,r:Res<Syn>) {
  (r.Ok? ==> WF(r.value,|s|) && r.value.lo==0 && r.value.hi==|s|) &&
  (r.Err? ==> r.pos<=|s|) &&
  (NoSpecialFrom(s,0) ==> r.Ok? && Matches(Lower(r.value,|s|),s) && LoweringNodesR09(r.value,|s|)==(if |s|==0 then 1 else 2*|s|-1))
 }
 ghost predicate TranscribedMirrorR09(s:seq<char>,r:Res<Syn>) {
  match r
  case Err(at,_) => at<=|s| && !NoSpecialFrom(s,0)
  case Ok(t) => (WF(t,|s|) && t.lo==0 && t.hi==|s| &&
   (NoSpecialFrom(s,0) ==> Matches(Lower(t,|s|),s) && LoweringNodesR09(t,|s|)==(if |s|==0 then 1 else 2*|s|-1)))
 }
 // Equivalence is explicitly relative to the transcribed mirror.
 lemma {:induction false} BothMirrorImplicationsR09(s:seq<char>,r:Res<Syn>)
  ensures OriginalContractR09(s,r) ==> TranscribedMirrorR09(s,r)
  ensures TranscribedMirrorR09(s,r) ==> OriginalContractR09(s,r)
 {match r case Err(_,_) => case Ok(_) =>}
 method ParseRelativeMirrorR09(s:seq<char>) returns (r:Res<Syn>)
  ensures OriginalContractR09(s,r) && TranscribedMirrorR09(s,r)
 {
  r:=P.Parse(s);
  BothMirrorImplicationsR09(s,r);
 }
}

module R09_Parser {
 import opened RG_A1_Re
 import opened RG_A1b_Facts
 import opened RG_A2_Deriv
 import opened RG_A3_Syntax
 import opened R09_Size
 lemma LiteralAppendR09(a:Re,u:seq<char>,c:char)
  requires Matches(a,u)
  ensures Matches(Cat(a,Chr(c)),u+[c])
 {
  var w:=u+[c];assert w[..|u|]==u && w[|u|..]==[c];
 }
  // item: R09.H1d
 // pair: R09.H1v
method Counted(s:seq<char>,a:Syn,j:nat) returns (res:Res<(Syn,nat)>)
  requires j<|s| && s[j]=='{' && WF(a,|s|) && a.hi==j && a.lo<j
  ensures res.Ok? ==> j<res.value.1<=|s| && WF(res.value.0,|s|) && res.value.0.lo==a.lo && res.value.0.hi==res.value.1
  ensures res.Err? ==> res.pos<=|s|
  ensures forall n:nat,m:nat,k:nat :: CountedAt(s,j,n,m,k) ==> res==Ok((SRep(a,n,m,a.lo,k),k))
 {
  // did: implement the frozen R09.H1d statement using the printed worked interfaces.

  if j+1>=|s| {res:=Err(j+1,"expected a bound");}
  else if !BoundChar(s[j+1]) {res:=Err(j+1,"expected a bound '0'..'9'");}
  else if j+2>=|s| {res:=Err(j+2,"expected '}' or ','");}
  else if s[j+2]=='}' {var n:=BoundVal(s[j+1]);res:=Ok((SRep(a,n,n,a.lo,j+3),j+3));}
  else if s[j+2]!=',' {res:=Err(j+2,"expected '}' or ','");}
  else if j+3>=|s| || !BoundChar(s[j+3]) {res:=Err(j+3,"expected a bound '0'..'9'");}
  else if j+4>=|s| || s[j+4]!='}' {res:=Err(j+4,"expected '}'");}
  else {
   var n:=BoundVal(s[j+1]);var m:=BoundVal(s[j+3]);
   if m<n {res:=Err(j+3,"upper bound below lower bound");}
   else {res:=Ok((SRep(a,n,m,a.lo,j+5),j+5));}
  }
 }
  // item: R09.H2d
 // pair: R09.H2v
method ClassItems(s:seq<char>,i:nat,acc:CharClass) returns (res:Res<(CharClass,nat)>)
  requires i<=|s| && ClassValid(acc) && ClassLowered(acc)
  ensures res.Ok? ==> i<res.value.1<=|s| && ClassValid(res.value.0) && ClassLowered(res.value.0)
  ensures res.Err? ==> res.pos<=|s|
  ensures forall k:nat :: SimpleClassBody(s,i,k) ==> res.Ok? && res.value.1==k+1
 {
  // did: implement the frozen R09.H2d statement using the printed worked interfaces.

  var j := i;
  var ranges := acc;
  while j < |s|
   invariant i <= j <= |s| && ClassValid(ranges) && ClassLowered(ranges)
   invariant forall k: nat :: SimpleClassBody(s, i, k) ==> SimpleClassBody(s, j, k)
   decreases |s| - j
  {
   if s[j] == ']' {
    res := Ok((ranges, j + 1));
    return;
   }
   var escaped := s[j] == '\\' && j + 1 < |s|;
   var c := if escaped then s[j + 1] else s[j];
   var k := if escaped then j + 2 else j + 1;
   if k + 1 < |s| && s[k] == '-' && s[k + 1] != ']' {
    var d := s[k + 1];
    if d < c {
     res := Err(k + 1, "empty range");
     return;
    }
    if d as int >= ClassMax {
     res := Err(k + 1, "class character out of range");
     return;
    }
    var next := ClassInsert(ranges, CRange(Code(c), Code(d)));
    assert ClassLowered(next) by {
     assert ClassBelow(ranges, ClassMax);
     ClassRangesFacts(next);
    }
    ranges := next;
    j := k + 2;
   } else {
    if c as int >= ClassMax {
     res := Err(j, "class character out of range");
     return;
    }
    var next := ClassInsert(ranges, CRange(Code(c), Code(c)));
    assert ClassLowered(next) by {
     assert ClassBelow(ranges, ClassMax);
     ClassRangesFacts(next);
    }
    ranges := next;
    j := k;
   }
  }
  res := Err(j, "unclosed class");
 }
 // item: R09.W3d
 method ParseAlt(s:seq<char>,i:nat) returns (res:Res<PR>)
  requires i<=|s|
  ensures res.Ok? ==> i<=res.value.j<=|s| && WF(res.value.t,|s|) && res.value.t.lo==i && res.value.t.hi==res.value.j
  ensures res.Err? ==> res.pos<=|s|
  ensures NoSpecialFrom(s,i) ==> res.Ok? && res.value.j==|s| && Matches(Lower(res.value.t,|s|),s[i..]) && LoweringNodesR09(res.value.t,|s|)==(if i==|s| then 1 else 2*(|s|-i)-1)
  decreases |s|-i,3
 {
  var p :- ParseCat(s,i);var x:=p.t;var j:=p.j;
  while j<|s| && s[j]=='|'
   invariant i<=j<=|s| && WF(x,|s|) && x.lo==i && x.hi==j
   invariant NoSpecialFrom(s,i) ==> j==|s| && Matches(Lower(x,|s|),s[i..]) && LoweringNodesR09(x,|s|)==(if i==|s| then 1 else 2*(|s|-i)-1)
   decreases |s|-j
  {
   var q :- ParseCat(s,j+1);
   x:=SAlt(x,q.t,i,q.j);j:=q.j;
  }
  res:=Ok(PR(x,j));
 }
 method ParseCat(s:seq<char>,i:nat) returns (res:Res<PR>)
  requires i<=|s|
  ensures res.Ok? ==> i<=res.value.j<=|s| && WF(res.value.t,|s|) && res.value.t.lo==i && res.value.t.hi==res.value.j
  ensures res.Err? ==> res.pos<=|s|
  ensures NoSpecialFrom(s,i) ==> res.Ok? && res.value.j==|s| && Matches(Lower(res.value.t,|s|),s[i..]) && LoweringNodesR09(res.value.t,|s|)==(if i==|s| then 1 else 2*(|s|-i)-1)
  decreases |s|-i,2
 {
  var x:=SEps(i,i);var j:=i;var first:=true;
  while j<|s| && s[j]!=')' && s[j]!='|'
   invariant i<=j<=|s| && WF(x,|s|) && x.lo==i && x.hi==j
   invariant first <==> j==i
   invariant NoSpecialFrom(s,i) ==> NoSpecialFrom(s,j) && Matches(Lower(x,|s|),s[i..j]) && LoweringNodesR09(x,|s|)==(if j==i then 1 else 2*(j-i)-1)
   decreases |s|-j
  {
   var q :- ParsePost(s,j);
   if NoSpecialFrom(s,i) {
    assert q.t==SChr(s[j],j,j+1) && q.j==j+1;
    assert s[i..j+1]==s[i..j]+[s[j]];
    LiteralAppendR09(Lower(x,|s|),s[i..j],s[j]);
   }
   x:=if first then q.t else SCat(x,q.t,i,q.j);first:=false;j:=q.j;
  }
  if NoSpecialFrom(s,i) { assert j==|s|; assert s[i..j]==s[i..]; }
  res:=Ok(PR(x,j));
 }
 method ParsePost(s:seq<char>,i:nat) returns (res:Res<PR>)
  requires i<|s|
  ensures res.Ok? ==> i<res.value.j<=|s| && WF(res.value.t,|s|) && res.value.t.lo==i && res.value.t.hi==res.value.j
  ensures res.Err? ==> res.pos<=|s|
  ensures NoSpecialFrom(s,i) ==> res==Ok(PR(SChr(s[i],i,i+1),i+1))
  decreases |s|-i,1
 {
  var p :- ParseAtom(s,i);var x:=p.t;var j:=p.j;
  while j<|s| && (s[j]=='*' || s[j]=='+' || s[j]=='?' || s[j]=='{')
   invariant i<j<=|s| && WF(x,|s|) && x.lo==i && x.hi==j
   invariant NoSpecialFrom(s,i) ==> x==SChr(s[i],i,i+1) && j==i+1
   decreases |s|-j
  {
   var c:=s[j];
   if c=='{' {var q :- Counted(s,x,j);x:=q.0;j:=q.1;}
   else {
    x:=if c=='*' then SStar(x,i,j+1) else if c=='+' then SPlus(x,i,j+1) else SOpt(x,i,j+1);
    j:=j+1;
   }
  }
  res:=Ok(PR(x,j));
 }
 method ParseAtom(s:seq<char>,i:nat) returns (res:Res<PR>)
  requires i<|s|
  ensures res.Ok? ==> i<res.value.j<=|s| && WF(res.value.t,|s|) && res.value.t.lo==i && res.value.t.hi==res.value.j
  ensures res.Err? ==> res.pos<=|s|
  ensures NoSpecialFrom(s,i) ==> res==Ok(PR(SChr(s[i],i,i+1),i+1))
  decreases |s|-i,0
 {
  var c:=s[i];
  if c=='(' {
   var p :- ParseAlt(s,i+1);
   if p.j<|s| && s[p.j]==')' {res:=Ok(PR(SGroup(p.t,i,p.j+1),p.j+1));}
   else {res:=Err(p.j,"expected ')'");}
  } else if c=='[' {
   var cc :- ClassItems(s, i + 1, ClassEmpty());
   res := Ok(PR(SClass(cc.0, i, cc.1), cc.1));
  } else if c=='\\' {
   if i+1<|s| {res:=Ok(PR(SChr(s[i+1],i,i+2),i+2));}
   else {res:=Err(i+1,"dangling escape");}
  } else if Special(c) {res:=Err(i,"unexpected special character");}
  else {res:=Ok(PR(SChr(c,i,i+1),i+1));}
 }
 method Parse(s:seq<char>) returns (res:Res<Syn>)
  ensures res.Ok? ==> WF(res.value,|s|) && res.value.lo==0 && res.value.hi==|s|
  ensures NoSpecialFrom(s,0) ==> res.Ok? && Matches(Lower(res.value,|s|),s) && LoweringNodesR09(res.value,|s|)==(if |s|==0 then 1 else 2*|s|-1)
  ensures res.Err? ==> res.pos<=|s|
 {
  var p :- ParseAlt(s,0);
  if p.j==|s| {res:=Ok(p.t);} else {res:=Err(p.j,"unexpected ')'");}
 }
}
module R09_Budget {
 newtype CostU32 = x:int | 0<=x<0x100000000
 datatype BudgetDecision = FitsCost(cost:CostU32) | OverBudget {
  predicate IsFailure() {OverBudget?}
  function PropagateFailure():BudgetDecision requires OverBudget? {OverBudget}
  function Extract():CostU32 requires FitsCost? {cost}
 }
  // item: R09.H3d
 // pair: R09.H3v
method RepeatExpansionBudgetR09(base:CostU32,lo:CostU32,hi:CostU32,cap:CostU32) returns (res:BudgetDecision)
  requires lo<=hi<=9
  ensures res.FitsCost? ==> res.cost<=cap && (res.cost as int)==3+(base as int)*(hi as int)+(lo as int)+3*((hi as int)-(lo as int))
  ensures res.OverBudget? ==> 3+(base as int)*(hi as int)+(lo as int)+3*((hi as int)-(lo as int))>(cap as int)
 {
  // did: implement the frozen R09.H3d statement using the printed worked interfaces.

  var overhead:CostU32:=3+lo+3*(hi-lo);
  if overhead>cap {res:=OverBudget;return;}
  if hi>0 && base>(cap-overhead)/hi {res:=OverBudget;return;}
  var cost:CostU32:=base*hi+overhead;
  res:=FitsCost(cost);
 }
}
module R09_CheckedCost {
 import opened RG_A1_Re
 import opened RG_A3_Syntax
 import opened R09_Size
 import opened R09_Budget
 method CheckedAddCostR09(a:CostU32,b:CostU32,extra:CostU32,cap:CostU32) returns (res:BudgetDecision)
  ensures res.FitsCost? ==> res.cost<=cap && (res.cost as int)==(a as int)+(b as int)+(extra as int)
  ensures res.OverBudget? ==> (a as int)+(b as int)+(extra as int)>(cap as int)
 {
  if extra>cap {res:=OverBudget;return;}
  if a>cap-extra {res:=OverBudget;return;}
  if b>cap-extra-a {res:=OverBudget;return;}
  res:=FitsCost(a+b+extra);
 }
 method CheckedClassCostR09(cc: RG_A2_Deriv.CharClass, cap: CostU32) returns (res: BudgetDecision)
  requires ClassLowered(cc)
  ensures res.FitsCost? ==> res.cost <= cap && res.cost as int == ClassNodesR09(RG_A2_Deriv.ClassRanges(cc))
  ensures res.OverBudget? ==> ClassNodesR09(RG_A2_Deriv.ClassRanges(cc)) > cap as int
 {
  var rs := RG_A2_Deriv.ClassRanges(cc);
  if cap < 1 {
   res := OverBudget;
   return;
  }
  var cost: CostU32 := 1;
  var i: nat := 0;
  while i < |rs|
   invariant i <= |rs| && cost <= cap
   invariant (cost as int) + ClassNodesR09(rs[i..]) == ClassNodesR09(rs) + 1
   decreases |rs| - i
  {
   var lo := rs[i].lo as int;
   var hi := rs[i].hi as int;
   var range: CostU32 := (2 * (hi - lo) + 1) as CostU32;
   assert rs[i..][1..] == rs[i + 1..];
   assert ClassNodesR09(rs[i + 1..]) >= 1;
   cost :- CheckedAddCostR09(cost, range, 1, cap);
   i := i + 1;
  }
  res := FitsCost(cost);
 }
 lemma RepetitionCostGrowsR09(base:nat,n:nat,m:nat)
  requires n<=m && m>0
  ensures 3+n*(base+1)+(m-n)*(base+3)>=base
 {}
 lemma RepetitionCostFormulaR09(base:nat,n:nat,m:nat)
  requires n<=m
  ensures 3+n*(base+1)+(m-n)*(base+3)==3+base*m+n+3*(m-n)
 {}
 method CheckedLoweringCostR09(t:Syn,len:nat,cap:CostU32) returns (res:BudgetDecision)
  requires WF(t,len)
  ensures res.FitsCost? ==> res.cost<=cap && res.cost as int==LoweringNodesR09(t,len)
  ensures res.OverBudget? ==> LoweringNodesR09(t,len)>cap as int
  decreases t
 {
  match t
  case SEps(_,_) => res:=CheckedAddCostR09(0,0,1,cap);
  case SChr(_,_,_) => res:=CheckedAddCostR09(0,0,1,cap);
  case SClass(cc,_,_) => res:=CheckedClassCostR09(cc,cap);
  case SAlt(a,b,_,_) =>
   var left :- CheckedLoweringCostR09(a,len,cap);
   var right :- CheckedLoweringCostR09(b,len,cap);
   res:=CheckedAddCostR09(left,right,1,cap);
  case SCat(a,b,_,_) =>
   var left :- CheckedLoweringCostR09(a,len,cap);
   var right :- CheckedLoweringCostR09(b,len,cap);
   res:=CheckedAddCostR09(left,right,1,cap);
  case SStar(a,_,_) =>
   var child :- CheckedLoweringCostR09(a,len,cap);
   res:=CheckedAddCostR09(child,0,1,cap);
  case SPlus(a,_,_) =>
   var child :- CheckedLoweringCostR09(a,len,cap);
   res:=CheckedAddCostR09(child,child,2,cap);
  case SOpt(a,_,_) =>
   var child :- CheckedLoweringCostR09(a,len,cap);
   res:=CheckedAddCostR09(child,0,2,cap);
  case SGroup(a,_,_) => res:=CheckedLoweringCostR09(a,len,cap);
  case SRep(a,n,m,_,_) =>
   if m==0 {res:=CheckedAddCostR09(0,0,3,cap);}
   else {
    RepetitionCostGrowsR09(LoweringNodesR09(a,len),n,m);
    var child :- CheckedLoweringCostR09(a,len,cap);
    RepetitionCostFormulaR09(LoweringNodesR09(a,len),n,m);
    res:=RepeatExpansionBudgetR09(child,n as CostU32,m as CostU32,cap);
   }
 }
}
module R09_Lowering {
 import opened RG_A1_Re
 import opened RG_A3_Syntax
 method RangeLowerExecR09(lo: RG_A2_Deriv.Cp, hi: RG_A2_Deriv.Cp) returns (out: Re)
  requires lo <= hi && (hi as int) < ClassMax
  ensures out == RangeRe(lo, hi)
 {
  var low := lo as int;
  var n := hi as int;
  out := Chr(hi as int as char);
  while n > low
   invariant 0 <= low <= n <= hi as int < ClassMax
   invariant low == lo as int
   invariant out == RangeRe(n as RG_A2_Deriv.Cp, hi)
   decreases n - low
  {
   n := n - 1;
   out := Alt(Chr(n as char), out);
  }
 }
 method ClassLowerExecR09(cc: RG_A2_Deriv.CharClass) returns (out: Re)
  requires ClassLowered(cc)
  ensures out == ClassToRe(cc)
 {
  var rs := RG_A2_Deriv.ClassRanges(cc);
  var i: nat := |rs|;
  out := Empty;
  while i > 0
   invariant i <= |rs|
   invariant out == RangesToRe(rs[i..])
   decreases i
  {
   i := i - 1;
   var first := RangeLowerExecR09(rs[i].lo, rs[i].hi);
   assert rs[i..][1..] == rs[i + 1..];
   out := Alt(first, out);
  }
 }
 method CopiesLowerExecR09(r:Re,k:nat) returns (out:Re)
  ensures out==Copies(r,k)
 {
  var i:nat:=0;out:=Eps;
  while i<k
   invariant i<=k && out==Copies(r,i)
   decreases k-i
  {out:=Cat(r,out);i:=i+1;}
 }
 method OptionalLowerExecR09(r:Re,k:nat) returns (out:Re)
  ensures out==CopiesUpTo(r,k)
 {
  var i:nat:=0;out:=Eps;
  while i<k
   invariant i<=k && out==CopiesUpTo(r,i)
   decreases k-i
  {out:=Alt(Eps,Cat(r,out));i:=i+1;}
 }
 method LoweringExecR09(t:Syn,len:nat) returns (out:Re)
  requires WF(t,len)
  ensures out==Lower(t,len)
  decreases t
 {
  match t
  case SEps(_,_) => out:=Eps;
  case SChr(c,_,_) => out:=Chr(c);
  case SClass(cc,_,_) => out:=ClassLowerExecR09(cc);
  case SAlt(a,b,_,_) =>
   var left:=LoweringExecR09(a,len);var right:=LoweringExecR09(b,len);out:=Alt(left,right);
  case SCat(a,b,_,_) =>
   var left:=LoweringExecR09(a,len);var right:=LoweringExecR09(b,len);out:=Cat(left,right);
  case SStar(a,_,_) => var child:=LoweringExecR09(a,len);out:=Star(child);
  case SPlus(a,_,_) => var child:=LoweringExecR09(a,len);out:=Cat(child,Star(child));
  case SOpt(a,_,_) => var child:=LoweringExecR09(a,len);out:=Alt(Eps,child);
  case SGroup(a,_,_) => out:=LoweringExecR09(a,len);
  case SRep(a,n,m,_,_) =>
   if m==0 {out:=Cat(Eps,Eps);}
   else {
    var child:=LoweringExecR09(a,len);
    var fixed:=CopiesLowerExecR09(child,n);var optional:=OptionalLowerExecR09(child,m-n);
    out:=Cat(fixed,optional);
   }
 }
}
module R09_Frontend {
 import opened RG_A1_Re
 import opened RG_A3_Syntax
 import opened R09_Size
 import opened R09_Budget
 import opened R09_CheckedCost
 import P = R09_Parser
 import L = R09_Lowering
 // item: R09.W2d
 method CheckedLoweringR09(tree:Syn,len:nat,cap:CostU32) returns (res:Res<Re>)
  requires WF(tree,len)
  ensures res.Ok? ==> res.value==Lower(tree,len) && NodeCount(res.value)<=cap as int
  ensures res.Err? ==> res.pos==0 && LoweringNodesR09(tree,len)>cap as int
 {
  var cost:=CheckedLoweringCostR09(tree,len,cap);
  if cost.OverBudget? {res:=Err(0,"expansion budget");return;}
  var lowered:=L.LoweringExecR09(tree,len);
  LoweringNodesCorrectR09(tree,len);
  res:=Ok(lowered);
 }
 method {:isolate_assertions} FrontendR09(s:seq<char>,cap:CostU32) returns (res:Res<(Syn,Re)>)
  ensures res.Ok? ==> (WF(res.value.0,|s|) && res.value.0.lo==0 && res.value.0.hi==|s|
   && res.value.1==Lower(res.value.0,|s|) && NodeCount(res.value.1)<=cap as int)
  ensures res.Err? ==> res.pos<=|s|
  ensures NoSpecialFrom(s,0) && (if |s|==0 then 1 else 2*|s|-1)<=cap as int ==>
   res.Ok? && Matches(res.value.1,s)
 {
  var tree :- P.Parse(s);
  var lowered :- CheckedLoweringR09(tree,|s|,cap);
  res:=Ok((tree,lowered));
 }
}
module R09_Repetition {
 import opened RG_A1_Re
 import opened RG_A1b_Facts
 import opened RG_A3_Syntax
  // item: R09.W4d
 lemma CopiesSplit(r: Re, a: nat, b: nat, s: seq<char>)
    ensures Matches(Copies(r, a + b), s) <==> Matches(Cat(Copies(r, a), Copies(r, b)), s)
    decreases a
  {
    if a == 0 {
      CatEpsLeft(Copies(r, b), s);
    } else {
      assert Copies(r, a + b) == Cat(r, Copies(r, a - 1 + b));
      assert Copies(r, a) == Cat(r, Copies(r, a - 1));
      CatAssoc(r, Copies(r, a - 1), Copies(r, b), s);
      var x, y := Copies(r, a - 1 + b), Cat(Copies(r, a - 1), Copies(r, b));
      forall t ensures Matches(x, t) <==> Matches(y, t) {
        CopiesSplit(r, a - 1, b, t);
      }
      CatCongRight(r, x, y, s);
    }
  }

  // Replacing the right operand by a language-equal one (a helper; A4 gives the same fact
  // from R10 on, and its empty body verifies under every induction setting).
  lemma CatCongRight(a: Re, b1: Re, b2: Re, s: seq<char>)
    requires forall t :: Matches(b1, t) <==> Matches(b2, t)
    ensures Matches(Cat(a, b1), s) <==> Matches(Cat(a, b2), s)
  {
    if Matches(Cat(a, b1), s) {
      var i :| 0 <= i <= |s| && Matches(a, s[..i]) && Matches(b1, s[i..]);
      assert Matches(b2, s[i..]);
    }
    if Matches(Cat(a, b2), s) {
      var i :| 0 <= i <= |s| && Matches(a, s[..i]) && Matches(b2, s[i..]);
      assert Matches(b1, s[i..]);
    }
  }

  lemma CopiesUpToCorrect(r: Re, j: nat, s: seq<char>)
    ensures Matches(CopiesUpTo(r, j), s) <==> exists k | 0 <= k <= j :: Matches(Copies(r, k), s)
    decreases j
  {
    if j > 0 {
      var u := CopiesUpTo(r, j - 1);
      assert CopiesUpTo(r, j) == Alt(Eps, Cat(r, u));
      if Matches(CopiesUpTo(r, j), s) {
        if s != [] {
          assert !Matches(Eps, s);
          assert Matches(Cat(r, u), s);
          var i :| 0 <= i <= |s| && Matches(r, s[..i]) && Matches(u, s[i..]);
          CopiesUpToCorrect(r, j - 1, s[i..]);
          var k :| 0 <= k <= j - 1 && Matches(Copies(r, k), s[i..]);
          assert Copies(r, k + 1) == Cat(r, Copies(r, k));
          assert Matches(Copies(r, k + 1), s);
        } else {
          assert Matches(Copies(r, 0), s);
        }
      }
      if exists k | 0 <= k <= j :: Matches(Copies(r, k), s) {
        var k :| 0 <= k <= j && Matches(Copies(r, k), s);
        if k > 0 {
          assert Copies(r, k) == Cat(r, Copies(r, k - 1));
          var i :| 0 <= i <= |s| && Matches(r, s[..i]) && Matches(Copies(r, k - 1), s[i..]);
          CopiesUpToCorrect(r, j - 1, s[i..]);
          assert exists k' | 0 <= k' <= j - 1 :: Matches(Copies(r, k'), s[i..]);
          assert Matches(Cat(r, u), s);
        } else {
          assert Copies(r, 0) == Eps;
        }
        assert Matches(CopiesUpTo(r, j), s);
        assert exists k | 0 <= k <= j :: Matches(Copies(r, k), s);
      }
    } else {
      assert Copies(r, 0) == Eps;
      if exists k | 0 <= k <= j :: Matches(Copies(r, k), s) {
        var k :| 0 <= k <= j && Matches(Copies(r, k), s);
        assert k == 0;
        assert exists k | 0 <= k <= j :: Matches(Copies(r, k), s);
      }
    }
  }

   // item: R09.H4d
 // pair: R09.H4v
lemma {:induction false} RepRangeCorrect(r: Re, n: nat, m: nat, s: seq<char>)
    requires n <= m
    ensures Matches(RepRange(r, n, m), s) <==> exists k | n <= k <= m :: Matches(Copies(r, k), s)
  {
  // did: implement the frozen R09.H4d statement using the printed worked interfaces.

    if Matches(RepRange(r, n, m), s) {
      var i :| 0 <= i <= |s| && Matches(Copies(r, n), s[..i]) && Matches(CopiesUpTo(r, m - n), s[i..]);
      CopiesUpToCorrect(r, m - n, s[i..]);
      var k :| 0 <= k <= m - n && Matches(Copies(r, k), s[i..]);
      CopiesSplit(r, n, k, s);
      assert Matches(Copies(r, n + k), s);
    }
    if exists k | n <= k <= m :: Matches(Copies(r, k), s) {
      var k :| n <= k <= m && Matches(Copies(r, k), s);
      CopiesSplit(r, n, k - n, s);
      var i :| 0 <= i <= |s| && Matches(Copies(r, n), s[..i]) && Matches(Copies(r, k - n), s[i..]);
      CopiesUpToCorrect(r, m - n, s[i..]);
      assert Matches(CopiesUpTo(r, m - n), s[i..]);
    }
  }

}
module R09_Cursor {
 import P = R09_Parser
 import opened RG_A3_Syntax
 class EffectCursorR09 {
  var text:seq<char>
  var position:nat
  constructor(input:seq<char>,start:nat)
   requires start<=|input|
   ensures text==input && position==start
  {text:=input;position:=start;}
 }
 // item: R09.W1d
 method ReadBoundR09(c:char,pos:nat,len:nat) returns (res:Res<nat>)
  requires pos<=len
  ensures res.Ok? ==> BoundChar(c) && res.value==BoundVal(c)
  ensures res.Err? ==> !BoundChar(c) && res.pos==pos
 {
  if !BoundChar(c) {res:=Err(pos,"expected a bound '0'..'9'");}
  else {res:=Ok(BoundVal(c));}
 }
  // item: R09.T1d
 // pair: R09.T1v
 // uses: error-propagation, old
method ReadBoundCursorR09(cur:EffectCursorR09) returns (res:Res<nat>)
  requires cur.position<|cur.text|
  modifies cur
  ensures cur.text==old(cur.text)
  ensures cur.position==old(cur.position)+1
  ensures res.Ok? ==> BoundChar(cur.text[old(cur.position)]) && res.value==BoundVal(cur.text[old(cur.position)])
  ensures res.Err? ==> !BoundChar(cur.text[old(cur.position)]) && res.pos==old(cur.position)
 {
  // did: implement the frozen R09.T1d statement using the printed worked interfaces.

  var start:=cur.position;
  cur.position:=start+1;
  var n :- ReadBoundR09(cur.text[start],start,|cur.text|);
  res:=Ok(n);
 }
  // item: R09.H5d
 // pair: R09.H5v
 // uses: error-propagation, old
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
  // did: implement the frozen R09.H5d statement using the printed worked interfaces.

  var start:=cur.position;
  var pair :- P.Counted(cur.text,a,start);
  cur.position:=pair.1;
  res:=Ok(pair.0);
 }
}

// item: R09.P3dv verdict
// Predict product-x/product-y under the fixed mathematical product-fit model.
// CHECK P3dv
// item: R09.P5dv verdict
// Predict error-x/error-y under exact input/error-position preservation.
// CHECK P5dv

// item: R09.C3d recognise:dynamic-frames
// modifies cur grants field updates; it does not erase the explicit old-word promise.
// item: R09.C4dv diverge:error-propagation
// Dafny Res supplies IsFailure/PropagateFailure/Extract; Rust Result and ?
// preserve the specified error through the native result conversion.
// item: R09.C5dv diverge:machine-int
// Dafny's bounded newtype and Rust u32 need guards before bounded products.
// Scalar indices are not UTF8 byte offsets; keep exact positioned outputs.
