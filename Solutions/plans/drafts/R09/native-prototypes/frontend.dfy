module R09_FrontendPrototype {
 import opened RG_A1_Re
 import opened RG_A3_Syntax
 import opened R09_SizePrototype
 import opened R09_BudgetPrototype
 import opened R09_CheckedCostPrototype
 import P = R09_ParserPrototype
 import L = R09_LoweringPrototype
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
