/* CONTRACT — R08 semantic debugger, R-v0
goal: repair the implementation so it honours the original whole-word model
allowed-files:
  - dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy
acceptance:
  - retain the original snapshot and native verify-stage diagnostic before the first edit
  - preserve the provided interface, concrete type, semantic model, all preconditions and postconditions; body edits only
  - after every edit run scripts/vcheck dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy and retain the actual stage, holes and diagnostics
  - scripts/vcheck --gate dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy exits0 with zero counted holes over the full file
  - scripts/vaudit dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy has no findings and scripts/specfreeze --against <snapshot> dafny/R/R08_Abstraction/agent/R08_AgentInfra.dfy preserves the original statement and model
  - explain why a verifier success against a changed model would not repair this contract; retain costs and the failed attempt
*/
/*! R08 semantic debugger (Reference Solution). Fixed whole-word model; A2 only. */
module R08_AgentInfra refines RG_A2_MatcherSpec {
 import A1 = RG_A1_Re
 import A2 = RG_A2_Deriv
 type Pattern = A1.Re
 ghost predicate WordLanguage(p:Pattern,word:seq<char>) { A1.Matches(p,word) }
 // item: R08.A1d
 method MatchWord(p:Pattern,word:seq<char>) returns (b:bool)
  ensures b == WordLanguage(p,word)
 {
  var prefix := if |word| == 0 then word else word[..|word|-1];
  b := A2.DerivMatch(p,word);
 }
}
