/*! R08 matcher interface (PROVIDED, frozen statement; PLAN F6).
This is a specification parameter, not an assumed implementation.
Concrete engines must supply their fixed model and prove MatchWord.
*/
abstract module RG_A2_MatcherSpec {
 type Pattern
 ghost predicate WordLanguage(p: Pattern,word: seq<char>)
 method MatchWord(p: Pattern,word: seq<char>) returns (b:bool)
  ensures b == WordLanguage(p,word)
}
