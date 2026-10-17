module R09_BudgetPrototype {
 newtype CostU32 = x:int | 0<=x<0x100000000
 datatype BudgetDecision = FitsCost(cost:CostU32) | OverBudget {
  predicate IsFailure() {OverBudget?}
  function PropagateFailure():BudgetDecision requires OverBudget? {OverBudget}
  function Extract():CostU32 requires FitsCost? {cost}
 }
 method RepeatExpansionBudgetR09(base:CostU32,lo:CostU32,hi:CostU32,cap:CostU32) returns (res:BudgetDecision)
  requires lo<=hi<=9
  ensures res.FitsCost? ==> res.cost<=cap && (res.cost as int)==3+(base as int)*(hi as int)+(lo as int)+3*((hi as int)-(lo as int))
  ensures res.OverBudget? ==> 3+(base as int)*(hi as int)+(lo as int)+3*((hi as int)-(lo as int))>(cap as int)
 {
  var overhead:CostU32:=3+lo+3*(hi-lo);
  if overhead>cap {res:=OverBudget;return;}
  if hi>0 && base>(cap-overhead)/hi {res:=OverBudget;return;}
  var cost:CostU32:=base*hi+overhead;
  res:=FitsCost(cost);
 }
}
