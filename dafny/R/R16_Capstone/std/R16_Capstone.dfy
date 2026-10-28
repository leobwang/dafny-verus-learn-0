/*!
# R16 — Capstone (Exercises)

Standalone R track. Import only the frozen layers A1 and A5 and your own
statement file R16_Statements.dfy; no earlier learner file is needed. The
paired exercise is verus/r/r16_capstone/src/lib.rs.

Record the two predictions first (scripts/firsttry.sh R16 --check: the
CHECK lines of the prediction block below, answered in slots/R16.slots), then
attempt T1 closed book before reading the chapter. Then work on paper first
(the chapter's §2: the blueprint is graded before you formalize), write and
freeze your statements (H1, in R16_Statements.dfy), and only then prove them
here. Five typed items ship in this language: T1, H1 (in the statement file),
H2, H3 and H4; H4 (jump threading) is the gated optimizer.

File order: the test-out T1, completeness H2 (your helper lemmas, then
`EmitComplete`), soundness H3 (helpers, then `EmitSound`), the optimizer H4
(the given `Hop` and `Shortcut`, your helpers, then `ShortcutCorrect`) and the
whole-program theorem H5. A5's `Accepts` is opaque: use its one-step lemmas
(`AcceptsChar`, `AcceptsSplit`, `AcceptsJmp`, `AcceptsMatch`) and
`AcceptsInside`, never a reveal.

Done: scripts/vcheck --gate dafny/R/R16_Capstone/std exits 0 with zero holes,
scripts/vaudit dafny/R/R16_Capstone/std reports no finding,
scripts/specfreeze --check R16 reports none, and
scripts/firsttry.sh R16 --report --strict exits 0.
*/

// =============================================================================
// Prediction block: do not run the subjects until these slots are recorded
// =============================================================================

// item: R16.P1dv verdict
/** vacuous-d and vacuous-v state a completeness candidate whose code runs past
    the end of its program, and prove it with an empty body. Predict both
    verdict and stage pairs. Answer form: D:<verdict>,<stage> V:<verdict>,<stage>. */
// SLOT: CHECK P1dv
// item: R16.P2dv verdict
/** whole-d and whole-v state completeness for whole programs only and prove a
    concatenation by calling the lemma on its two halves. Predict both verdict
    and stage pairs. Answer form: D:<verdict>,<stage> V:<verdict>,<stage>. */
// SLOT: CHECK P2dv

module R16_Capstone {
  // specfreeze: frozen-imports
  import opened RG_A1_Re
  import opened RG_A5_VM
  import opened R16_Statements

  // ===========================================================================
  // Test-out (closed book)
  // ===========================================================================

  // item: R16.T1d
  // uses: lemma-recursion
  // pair: R16.T1v
  /** **T1.** Closed book: the code A5 emits for `r` is at most two
      instructions per node of `r`, wherever it is placed. Which constructors
      emit more instructions than they have children, and at which addresses
      does `Emit` place the code of each child? */
  lemma EmitSizeR16(r: Re, pc: int)
    ensures |Emit(r, pc)| <= 2 * NodeCount(r)
  {
    assume false;
  }
  // Hint(1): induction on `r`, one call per child; this unit proves no lemma by induction on its own (manual-lemma-induction).
  // Hint(2): read the addresses off `Emit`: an `Alt`'s right child sits at `pc + 2 + |Emit(a, pc + 1)|`, a `Cat`'s at `pc + |Emit(a, pc)|`.

  // ===========================================================================
  // Completeness
  // ===========================================================================

  // item: R16.H2d
  // uses: lemma-recursion, lexicographic-decreases
  // pair: R16.H2v
  /** **H2.** Prove your frozen completeness statement. Write your helper
      lemmas above `EmitComplete`, then its body. `AcceptsFrom` hides the fuel,
      so the induction runs on a fuelled helper: from an accepting run of the
      continuation with fuel `f`, build one of `r`'s code with some fuel `f2`.
      Which constructor's case recurses on the same regex, and what then
      becomes smaller? Which addresses does each layout lemma name? */
  // Your helper lemmas (H2), here.

