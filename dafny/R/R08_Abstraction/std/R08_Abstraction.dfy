/*!
# R08 — Abstraction (Exercises)

Imports: the given regex spine A1 (`RG_A1_Re`), A1b (`RG_A1b_Facts`) and A2
(`RG_A2_Deriv`), and A2's step-matcher interface (`RG_A2_StepMatcher`, in
`dafny/given/R/RG_A2_MatcherStatement.dfy`); nothing else: no earlier exercise
file. The layers are frozen and complete; read them, never edit them.

How to work this file:
1. Predictions first: fill every slot of the prediction block below (the
   verdict answers go in slots/R08.slots), of dafny/checks/R08_checks.dfy and
   of specimens/R08/P*.specimen, then record the first tries with
   `scripts/firsttry.sh R08 --check`, before you run anything they are about.
2. Read the worked derivative engine (W1), then replace each hole, H1 to H4,
   in order. Every hole is a lemma that one of an engine's interface laws
   rests on.
3. Done = `scripts/vcheck --gate dafny/R/R08_Abstraction/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/R/R08_Abstraction/std`
   reports no finding, AND `scripts/firsttry.sh R08 --report --strict` exits 0.
4. Stuck for 20 minutes? /tutor R08.

This file ships with exactly 4 holes: H1–H4, each counted by `scripts/vcheck`.
R08 as a whole ships 8 holes (4 here, 4 in the Verus file
verus/r/r08_abstraction/src/lib.rs) and 5 predictions.

Item kinds: P prediction (a slot) · W worked example (complete; read it) ·
H hole (replace the body) · C card (a WRITE card is a short exercise in a
specimen; a recognise or divergence card is read).
*/

// =============================================================================
// Predictions (commit before you run anything they are about)
// =============================================================================

// item: R08.P3dv verdict
// specimens/R08/P3d.dfy.specimen and P3v.rs.specimen prove one interface law
// by calling the same law on a shorter list, inside the refinement (Dafny) and
// inside the trait implementation (Verus). Does each verify? Answer form in
// slots/R08.slots: `D:<verified|failed> V:<verified|failed>`.
// SLOT: CHECK P3dv

// item: R08.P5dv verdict
// specimens/R08/P5x-d.dfy.specimen, P5y-d.dfy.specimen, P5x-v.rs.specimen and
// P5y-v.rs.specimen hold one complete engine whose language is
// `Matches(Backwards(p), w)`. Client [x] promises `Matches(p, w)`, client [y]
// promises `Matches(Backwards(p), w)`; each only returns the engine's MatchWord.
// Which verify? Answer form: `D:<x>,<y> V:<x>,<y>`, each verified or failed.
// SLOT: CHECK P5dv

// =============================================================================
// W1 (worked): the derivative engine
// =============================================================================

// item: R08.W1d
// The derivative engine refines the interface with Pattern = Config = Re. Each
// law is one call to a layer lemma; MatchWord is inherited, already verified.
module R08_DerivEngine refines RG_A2_StepMatcher {
  import opened RG_A1_Re
  import B = RG_A1b_Facts
  import A2 = RG_A2_Deriv

  type Pattern = Re
  type Config = Re

  ghost predicate Lang(p: Pattern, w: seq<char>)
  {
    Matches(p, w)
  }

  ghost predicate Res(st: Config, w: seq<char>)
  {
    Matches(st, w)
  }

  function Start(p: Pattern): Config
  {
    p
  }

  function Feed(st: Config, c: char): Config
  {
    A2.Deriv(st, c)
  }

  predicate Final(st: Config)
  {
    Nullable(st)
  }

  lemma StartLaw(p: Pattern, w: seq<char>)
  {
  }

  lemma FeedLaw(st: Config, c: char, w: seq<char>)
  {
    A2.DerivCorrect(st, c, w);
  }

  lemma FinalLaw(st: Config)
  {
    B.NullableCorrect(st);
  }
}

// A client of the interface: it knows only MatchWord's contract and the engine's Lang.
module R08_DerivClient {
  import opened RG_A1_Re
  import E = R08_DerivEngine

  method MatchDeriv(r: Re, w: seq<char>) returns (b: bool)
    ensures b == Matches(r, w)
  {
    b := E.MatchWord(r, w);
  }
}

// =============================================================================
// The range-star engine: a second refinement, over A2's class API
// =============================================================================

// A pattern is a list of character ranges `(lo, hi)`; a word matches when each of
// its characters lies in one of the ranges (the regex `[a-cx-z]*` for the list
// `[('a', 'c'), ('x', 'z')]`). The language speaks of ranges; the engine builds
// one A2 class at the start and only tests membership afterwards.
module R08_RangeStarEngine refines RG_A2_StepMatcher {
  import A2 = RG_A2_Deriv

