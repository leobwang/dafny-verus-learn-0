/*!
# R10 — Invariants in types (exercises)

Standalone R track. Import only the frozen layers A1 to A4; no earlier learner
file is needed. The paired exercise is verus/r/r10_type_invariants/src/lib.rs.

Fill the five predictions in slots/R10.slots (switched on by the two CHECK
lines of the prediction block), specimens/R10/P2v.rs.specimen,
specimens/R10/P4v.rs.specimen and dafny/checks/R10_checks.dfy, and record the
first attempts with scripts/firsttry.sh R10 --check before running their
scenarios. Four typed holes ship in this language, eight across the pair.

File order: the prediction block, the worked examples (W1 the packet types, W2
the runtime check, W3 a language fact the shape does not give), the holes H1
to H4 with the given idempotence corollary after H3, then the given compiled
use-site test. Shape (Normal), exact normalization (Norm) and language
preservation (EquivalentReR10) are three different promises.

Done: the unit gates with zero tool-counted holes, vaudit is clean,
specfreeze --check R10 passes and firsttry's strict report is OK. Preserve the
given contracts and implementations. /tutor R10 is available after an attempt.
*/

// =============================================================================
// Prediction block: do not run the scenarios until these slots are recorded
// =============================================================================

// item: R10.P3dv verdict
/** option-x validates a raw regex at runtime and receives a rejection;
    precondition-x calls a routine whose precondition demands normal shape on
    the same raw regex. Predict both verdicts in each language.
    Answer form: D:<x>,<y> V:<x>,<y>, each ok, fail, timeout or err:<stage>. */
// SLOT: CHECK P3dv
// item: R10.P5dv verdict
/** shape-x returns a normal value under a shape-only promise; language-x
    returns the same value under the promise that it matches what Chr('q')
    matches. Predict both verdicts in each language. Same form as P3dv. */
// SLOT: CHECK P5dv

module R10_TypeInvariants {
  import opened RG_A1_Re
  import opened RG_A4_Norm

  // ===========================================================================
  // Worked examples
  // ===========================================================================

  // item: R10.W1d
  /** A packet: a normal regex (A4's subset type NormRe) and a ghost node
      count. The subset type TypedPacketR10 makes the count's meaning part of
      the type: every value of it, wherever it is built, satisfies the
      predicate. The ghost field is erased from the compiled program. */
  datatype CountPacketR10 = CountPacketR10(expr: NormRe, ghost count: nat)

  type TypedPacketR10 = p: CountPacketR10 | p.count == NodeCount(p.expr) witness CountPacketR10(Empty, 1)

  datatype PacketChoiceR10 = NoPacketR10 | HasPacketR10(packet: TypedPacketR10)

  // item: R10.W2d
  /** The runtime end of the enforcement spectrum: A4's Normal is a compiled
      predicate, so a caller can test a raw regex and branch. */
  function RuntimeShapeR10(r: Re): bool
  {
    Normal(r)
  }

  // item: R10.W3d
  /** A language fact the shape does not give: replacing the right operand of
      a Cat by a language-equal one keeps the language (A4's CatCongRight). */
  lemma ReplaceRightR10(a: Re, b1: Re, b2: Re, s: seq<char>)
    requires forall t :: Matches(b1, t) <==> Matches(b2, t)
    ensures Matches(Cat(a, b1), s) <==> Matches(Cat(a, b2), s)
  {
    CatCongRight(a, b1, b2, s);
  }

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: R10.H1d
  // pair: R10.H1v
  // uses: subset-type, by-method, ghost
  /** **H1.** Implement the method half of TryPacketR10: accept exactly the
      normal inputs, each in a packet whose ghost count is its node count, and
      reject the rest. The function body is the model the method must equal.
      What must hold at the moment you build a TypedPacketR10, and which value
      may the ghost count take? */
  function TryPacketR10(r: Re): PacketChoiceR10
  {
    if Normal(r) then HasPacketR10(CountPacketR10(r, NodeCount(r))) else NoPacketR10
  } by method {
    assume false;
  }
  // Hint(1): the compiled branch can call Normal (it is not ghost); the count is ghost and is not computed at run time.
  // Hint(2): a TypedPacketR10 literal is checked against its subset predicate where it is built: count == NodeCount(expr).

