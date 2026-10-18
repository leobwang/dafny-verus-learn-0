/*!
# RG_A2 — the step-matcher interface (PROVIDED, frozen statement; PLAN F6)

An abstract matcher that reads a word one character at a time. An engine supplies its
pattern and state types, its language `Lang` (the engine's frozen semantic binding), what a
state still accepts (`Res`), and three executable functions. It then owes three laws.
`MatchWord`'s loop is verified once, here, from the three laws alone: no engine re-proves it.

This file is a specification parameter, not an implementation: it holds no engine, and an
engine that refines it inherits every contract below unchanged. R08 builds the engines;
R11's certifying matcher and R16's machine can refine the same interface.
*/
abstract module RG_A2_StepMatcher {
  type Pattern
  type Config

  // The engine's language: the meaning every client of MatchWord relies on.
  ghost predicate Lang(p: Pattern, w: seq<char>)

  // The words a state still accepts.
  ghost predicate Res(st: Config, w: seq<char>)

  function Start(p: Pattern): Config
  function Feed(st: Config, c: char): Config
  predicate Final(st: Config)

  // The three laws: the start state accepts the pattern's language ...
  lemma StartLaw(p: Pattern, w: seq<char>)
    ensures Res(Start(p), w) <==> Lang(p, w)

  // ... one step consumes exactly one character ...
  lemma FeedLaw(st: Config, c: char, w: seq<char>)
    ensures Res(Feed(st, c), w) <==> Res(st, [c] + w)

  // ... and a final state is one that accepts the empty word.
  lemma FinalLaw(st: Config)
    ensures Final(st) <==> Res(st, [])

  // The run loop: its invariant is assembled from the three laws.
  method MatchWord(p: Pattern, w: seq<char>) returns (b: bool)
    ensures b == Lang(p, w)
  {
    var st := Start(p);
    var i := 0;
    StartLaw(p, w);
    assert w[0..] == w;
    while i < |w|
      invariant 0 <= i <= |w|
      invariant Res(st, w[i..]) <==> Lang(p, w)
    {
      FeedLaw(st, w[i], w[i + 1..]);
      assert [w[i]] + w[i + 1..] == w[i..];
      st := Feed(st, w[i]);
      i := i + 1;
    }
    FinalLaw(st);
    assert w[i..] == [];
    b := Final(st);
  }
}