  datatype StarState = StarState(alive: bool, cls: A2.CharClass)

  type Pattern = seq<(char, char)>
  type Config = StarState

  // Given: c lies in one of the ranges.
  ghost predicate InSomeRange(rs: seq<(char, char)>, c: char)
  {
    exists j | 0 <= j < |rs| :: rs[j].0 <= c <= rs[j].1
  }

  // Given: the class of all the ranges, built with A2's class API.
  function RangesClass(rs: seq<(char, char)>): (cls: A2.CharClass)
    ensures A2.ClassValid(cls)
  {
    if rs == [] then A2.ClassEmpty() else A2.ClassUnion(A2.ClassRange(rs[0].0, rs[0].1), RangesClass(rs[1..]))
  }

  ghost predicate Lang(p: Pattern, w: seq<char>)
  {
    forall i | 0 <= i < |w| :: InSomeRange(p, w[i])
  }

  ghost predicate Res(st: Config, w: seq<char>)
  {
    st.alive && forall i | 0 <= i < |w| :: A2.InClass(st.cls, w[i])
  }

  function Start(p: Pattern): Config
  {
    StarState(true, RangesClass(p))
  }

  function Feed(st: Config, c: char): Config
  {
    if st.alive && A2.ClassMember(st.cls, c) then st else StarState(false, st.cls)
  }

  predicate Final(st: Config)
  {
    st.alive
  }

  // The start law rests on a fact about the class RangesClass builds; the
  // engine proves it in a lemma of its own (H1), and the law calls it.
  lemma StartLaw(p: Pattern, w: seq<char>)
  {
    forall c {
      RangesClassLaw(p, c);
    }
  }

  lemma FeedLaw(st: Config, c: char, w: seq<char>)
  {
    var cw := [c] + w;
    assert cw[0] == c;
    assert forall i | 0 <= i < |w| :: cw[i + 1] == w[i];
  }

  lemma FinalLaw(st: Config)
  {
  }

  // item: R08.H1d
  // uses: refines
  // pair: R08.H1v
  /** **H1.** The class the engine builds holds exactly the characters of the
      pattern's ranges. RangesClass unions one ClassRange per range: what do
      ClassUnion's and ClassRange's postconditions say about membership, what
      does the recursive call give you for `rs[1..]`, and which index of `rs`
      is range `j` of `rs[1..]`? */
  lemma {:induction false} RangesClassLaw(rs: seq<(char, char)>, c: char)
    ensures A2.InClass(RangesClass(rs), c) <==> InSomeRange(rs, c)
  // Hint(1): induction on `rs` (this lemma has `{:induction false}`): call
  //          RangesClassLaw on `rs[1..]`, then handle the witnesses yourself.
  // Hint(2): `var j :| …` picks a witness range; relate `rs[1..][j]` to
  //          `rs[j + 1]` in one direction and `rs[j]` to `rs[1..][j - 1]` in
  //          the other.

}

// =============================================================================
// The alternative-set engine: a state is a list of alternatives
// =============================================================================

// The state is the list of the pattern's top-level alternatives; a step takes
// the derivative of each and splits the results again. Res is the opaque
// AltRes: its existential stays out of every proof that does not reveal it.
module R08_AltSetEngine refines RG_A2_StepMatcher {
  import opened RG_A1_Re
  import B = RG_A1b_Facts
  import A2 = RG_A2_Deriv

  type Pattern = Re
  type Config = seq<Re>

  // Given: split the top-level Alt nodes, drop the literal Empty parts.
  function Parts(r: Re): seq<Re>
  {
    match r
    case Empty => []
    case Alt(a, b) => Parts(a) + Parts(b)
    case _ => [r]
  }

  // Given: some alternative of the list matches w.
  ghost predicate AnyMatches(st: seq<Re>, w: seq<char>)
  {
    exists i | 0 <= i < |st| :: Matches(st[i], w)
  }

  // Given: the derivative of every alternative, split again.
  function FeedAll(st: seq<Re>, c: char): seq<Re>
  {
    if st == [] then [] else Parts(A2.Deriv(st[0], c)) + FeedAll(st[1..], c)
  }

  // Given: some alternative of the list is nullable.
  predicate AnyNullable(st: seq<Re>)
  {
    st != [] && (Nullable(st[0]) || AnyNullable(st[1..]))
  }

  ghost predicate Lang(p: Pattern, w: seq<char>)
  {
    Matches(p, w)
  }

