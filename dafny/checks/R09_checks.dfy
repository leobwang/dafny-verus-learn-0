/*! R09 single-bound error position prediction. */
module R09_PredictBound {
 datatype SingleBoundR09 = BoundValueR09(value:nat) | BoundErrorR09(position:nat)
 method ReadSingleR09(c:char,at:nat) returns (out:SingleBoundR09)
  ensures '0'<=c<='9' ==> out==BoundValueR09((c as int)-('0' as int))
  ensures !('0'<=c<='9') ==> out==BoundErrorR09(at)
 {out:=if '0'<=c<='9' then BoundValueR09((c as int)-('0' as int)) else BoundErrorR09(at);}
 // item: R09.P1d value
 // Answer form: numeral.
 @Test method BoundPositionValueR09() {
  var out:=ReadSingleR09('x',2);
  var value:=if out.BoundErrorR09? then out.position else out.value;
  // SLOT: expect value == ???;
 }
}
