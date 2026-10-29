// Reference Solution.
/*! R16 capstone agent file (rung 14: reviewer, co-developer, adversary). A second
optimizer for rexc's VM: `ShortcutSplitR16` threads every jump and both targets
of every split through one jump. Its statement, `ShortcutSplitCorrectR16`, is
frozen: both directions, from every address. The shipped optimizer holds one
planted defect (chapter §14). Snapshot this file under research/R16/ before any
contractor edit. The contractor (/contract R16, a fresh session, contract R-v1)
may edit only the optimizer (`ThruR16`, `HopSplitR16`, `ShortcutSplitR16`) and
write the body of `ShortcutSplitCorrectR16` and its helper lemmas; the
statement, the imports and this header stay. A delivery that weakens the
statement fails specfreeze --check R16, and your trust-report must say FAIL on
it. Acceptance: scripts/vcheck --gate on this file exits 0 with zero holes,
scripts/vaudit reports no finding, and scripts/specfreeze --check R16 reports none.
*/
module R16_AgentCapstone {
  // specfreeze: frozen-imports
  import opened RG_A1_Re
  import opened RG_A5_VM

  // Where a thread at address `a` may go at once: through one jump, if `a`
  // holds one; otherwise `a` itself.
  function ThruR16(p: Prog, a: int): int
  {
    if 0 <= a < |p| && p[a].IJmp? then p[a].x else a
  }

  function HopSplitR16(p: Prog, ins: Inst): Inst
  {
    match ins
    case IJmp(a) => IJmp(ThruR16(p, a))
    case ISplit(x, y) => ISplit(ThruR16(p, x), ThruR16(p, y))
    case _ => ins
  }

  function ShortcutSplitR16(p: Prog): Prog
  {
    seq(|p|, i requires 0 <= i < |p| => HopSplitR16(p, p[i]))
  }

  // item: R16.A1d
  // @hole-begin R16.A1d
  lemma ThruForwardR16(p: Prog, a: int, w: seq<char>, f: nat) returns (g: nat)
    requires Accepts(p, a, w, f)
    ensures g <= f && Accepts(p, ThruR16(p, a), w, g)
  {
    if 0 <= a < |p| && p[a].IJmp? {
      AcceptsJmp(p, a, w, f);
      g := f - 1;
    } else {
      g := f;
    }
  }

  lemma ThruBackR16(p: Prog, a: int, w: seq<char>, g: nat) returns (f: nat)
    requires Accepts(p, ThruR16(p, a), w, g)
    ensures Accepts(p, a, w, f)
  {
    if 0 <= a < |p| && p[a].IJmp? {
      AcceptsJmp(p, a, w, g + 1);
      f := g + 1;
    } else {
      f := g;
    }
  }

  lemma ToSplitR16(p: Prog, pc: int, w: seq<char>, f: nat) returns (g: nat)
    requires Accepts(p, pc, w, f)
    ensures Accepts(ShortcutSplitR16(p), pc, w, g)
    decreases f
  {
    var q := ShortcutSplitR16(p);
    AcceptsInside(p, pc, w, f);
    match p[pc]
    case IMatch =>
      AcceptsMatch(p, pc, w, f);
      AcceptsMatch(q, pc, w, 1);
      g := 1;
    case IChar(c) =>
      AcceptsChar(p, pc, w, f);
      var g1 := ToSplitR16(p, pc + 1, w[1..], f - 1);
      g := g1 + 1;
      AcceptsChar(q, pc, w, g);
    case ISplit(x, y) =>
      AcceptsSplit(p, pc, w, f);
      var b := if Accepts(p, x, w, f - 1) then x else y;
      var f1 := ThruForwardR16(p, b, w, f - 1);
      var g1 := ToSplitR16(p, ThruR16(p, b), w, f1);
      g := g1 + 1;
      AcceptsSplit(q, pc, w, g);
    case IJmp(a) =>
      AcceptsJmp(p, pc, w, f);
      var f1 := ThruForwardR16(p, a, w, f - 1);
      var g1 := ToSplitR16(p, ThruR16(p, a), w, f1);
      g := g1 + 1;
      AcceptsJmp(q, pc, w, g);
  }

  lemma FromSplitR16(p: Prog, pc: int, w: seq<char>, f: nat) returns (g: nat)
    requires Accepts(ShortcutSplitR16(p), pc, w, f)
    ensures Accepts(p, pc, w, g)
    decreases f
  {
    var q := ShortcutSplitR16(p);
    AcceptsInside(q, pc, w, f);
    match p[pc]
    case IMatch =>
      AcceptsMatch(q, pc, w, f);
      AcceptsMatch(p, pc, w, 1);
      g := 1;
    case IChar(c) =>
      AcceptsChar(q, pc, w, f);
      var g1 := FromSplitR16(p, pc + 1, w[1..], f - 1);
      g := g1 + 1;
      AcceptsChar(p, pc, w, g);
    case ISplit(x, y) =>
      AcceptsSplit(q, pc, w, f);
      var b := if Accepts(q, ThruR16(p, x), w, f - 1) then x else y;
      var g1 := FromSplitR16(p, ThruR16(p, b), w, f - 1);
      var g2 := ThruBackR16(p, b, w, g1);
      g := g2 + 1;
      AcceptsSplit(p, pc, w, g);
    case IJmp(a) =>
      AcceptsJmp(q, pc, w, f);
      var g1 := FromSplitR16(p, ThruR16(p, a), w, f - 1);
      var g2 := ThruBackR16(p, a, w, g1);
      g := g2 + 1;
      AcceptsJmp(p, pc, w, g);
  }
  // @hole-end R16.A1d

  lemma ShortcutSplitCorrectR16(p: Prog, pc: int, w: seq<char>)
    ensures AcceptsFrom(ShortcutSplitR16(p), pc, w) <==> AcceptsFrom(p, pc, w)
  {
    // @hole-begin R16.A1d
    if AcceptsFrom(p, pc, w) {
      var f: nat :| Accepts(p, pc, w, f);
      var g := ToSplitR16(p, pc, w, f);
    }
    if AcceptsFrom(ShortcutSplitR16(p), pc, w) {
      var f: nat :| Accepts(ShortcutSplitR16(p), pc, w, f);
      var g := FromSplitR16(p, pc, w, f);
    }
    // @hole-end R16.A1d
  }
}
