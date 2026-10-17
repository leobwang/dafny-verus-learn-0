// Reference Solution.
/*! R11 relative split observation; provided-only std unit. */
module R11_PredictSplit {
 import opened RG_A4_Norm
 method AbsoluteMiddleR11(start:nat,d:Derivation) returns(mid:nat)
  requires d.DCat?
  ensures mid==start+d.k
 {mid:=start+d.k;}
 // item: R11.P1d value
 // Answer form: numeral.
 @Test method RelativeMiddleR11() {
  var certificate:=DCat(2,DCat(1,DChr,DChr),DChr);
  var middle:=AbsoluteMiddleR11(4,certificate);
  expect middle == 6;
 }
}
