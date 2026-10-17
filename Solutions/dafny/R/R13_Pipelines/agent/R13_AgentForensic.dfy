// Reference Solution.
module R13_ForensicDelivery {
 // specfreeze: frozen-imports
 method DeliveredScoreR13(a:nat,b:nat) returns(score:nat)
  requires a<=4294967295 && b<=4294967295
  ensures score==2*a+3*b && score<=21474836475
 {score:=SupportScoreR13(a,b);}
 // item: R13.A1d
 method SupportScoreR13(a:nat,b:nat) returns(score:nat)
  requires a<=4294967295 && b<=4294967295
  ensures score==2*a+3*b && score<=21474836475
 {// did: discharge the helper contract over the full original bounded input domain.
 score:=2*a+3*b;}
}
