//! R08 matcher interface (PROVIDED, frozen). No assumed implementation.
use vstd::prelude::*;
verus! {
pub trait WordMatcher {
 spec fn word_language(&self,word: Seq<char>) -> bool;
 fn match_word(&self,word: &Vec<char>) -> (b:bool)
  ensures b == self.word_language(word@);
}
}
