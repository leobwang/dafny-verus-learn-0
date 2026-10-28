// Reference Solution.
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
// CHECK P1dv
// item: R16.P2dv verdict
/** whole-d and whole-v state completeness for whole programs only and prove a
    concatenation by calling the lemma on its two halves. Predict both verdict
    and stage pairs. Answer form: D:<verdict>,<stage> V:<verdict>,<stage>. */
// CHECK P2dv

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
    // @hole-begin R16.T1d
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      EmitSizeR16(a, pc + 1);
      EmitSizeR16(b, pc + 2 + |Emit(a, pc + 1)|);
    case Cat(a, b) =>
      EmitSizeR16(a, pc);
      EmitSizeR16(b, pc + |Emit(a, pc)|);
    case Star(a) =>
      EmitSizeR16(a, pc + 1);
    // @hole-end R16.T1d
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
  // @hole-begin R16.H2d
  lemma CompleteFuel(p: Prog, r: Re, pc: int, u: seq<char>, v: seq<char>, f: nat) returns (f2: nat)
    requires CodeAt(p, pc, Emit(r, pc))
    requires Matches(r, u)
    requires Accepts(p, pc + |Emit(r, pc)|, v, f)
    ensures Accepts(p, pc, u + v, f2)
    decreases r, |u|, 1
  {
    match r
    case Eps =>
      assert u + v == v;
      f2 := f;
    case Chr(c) =>
      LayoutOne(p, pc, r);
      assert (u + v)[1..] == v;
      f2 := f + 1;
      AcceptsChar(p, pc, u + v, f2);
    case Alt(a, b) =>
      f2 := CompleteAlt(p, a, b, pc, u, v, f);
    case Cat(a, b) =>
      f2 := CompleteCat(p, a, b, pc, u, v, f);
    case Star(a) =>
      f2 := CompleteStar(p, a, pc, u, v, f);
  }

  lemma {:isolate_assertions} CompleteAlt(p: Prog, a: Re, b: Re, pc: int, u: seq<char>, v: seq<char>, f: nat) returns (f2: nat)
    requires CodeAt(p, pc, Emit(Alt(a, b), pc))
    requires Matches(Alt(a, b), u)
    requires Accepts(p, pc + |Emit(Alt(a, b), pc)|, v, f)
    ensures Accepts(p, pc, u + v, f2)
    decreases Alt(a, b), |u|, 0
  {
    LayoutAlt(p, pc, a, b);
    var ca := Emit(a, pc + 1);
    EmitLenAlt(a, b, pc);
    var f1;
    if Matches(a, u) {
      AcceptsJmp(p, pc + 1 + |ca|, v, f + 1);
      f1 := CompleteFuel(p, a, pc + 1, u, v, f + 1);
    } else {
      f1 := CompleteFuel(p, b, pc + 2 + |ca|, u, v, f);
    }
    f2 := f1 + 1;
    AcceptsSplit(p, pc, u + v, f2);
  }

  lemma CompleteCat(p: Prog, a: Re, b: Re, pc: int, u: seq<char>, v: seq<char>, f: nat) returns (f2: nat)
    requires CodeAt(p, pc, Emit(Cat(a, b), pc))
    requires Matches(Cat(a, b), u)
    requires Accepts(p, pc + |Emit(Cat(a, b), pc)|, v, f)
    ensures Accepts(p, pc, u + v, f2)
    decreases Cat(a, b), |u|, 0
  {
    LayoutCat(p, pc, a, b);
    var ca := Emit(a, pc);
    var cb := Emit(b, pc + |ca|);
    assert |Emit(Cat(a, b), pc)| == |ca| + |cb|;
    var k :| 0 <= k <= |u| && Matches(a, u[..k]) && Matches(b, u[k..]);
    var f1 := CompleteFuel(p, b, pc + |Emit(a, pc)|, u[k..], v, f);
    f2 := CompleteFuel(p, a, pc, u[..k], u[k..] + v, f1);
    assert u[..k] + (u[k..] + v) == u + v;
  }

  lemma CompleteStar(p: Prog, a: Re, pc: int, u: seq<char>, v: seq<char>, f: nat) returns (f2: nat)
    requires CodeAt(p, pc, Emit(Star(a), pc))
    requires Matches(Star(a), u)
    requires Accepts(p, pc + |Emit(Star(a), pc)|, v, f)
    ensures Accepts(p, pc, u + v, f2)
    decreases Star(a), |u|, 0
  {
    LayoutStar(p, pc, a);
    var ca := Emit(a, pc + 1);
    if u == [] {
      assert u + v == v;
      f2 := f + 1;
    } else {
      var k :| 0 < k <= |u| && Matches(a, u[..k]) && Matches(Star(a), u[k..]);
      var f1 := CompleteFuel(p, Star(a), pc, u[k..], v, f);
      AcceptsJmp(p, pc + 1 + |ca|, u[k..] + v, f1 + 1);
      var f3 := CompleteFuel(p, a, pc + 1, u[..k], u[k..] + v, f1 + 1);
      assert u[..k] + (u[k..] + v) == u + v;
      f2 := f3 + 1;
    }
    AcceptsSplit(p, pc, u + v, f2);
  }
  // @hole-end R16.H2d

  lemma EmitComplete(p: Prog, r: Re, pc: int, u: seq<char>, v: seq<char>)
    ensures EmitCompleteStatement(p, r, pc, u, v)
  {
    // @hole-begin R16.H2d
    if CodeAt(p, pc, Emit(r, pc)) && Matches(r, u) && AcceptsFrom(p, pc + |Emit(r, pc)|, v) {
      var f: nat :| Accepts(p, pc + |Emit(r, pc)|, v, f);
      var f2 := CompleteFuel(p, r, pc, u, v, f);
    }
    // @hole-end R16.H2d
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
  // @hole-begin R16.H3d
  lemma SoundFuel(p: Prog, r: Re, pc: int, w: seq<char>, f: nat) returns (k: nat, f2: nat)
    requires CodeAt(p, pc, Emit(r, pc))
    requires Accepts(p, pc, w, f)
    ensures k <= |w| && f2 <= f
    ensures Matches(r, w[..k]) && Accepts(p, pc + |Emit(r, pc)|, w[k..], f2)
    decreases f, r, 1
  {
    match r
    case Empty =>
      LayoutOne(p, pc, r);
      AcceptsJmp(p, pc, w, f);
      k, f2 := SoundFuel(p, r, pc, w, f - 1);
    case Eps =>
      assert w[..0] == [] && w[0..] == w;
      k, f2 := 0, f;
    case Chr(c) =>
      LayoutOne(p, pc, r);
      AcceptsChar(p, pc, w, f);
      assert w[..1] == [c];
      k, f2 := 1, f - 1;
    case Alt(a, b) =>
      k, f2 := SoundAlt(p, a, b, pc, w, f);
    case Cat(a, b) =>
      k, f2 := SoundCat(p, a, b, pc, w, f);
    case Star(a) =>
      k, f2 := SoundStar(p, a, pc, w, f);
  }

  lemma {:isolate_assertions} SoundAlt(p: Prog, a: Re, b: Re, pc: int, w: seq<char>, f: nat) returns (k: nat, f2: nat)
    requires CodeAt(p, pc, Emit(Alt(a, b), pc))
    requires Accepts(p, pc, w, f)
    ensures k <= |w| && f2 <= f
    ensures Matches(Alt(a, b), w[..k]) && Accepts(p, pc + |Emit(Alt(a, b), pc)|, w[k..], f2)
    decreases f, Alt(a, b), 0
  {
    LayoutAlt(p, pc, a, b);
    var ca := Emit(a, pc + 1);
    var cb := Emit(b, pc + 2 + |ca|);
    EmitLenAlt(a, b, pc);
    AcceptsSplit(p, pc, w, f);
    if Accepts(p, pc + 1, w, f - 1) {
      var f1;
      k, f1 := SoundFuel(p, a, pc + 1, w, f - 1);
      AcceptsJmp(p, pc + 1 + |ca|, w[k..], f1);
      f2 := f1 - 1;
      assert Accepts(p, pc + 2 + |ca| + |cb|, w[k..], f2);
    } else {
      k, f2 := SoundFuel(p, b, pc + 2 + |ca|, w, f - 1);
      assert Accepts(p, pc + 2 + |ca| + |cb|, w[k..], f2);
    }
  }

  lemma SoundCat(p: Prog, a: Re, b: Re, pc: int, w: seq<char>, f: nat) returns (k: nat, f2: nat)
    requires CodeAt(p, pc, Emit(Cat(a, b), pc))
    requires Accepts(p, pc, w, f)
    ensures k <= |w| && f2 <= f
    ensures Matches(Cat(a, b), w[..k]) && Accepts(p, pc + |Emit(Cat(a, b), pc)|, w[k..], f2)
    decreases f, Cat(a, b), 0
  {
    LayoutCat(p, pc, a, b);
    var ca := Emit(a, pc);
    var cb := Emit(b, pc + |ca|);
    assert |Emit(Cat(a, b), pc)| == |ca| + |cb|;
    var k1, f1 := SoundFuel(p, a, pc, w, f);
    var k2;
    k2, f2 := SoundFuel(p, b, pc + |Emit(a, pc)|, w[k1..], f1);
    k := k1 + k2;
    assert w[..k][..k1] == w[..k1];
    assert w[..k][k1..] == w[k1..][..k2];
    assert w[k1..][k2..] == w[k..];
  }

  lemma SoundStar(p: Prog, a: Re, pc: int, w: seq<char>, f: nat) returns (k: nat, f2: nat)
    requires CodeAt(p, pc, Emit(Star(a), pc))
    requires Accepts(p, pc, w, f)
    ensures k <= |w| && f2 <= f
    ensures Matches(Star(a), w[..k]) && Accepts(p, pc + |Emit(Star(a), pc)|, w[k..], f2)
    decreases f, Star(a), 0
  {
    LayoutStar(p, pc, a);
    var ca := Emit(a, pc + 1);
    AcceptsSplit(p, pc, w, f);
    if Accepts(p, pc + 1, w, f - 1) {
      var k1, f1 := SoundFuel(p, a, pc + 1, w, f - 1);
      AcceptsJmp(p, pc + 1 + |ca|, w[k1..], f1);
      var k2;
      k2, f2 := SoundFuel(p, Star(a), pc, w[k1..], f1 - 1);
      k := k1 + k2;
      assert w[k1..][k2..] == w[k..];
      if k1 > 0 {
        assert w[..k][..k1] == w[..k1];
        assert w[..k][k1..] == w[k1..][..k2];
      } else {
        assert w[..k] == w[k1..][..k2];
      }
    } else {
      assert w[..0] == [] && w[0..] == w;
      k, f2 := 0, f - 1;
    }
  }
  // @hole-end R16.H3d

  lemma EmitSound(p: Prog, r: Re, pc: int, w: seq<char>)
    ensures EmitSoundStatement(p, r, pc, w)
  {
    // @hole-begin R16.H3d
    if CodeAt(p, pc, Emit(r, pc)) && AcceptsFrom(p, pc, w) {
      var f: nat :| Accepts(p, pc, w, f);
      var k, f2 := SoundFuel(p, r, pc, w, f);
    }
    // @hole-end R16.H3d
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
  // @hole-begin R16.H4d
  lemma ToShortcut(p: Prog, pc: int, w: seq<char>, f: nat) returns (g: nat)
    requires Accepts(p, pc, w, f)
    ensures Accepts(Shortcut(p), pc, w, g)
    decreases f
  {
    var q := Shortcut(p);
    AcceptsInside(p, pc, w, f);
    match p[pc]
    case IMatch =>
      AcceptsMatch(p, pc, w, f);
      AcceptsMatch(q, pc, w, 1);
      g := 1;
    case IChar(c) =>
      AcceptsChar(p, pc, w, f);
      var g1 := ToShortcut(p, pc + 1, w[1..], f - 1);
      g := g1 + 1;
      AcceptsChar(q, pc, w, g);
    case ISplit(x, y) =>
      AcceptsSplit(p, pc, w, f);
      var g1;
      if Accepts(p, x, w, f - 1) {
        g1 := ToShortcut(p, x, w, f - 1);
      } else {
        g1 := ToShortcut(p, y, w, f - 1);
      }
      g := g1 + 1;
      AcceptsSplit(q, pc, w, g);
    case IJmp(a) =>
      AcceptsJmp(p, pc, w, f);
      var g1;
      if 0 <= a < |p| && p[a].IJmp? {
        AcceptsJmp(p, a, w, f - 1);
        g1 := ToShortcut(p, p[a].x, w, f - 2);
      } else {
        g1 := ToShortcut(p, a, w, f - 1);
      }
      g := g1 + 1;
      AcceptsJmp(q, pc, w, g);
  }

  lemma FromShortcut(p: Prog, pc: int, w: seq<char>, f: nat) returns (g: nat)
    requires Accepts(Shortcut(p), pc, w, f)
    ensures Accepts(p, pc, w, g)
    decreases f
  {
    var q := Shortcut(p);
    AcceptsInside(q, pc, w, f);
    match p[pc]
    case IMatch =>
      AcceptsMatch(q, pc, w, f);
      AcceptsMatch(p, pc, w, 1);
      g := 1;
    case IChar(c) =>
      AcceptsChar(q, pc, w, f);
      var g1 := FromShortcut(p, pc + 1, w[1..], f - 1);
      g := g1 + 1;
      AcceptsChar(p, pc, w, g);
    case ISplit(x, y) =>
      AcceptsSplit(q, pc, w, f);
      var g1;
      if Accepts(q, x, w, f - 1) {
        g1 := FromShortcut(p, x, w, f - 1);
      } else {
        g1 := FromShortcut(p, y, w, f - 1);
      }
      g := g1 + 1;
      AcceptsSplit(p, pc, w, g);
    case IJmp(a) =>
      AcceptsJmp(q, pc, w, f);
      if 0 <= a < |p| && p[a].IJmp? {
        var g1 := FromShortcut(p, p[a].x, w, f - 1);
        AcceptsJmp(p, a, w, g1 + 1);
        g := g1 + 2;
      } else {
        var g1 := FromShortcut(p, a, w, f - 1);
        g := g1 + 1;
      }
      AcceptsJmp(p, pc, w, g);
  }
  // @hole-end R16.H4d

  lemma ShortcutCorrect(p: Prog, pc: int, w: seq<char>)
    ensures AcceptsFrom(Shortcut(p), pc, w) <==> AcceptsFrom(p, pc, w)
  {
    // @hole-begin R16.H4d
    if AcceptsFrom(p, pc, w) {
      var f: nat :| Accepts(p, pc, w, f);
      var g := ToShortcut(p, pc, w, f);
    }
    if AcceptsFrom(Shortcut(p), pc, w) {
      var f: nat :| Accepts(Shortcut(p), pc, w, f);
      var g := FromShortcut(p, pc, w, f);
    }
    // @hole-end R16.H4d
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
    // @hole-begin R16.H5d
    var p := EmitProg(r);
    var code := Emit(r, 0);
    LayoutProg(r);
    if AcceptsFrom(p, 0, s) {
      EmitSound(p, r, 0, s);
      var k :| 0 <= k <= |s| && Matches(r, s[..k]) && AcceptsFrom(p, |code|, s[k..]);
      var f: nat :| Accepts(p, |code|, s[k..], f);
      AcceptsMatch(p, |code|, s[k..], f);
      assert s[..k] == s;
    }
    if Matches(r, s) {
      AcceptsMatch(p, |code|, [], 1);
      EmitComplete(p, r, 0, s, []);
      assert s + [] == s;
    }
    // @hole-end R16.H5d
  }
  // Hint(1): A5's `LayoutProg` places `Emit(r, 0)` at address 0 and `IMatch` right after it; the continuation is that one instruction.
  // Hint(2): `AcceptsMatch` accepts only the empty word, so the split your soundness statement returns must be the whole word; completeness needs the continuation to accept `[]`, with one unit of fuel.
}
