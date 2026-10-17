/*! R08 literal interface value prediction. */
module R08_PredictLiteral refines RG_A2_MatcherSpec {
 type Pattern = char
 ghost predicate WordLanguage(p:Pattern,word:seq<char>) { word == [p] }
 method MatchWord(p:Pattern,word:seq<char>) returns (b:bool)
  ensures b == WordLanguage(p,word)
 { b := word == [p]; }
}
module R08_Checks {
 import E = R08_PredictLiteral
 // item: R08.P1d value
 // Answer form: bool literal.
 @Test method LiteralInterfaceValue() {
  var b := E.MatchWord('k',"kk");
  // SLOT: expect b == ???;
 }
}
