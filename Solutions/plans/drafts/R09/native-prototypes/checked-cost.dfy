module R09_CheckedCostPrototype {
 import opened RG_A1_Re
 import opened RG_A3_Syntax
 import opened R09_SizePrototype
 import opened R09_BudgetPrototype
 method CheckedAddCostR09(a:CostU32,b:CostU32,extra:CostU32,cap:CostU32) returns (res:BudgetDecision)
  ensures res.FitsCost? ==> res.cost<=cap && (res.cost as int)==(a as int)+(b as int)+(extra as int)
  ensures res.OverBudget? ==> (a as int)+(b as int)+(extra as int)>(cap as int)
 {
  if extra>cap {res:=OverBudget;return;}
  if a>cap-extra {res:=OverBudget;return;}
  if b>cap-extra-a {res:=OverBudget;return;}
  res:=FitsCost(a+b+extra);
 }
 method CheckedClassCostR09(cc:RG_A2_Deriv.CharClass,cap:CostU32) returns (res:BudgetDecision)
  requires ClassLowered(cc)
  ensures res.FitsCost? ==> res.cost<=cap && res.cost as int==ClassNodesR09(cc)
  ensures res.OverBudget? ==> ClassNodesR09(cc)>cap as int
 {
  if cap<1 {res:=OverBudget;return;}
  var cost:CostU32:=1;var i:nat:=0;
  while i<|cc|
   invariant i<=|cc| && cost<=cap
   invariant (cost as int)+ClassNodesR09(cc[i..])==ClassNodesR09(cc)+1
   decreases |cc|-i
  {
   var lo:=cc[i].lo as int;var hi:=cc[i].hi as int;
   var range:CostU32:=(2*(hi-lo)+1) as CostU32;
   assert cc[i..][1..]==cc[i+1..];
   assert ClassNodesR09(cc[i+1..])>=1;
   cost :- CheckedAddCostR09(cost,range,1,cap);
   i:=i+1;
  }
  res:=FitsCost(cost);
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