  lemma EmitComplete(p: Prog, r: Re, pc: int, u: seq<char>, v: seq<char>)
    ensures EmitCompleteStatement(p, r, pc, u, v)
  {
    assume false;
  }
  // Hint(1): a fuelled helper by induction on `r`, with `Star` by induction on the length of the word: the first pass through `a` reads a non-empty chunk (A1's `Matches` gives it), and the rest is a shorter match of `Star(a)`.
  // Hint(2): `LayoutAlt`, `LayoutCat` and `LayoutStar` name each child's address and the jumps between them; `AcceptsSplit` and `AcceptsJmp` take one step each, so the fuel grows by one per instruction you pass.

  // ===========================================================================
  // Soundness
  // ===========================================================================

  // item: R16.H3d
  // uses: lemma-recursion, lexicographic-decreases
  // pair: R16.H3v
  /** **H3.** Prove your frozen soundness statement. Write your helper lemmas
      above `EmitSound`, then its body. Here the induction runs on the fuel of
      the given run: from a run of `r`'s code with fuel `f`, find the split
      point `k` and a run of the continuation with no more fuel. Which cases
      spend no fuel before they recurse, and on what? How does a `Split`
      decide which branch to follow? */
  // Your helper lemmas (H3), here.

  lemma EmitSound(p: Prog, r: Re, pc: int, w: seq<char>)
    ensures EmitSoundStatement(p, r, pc, w)
  {
    assume false;
  }
  // Hint(1): a fuelled helper by induction on the fuel first and the regex second: `Cat` and the entry of `Alt` and `Star` recurse on a smaller regex with the same fuel, an `Empty`'s self-jump on the same regex with less.
  // Hint(2): `AcceptsSplit` says which of the two branches holds the run (test one with `if`); `Star`'s loop body may read the empty word, so treat a first chunk of length 0 apart when you join the two matches.

  // ===========================================================================
  // The optimizer (gated)
  // ===========================================================================

  // One-hop jump threading: a jump whose target is a jump goes straight to the
  // second jump's target. Every other instruction, and a jump whose target is
  // not a jump (or is outside the program), is unchanged. A self-loop stays one.
  function Hop(p: Prog, ins: Inst): Inst
  {
    if ins.IJmp? && 0 <= ins.x < |p| && p[ins.x].IJmp? then IJmp(p[ins.x].x) else ins
  }

  function Shortcut(p: Prog): Prog
  {
    seq(|p|, i requires 0 <= i < |p| => Hop(p, p[i]))
  }

  // item: R16.H4d
  // uses: lemma-recursion
  // pair: R16.H4v
  /** **H4.** Prove that threading every jump changes no state's language, in
      both directions, from every address. Write your helper lemmas above
      `ShortcutCorrect`, then its body. A threaded jump skips one instruction
      of the original, so one direction spends more fuel than the other. Which
      direction is that, and what does `AcceptsInside` give you before you
      look at the instruction at `pc`? */
  // Your helper lemmas (H4), here.

  lemma ShortcutCorrect(p: Prog, pc: int, w: seq<char>)
    ensures AcceptsFrom(Shortcut(p), pc, w) <==> AcceptsFrom(p, pc, w)
  {
    assume false;
  }
  // Hint(1): one fuelled helper per direction, each by induction on the fuel, with one case per instruction kind at `pc`; the threaded jump is the only case where the two programs differ.
  // Hint(2): from the original to the threaded program, a jump to a jump spends two steps of the original for one of the threaded; the other way, rebuild the skipped jump with `AcceptsJmp(p, a, w, g1 + 1)`.

  // ===========================================================================
  // The whole-program theorem
  // ===========================================================================

  // item: R16.H5d
  // pair: R16.H5v
  /** **H5.** The compiled program, `Emit(r, 0)` followed by `IMatch`, accepts
      exactly the words `r` matches. Use only your two statements (through
      `EmitComplete` and `EmitSound`) and A5's one-step lemmas. Which
      continuation does each direction need, and which word does the final
      `IMatch` accept? */
  lemma EmitCorrect(r: Re, s: seq<char>)
    ensures AcceptsFrom(EmitProg(r), 0, s) <==> Matches(r, s)
  {
    assume false;
  }
  // Hint(1): A5's `LayoutProg` places `Emit(r, 0)` at address 0 and `IMatch` right after it; the continuation is that one instruction.
  // Hint(2): `AcceptsMatch` accepts only the empty word, so the split your soundness statement returns must be the whole word; completeness needs the continuation to accept `[]`, with one unit of fuel.
}