  // item: R10.H2d
  // pair: R10.H2v
  // uses: subset-type, by-method, ghost
  /** **H2.** Implement the method half of CatPacketR10: the packet of
      MkCat(a.expr, b.expr), with its ghost count rebuilt from the two packets'
      counts rather than by traversing the result. In which cases of MkCat is
      the result one of the operands, and what do the operands' subset
      predicates tell you then? */
  function CatPacketR10(a: TypedPacketR10, b: TypedPacketR10): TypedPacketR10
  {
    CountPacketR10(MkCat(a.expr, b.expr), NodeCount(MkCat(a.expr, b.expr)))
  } by method {
    assume false;
  }
  // Hint(1): follow MkCat's four branches; a ghost let can be an if-expression over the same tests.
  // Hint(2): a.count == NodeCount(a.expr) and b.count == NodeCount(b.expr) hold by the subset type; NodeCount(Cat(x, y)) is 1 + both.

  // item: R10.H3d
  // pair: R10.H3v
  /** **H3.** Normalizing a regex that is already normal returns it unchanged.
      Prove it by structural induction (the lever {:induction false} keeps the
      hypotheses yours). For which constructors does Norm call a smart
      constructor on normalized children, and why does each smart constructor
      return its plain node when the children are normal? */
  lemma {:induction false} NormalFixedR10(r: NormRe)
    ensures Norm(r) == r
    decreases r
  {
    assume false;
  }
  // Hint(1): the leaves are their own normal form; each recursive constructor needs its children's hypotheses.
  // Hint(2): Normal(Alt(a, b)) excludes Empty children and a == b, so MkAlt takes its last branch; Cat and Star likewise.

  // Given: idempotence follows from H3, because Norm's result is normal.
  lemma {:induction false} NormIdempotentR10(r: Re)
    ensures Norm(Norm(r)) == Norm(r)
  {
    NormalFixedR10(Norm(r));
  }

  // item: R10.H4d
  // pair: R10.H4v
  // uses: subset-type, by-method
  /** **H4.** Implement the method half of NormalizePacketR10: the compiled
      structural normalizer whose result equals the ghost model Norm(r),
      packed with its count. Reuse H1 and H2 where they fit. Norm is ghost, so
      the method cannot call it: which compiled operations compute each case,
      and what keeps the recursion's measure? */
  function NormalizePacketR10(r: Re): TypedPacketR10
    decreases r
  {
    CountPacketR10(Norm(r), NodeCount(Norm(r)))
  } by method {
    assume false;
  }
  // Hint(1): MkAlt, MkCat and MkStar are compiled; the recursion on the children follows the function's decreases r.
  // Hint(2): TryPacketR10 packs a leaf (a leaf is normal) and CatPacketR10 packs a Cat; Alt and Star need their own packets.

  // Given (not an item): the compiled use-site check of H1, H2 and H4. It runs
  // your method bodies; `scripts/vcheck --test` executes it once they are done.
  @Test
  method PacketSampleTest()
  {
    var accepted := TryPacketR10(Cat(Chr('a'), Chr('b')));
    expect accepted.HasPacketR10?;
    var rejected := TryPacketR10(Alt(Empty, Chr('a')));
    expect rejected.NoPacketR10?;
    var joined := CatPacketR10(accepted.packet, accepted.packet);
    expect joined.expr == Cat(Cat(Chr('a'), Chr('b')), Cat(Chr('a'), Chr('b')));
    var normal := NormalizePacketR10(Star(Star(Alt(Chr('c'), Empty))));
    expect normal.expr == Star(Chr('c'));
  }
}
