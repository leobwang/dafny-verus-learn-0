/*! R08 — Abstraction (Exercises).
Standalone R: frozen A1/A1b/A2, including the provided matcher interface.
Four holes per language: implement two fixed models, then reveal two opaque
models. The types, semantic bindings, contracts and opaque bodies stay fixed.
Commit five predictions and record first tries before enabling their guards.
Done: zero-hole full gates, clean audits, original snapshot and strict report,
refinement lab, written card, seventh bench card, semantic debugger and viva.
Live actor validation remains recorded debt, never an inferred outcome.
*/
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a2::*;
use rg_re_a2::char_class::CharClass;
use rg_re_a2::word_matcher::WordMatcher;
verus! {
// item: R08.W1v
pub struct LiteralEngine { pub character: char }
impl WordMatcher for LiteralEngine {
 open spec fn word_language(&self,word:Seq<char>) -> bool { word == seq![self.character] }
 fn match_word(&self,word:&Vec<char>) -> (b:bool)
  ensures b == self.word_language(word@),
 {
  let b = word.len() == 1 && word[0] == self.character;
  proof { if b { assert(word@ =~= seq![self.character]); } }
  b
 }
}
// item: R08.W2v
pub fn read_model<E:WordMatcher>(engine:&E,word:&Vec<char>) -> (b:bool)
 ensures b == engine.word_language(word@),
{ engine.match_word(word) }
pub struct DerivEngine { pub pattern: Re }
impl WordMatcher for DerivEngine {
 open spec fn word_language(&self,word:Seq<char>) -> bool { matches(self.pattern,word) }
 // item: R08.H1v
 // pair: R08.H1d
 // uses: trait-spec
 #[verifier::external_body]
 fn match_word(&self,word:&Vec<char>) -> (b:bool)
  ensures b == self.word_language(word@),
{ unimplemented!() }
}
pub struct ClassEngine { pub class: CharClass }
impl WordMatcher for ClassEngine {
 open spec fn word_language(&self,word:Seq<char>) -> bool { word.len() == 1 && self.class@.contains(word[0]) }
 // item: R08.H2v
 // pair: R08.H2d
 // uses: trait-spec
 #[verifier::external_body]
 fn match_word(&self,word:&Vec<char>) -> (b:bool)
  ensures b == self.word_language(word@),
{ unimplemented!() }
}
#[verifier::opaque]
pub open spec fn hidden_word(r:Re,word:Seq<char>) -> bool { matches(r,word) }
#[verifier::opaque]
pub open spec fn hidden_residual(r:Re,c:char,word:Seq<char>) -> bool { matches(deriv(r,c),word) }
// item: R08.H3v
// pair: R08.H3d
// uses: reveal
pub proof fn reveal_word(r:Re,word:Seq<char>)
 ensures hidden_word(r,word) == matches(r,word),
{ #[verifier::proof_note("R08.H3v")] assume(false); }
// item: R08.H4v
// pair: R08.H4d
// uses: reveal
pub proof fn reveal_residual(r:Re,c:char,word:Seq<char>)
 ensures hidden_residual(r,c,word) == matches(r,seq![c]+word),
{ #[verifier::proof_note("R08.H4v")] assume(false); }
}

// item: R08.C3v recognise:open-spec
// The implementation's spec method binds this receiver's mathematical model.
