/* CONTRACT — R08 semantic debugger, R-v0
goal: repair the implementation so it honours the original whole-word model
allowed-files:
  - verus/r/r08_abstraction/src/agent.rs
acceptance:
  - retain the original snapshot and native verify-stage diagnostic before the first edit
  - preserve the provided interface, concrete type, semantic model, all preconditions and postconditions; body edits only
  - after every edit run scripts/vcheck verus/r/r08_abstraction/src/agent.rs and retain the actual stage, holes and diagnostics
  - scripts/vcheck --gate verus/r/r08_abstraction/src/agent.rs exits0 with zero counted holes over the full file
  - scripts/vaudit verus/r/r08_abstraction/src/agent.rs has no findings and scripts/specfreeze --against <snapshot> verus/r/r08_abstraction/src/agent.rs preserves the original statement and model
  - explain why a verifier success against a changed model would not repair this contract; retain costs and the failed attempt
*/
/*! R08 semantic debugger (Exercises). Prefix copying is complete, not a hole. */
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a2::*;
use rg_re_a2::word_matcher::WordMatcher;
verus! {
// GIVEN adapter: its complete proof is not a learner repair target.
fn shortened_word_copy_r08(word:&Vec<char>) -> (prefix:Vec<char>)
 ensures prefix@ == if word.len() == 0 { word@ } else { word@.take(word.len()-1) },
{
 let target = if word.len() == 0 { 0 } else { word.len()-1 };
 let mut prefix:Vec<char> = Vec::new();
 let mut i:usize = 0;
 while i < target
  invariant i <= target, target <= word.len(),
   target == if word.len() == 0 { 0 } else { word.len()-1 },
   prefix@ == word@.take(i as int),
  decreases target-i,
 { prefix.push(word[i]); i=i+1; }
 prefix
}
pub struct InfraEngine { pub pattern: Re }
impl WordMatcher for InfraEngine {
 open spec fn word_language(&self,word:Seq<char>) -> bool { matches(self.pattern,word) }
 // item: R08.A1v
 fn match_word(&self,word:&Vec<char>) -> (b:bool)
  ensures b == self.word_language(word@),
 {
  let prefix = shortened_word_copy_r08(word);
  deriv_match(&self.pattern,&prefix)
 }
}
}
