/*! R08 — Abstraction (Exercises).
Standalone R: frozen A1/A1b/A2, including the provided matcher interface.
Four holes per language: implement two fixed models, then reveal two opaque
models. The types, semantic bindings, contracts and opaque bodies stay fixed.
Commit five predictions and record first tries before enabling their guards.
Done: zero-hole full gates, clean audits, original snapshot and strict report,
refinement lab, written card, seventh bench card, semantic debugger and viva.
Live actor validation remains recorded debt, never an inferred outcome.
*/
// item: R08.P3dv verdict
// Compare full-word and prefix-word model bindings in the two complete specimens.
// D:<x>,<y> V:<x>,<y>; retain the exact provided model, not a preferred intent.
// SLOT: CHECK P3dv
// item: R08.P5dv verdict
// Compare the two printed complete one-character models. D:<v> V:<v>.
// SLOT: CHECK P5dv
module R08_Literal refines RG_A2_MatcherSpec {
 type Pattern = char
 ghost predicate WordLanguage(p:Pattern,word:seq<char>) { word == [p] }
 // item: R08.W1d
 method MatchWord(p:Pattern,word:seq<char>) returns (b:bool)
  ensures b == WordLanguage(p,word)
 { b := word == [p]; }
}
module R08_LiteralClient {
 import L = R08_Literal
 // item: R08.W2d
 method ReadModel(p:char,word:seq<char>) returns (b:bool)
  ensures b == (word == [p])
 { b := L.MatchWord(p,word); }
}
module R08_Derivative refines RG_A2_MatcherSpec {
 import A1 = RG_A1_Re
 import A2 = RG_A2_Deriv
 type Pattern = A1.Re
 ghost predicate WordLanguage(p:Pattern,word:seq<char>) { A1.Matches(p,word) }
 // item: R08.H1d
 // pair: R08.H1v
 // uses: refines
 method MatchWord(p:Pattern,word:seq<char>) returns (b:bool)
  ensures b == WordLanguage(p,word)
 { assume false; }
}
module R08_Class refines RG_A2_MatcherSpec {
 import A2 = RG_A2_Deriv
 type Pattern = A2.CharClass
 ghost predicate WordLanguage(p:Pattern,word:seq<char>) { |word| == 1 && A2.InClass(p,word[0]) }
 // item: R08.H2d
 // pair: R08.H2v
 // uses: refines
 method MatchWord(p:Pattern,word:seq<char>) returns (b:bool)
  ensures b == WordLanguage(p,word)
 { assume false; }
}
module R08_Opacity {
 import A1 = RG_A1_Re
 import A2 = RG_A2_Deriv
 opaque ghost predicate HiddenWord(r:A1.Re,word:seq<char>) { A1.Matches(r,word) }
 opaque ghost predicate HiddenResidual(r:A1.Re,c:char,word:seq<char>) { A1.Matches(A2.Deriv(r,c),word) }
 // item: R08.H3d
 // pair: R08.H3v
 // uses: reveal
 lemma {:induction false} RevealWord(r:A1.Re,word:seq<char>)
  ensures HiddenWord(r,word) <==> A1.Matches(r,word)

 // item: R08.H4d
 // pair: R08.H4v
 // uses: reveal
 lemma {:induction false} RevealResidual(r:A1.Re,c:char,word:seq<char>)
  ensures HiddenResidual(r,c,word) <==> A1.Matches(r,[c]+word)

}

// item: R08.C3d recognise:abstract-module
// The abstract matcher is provided in a given-role, SHA-pinned statement file.
// item: R08.C4dv diverge:refines
// Dafny refinement can weaken requires and strengthen ensures. Verus trait
// implementations must discharge their trait contract under its stated domain.
// These are facts to explain, not another track's reserved legality prediction.
// item: R08.C5dv diverge:refines
// A green different model does not repair the original frozen model.