  // The engine's model, opaque: its existential stays out of every proof that
  // does not reveal it. (The opacity sits on a predicate of the engine's own:
  // Dafny does not make a refining declaration opaque.)
  opaque ghost predicate AltRes(st: seq<Re>, w: seq<char>)
  {
    AnyMatches(st, w)
  }

  ghost predicate Res(st: Config, w: seq<char>)
  {
    AltRes(st, w)
  }

  function Start(p: Pattern): Config
  {
    Parts(p)
  }

  function Feed(st: Config, c: char): Config
  {
    FeedAll(st, c)
  }

  predicate Final(st: Config)
  {
    AnyNullable(st)
  }

  lemma StartLaw(p: Pattern, w: seq<char>)
  {
    reveal AltRes();
    PartsLaw(p, w);
  }

  lemma FeedLaw(st: Config, c: char, w: seq<char>)
  {
    AltFeedLaw(st, c, w);
  }

  lemma FinalLaw(st: Config)
  {
    AltFinalLaw(st);
  }

  // item: R08.H2d
  // pair: R08.H2v
  /** **H2.** Splitting a pattern into its parts keeps its language:
      some part matches `w` exactly when the pattern does. In the `Alt`
      case the parts of `Alt(a, b)` are `Parts(a) + Parts(b)`: where in the
      concatenation is a part of `a` that matches, and where is a part of
      `b`? Going back, how do you tell from an index which half it is in? */
  lemma {:induction false} PartsLaw(r: Re, w: seq<char>)
    ensures AnyMatches(Parts(r), w) <==> Matches(r, w)
  // Hint(1): induction on `r` (this lemma has `{:induction false}`): call
  //          PartsLaw on `a` and `b`, then give the witnesses by hand.
  // Hint(2): `(pa + pb)[i] == pa[i]` for `i < |pa|`, and
  //          `(pa + pb)[|pa| + i] == pb[i]`; the non-Alt, non-Empty case
  //          has the one-element list `[r]`.


  // item: R08.H3d
  // uses: refines, reveal
  // pair: R08.H3v
  /** **H3.** The alternative-set engine's step law. `FeedAll(st, c)` is
      `Parts(Deriv(st[0], c))` followed by `FeedAll(st[1..], c)`; `Res` is
      the opaque `AltRes`. Which given lemmas say what a part of the derivative of
      `st[0]` matches, which call covers the rest of the list, and where
      must the witness index go in each direction? */
  lemma {:induction false} AltFeedLaw(st: seq<Re>, c: char, w: seq<char>)
    ensures AltRes(FeedAll(st, c), w) <==> AltRes(st, [c] + w)
    decreases |st|
  // Hint(1): reveal AltRes in this lemma, then induction on |st|; the
  //          recursive call on st[1..] is your induction hypothesis.
  // Hint(2): PartsLaw (H2) and A2.DerivCorrect on st[0]; then move one
  //          witness across `head + tail` and across st[0] / st[1..].


  // item: R08.H4d
  // uses: refines, reveal
  // pair: R08.H4v
  /** **H4.** The alternative-set engine's final law: the state is final
      exactly when some alternative accepts the empty word. `AltRes` is
      opaque for every lemma that does not reveal it. Where does the reveal belong,
      and which A1b fact turns `Nullable` into a match of `[]`? */
  lemma {:induction false} AltFinalLaw(st: seq<Re>)
    ensures AnyNullable(st) <==> AltRes(st, [])
    decreases |st|
  // Hint(1): reveal AltRes here, in this lemma only; induction on |st|.
  // Hint(2): RG_A1b_Facts.NullableCorrect on st[0]; index i + 1 of st is
  //          index i of st[1..].

}

// =============================================================================
// Cards (read; the WRITE cards are specimens)
// =============================================================================

// item: R08.C3d recognise:abstract-module
// RG_A2_StepMatcher is an abstract module in a given-role statement file: its
// types and functions have no bodies, its lemmas no proofs, and only MatchWord has a
// body. A refining module supplies the rest; it can neither change a contract
// nor re-prove MatchWord.

// item: R08.C4dv diverge:refines
// What a refinement may change. Dafny: a refining module gives bodies to the
// interface's bodiless declarations and may add declarations of its own; every
// inherited requires and ensures stays. Verus: a trait implementation keeps the
// trait's requires and ensures, and a caller through the trait sees only the
// trait's. In both, the obligations the interface states are each engine's,
// and the refinement lab lists them with the side that discharges each.

// item: R08.C5dv diverge:refines
// One model, two representations. Dafny's Config is its own model: a compiled
// seq or datatype is the value the laws talk about. Verus separates the
// executable Config (a Vec, a struct holding a Vec) from its spec Model, because
// a Vec cannot be built in spec mode, and states the laws over the Model:
// `model(st)` is the abstraction function of the refinement square.
