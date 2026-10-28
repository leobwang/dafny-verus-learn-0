// Probe: A5 reconciled (word-relative VM, opaque Accepts, one-step lemmas, Emit, CodeAt,
// layout lemmas) + R16 reference proofs of the fuel-free generalized statements.
module RG_A5_VM_Probe {
  import opened RG_A1_Re

  datatype Inst = IChar(c: char) | ISplit(x: int, y: int) | IJmp(x: int) | IMatch
  type Prog = seq<Inst>

  opaque predicate Accepts(p: Prog, pc: int, w: seq<char>, fuel: nat)
    decreases fuel
  {
    fuel > 0 && 0 <= pc < |p| &&
    match p[pc]
    case IChar(c) => |w| > 0 && w[0] == c && Accepts(p, pc + 1, w[1..], fuel - 1)
    case ISplit(x, y) => Accepts(p, x, w, fuel - 1) || Accepts(p, y, w, fuel - 1)
    case IJmp(x) => Accepts(p, x, w, fuel - 1)
    case IMatch => w == []
  }

  ghost predicate AcceptsFrom(p: Prog, pc: int, w: seq<char>)
  {
    exists fuel: nat :: Accepts(p, pc, w, fuel)
  }

  lemma AcceptsChar(p: Prog, pc: int, w: seq<char>, fuel: nat)
    requires 0 <= pc < |p| && p[pc].IChar?
    ensures Accepts(p, pc, w, fuel) <==>
            fuel > 0 && |w| > 0 && w[0] == p[pc].c && Accepts(p, pc + 1, w[1..], fuel - 1)
  {
    reveal Accepts();
  }

  lemma AcceptsSplit(p: Prog, pc: int, w: seq<char>, fuel: nat)
    requires 0 <= pc < |p| && p[pc].ISplit?
    ensures Accepts(p, pc, w, fuel) <==>
            fuel > 0 && (Accepts(p, p[pc].x, w, fuel - 1) || Accepts(p, p[pc].y, w, fuel - 1))
  {
    reveal Accepts();
  }

  lemma AcceptsJmp(p: Prog, pc: int, w: seq<char>, fuel: nat)
    requires 0 <= pc < |p| && p[pc].IJmp?
    ensures Accepts(p, pc, w, fuel) <==> fuel > 0 && Accepts(p, p[pc].x, w, fuel - 1)
  {
    reveal Accepts();
  }

  lemma AcceptsMatch(p: Prog, pc: int, w: seq<char>, fuel: nat)
    requires 0 <= pc < |p| && p[pc] == IMatch
    ensures Accepts(p, pc, w, fuel) <==> fuel > 0 && w == []
  {
    reveal Accepts();
  }

  lemma AcceptsInside(p: Prog, pc: int, w: seq<char>, fuel: nat)
    requires Accepts(p, pc, w, fuel)
    ensures fuel > 0 && 0 <= pc < |p|
  {
    reveal Accepts();
  }

  function Emit(r: Re, pc: int): seq<Inst>
    decreases r
  {
    match r
    case Empty => [IJmp(pc)]
    case Eps => []
    case Chr(c) => [IChar(c)]
    case Alt(a, b) =>
      var ca := Emit(a, pc + 1);
      var cb := Emit(b, pc + 2 + |ca|);
      [ISplit(pc + 1, pc + 2 + |ca|)] + ca + [IJmp(pc + 2 + |ca| + |cb|)] + cb
    case Cat(a, b) =>
      var ca := Emit(a, pc);
      ca + Emit(b, pc + |ca|)
    case Star(a) =>
      var ca := Emit(a, pc + 1);
      [ISplit(pc + 1, pc + 2 + |ca|)] + ca + [IJmp(pc)]
  }

  function EmitProg(r: Re): Prog
  {
    Emit(r, 0) + [IMatch]
  }

  predicate CodeAt(p: Prog, pc: int, code: seq<Inst>)
  {
    0 <= pc && pc + |code| <= |p| && forall k | 0 <= k < |code| :: p[pc + k] == code[k]
  }

  lemma LayoutOne(p: Prog, pc: int, r: Re)
    requires r.Empty? || r.Chr?
    requires CodeAt(p, pc, Emit(r, pc))
    ensures p[pc] == Emit(r, pc)[0]
  {
  }

  lemma LayoutAlt(p: Prog, pc: int, a: Re, b: Re)
    requires CodeAt(p, pc, Emit(Alt(a, b), pc))
    ensures var ca := Emit(a, pc + 1);
            var cb := Emit(b, pc + 2 + |ca|);
            p[pc] == ISplit(pc + 1, pc + 2 + |ca|) && CodeAt(p, pc + 1, ca)
            && p[pc + 1 + |ca|] == IJmp(pc + 2 + |ca| + |cb|) && CodeAt(p, pc + 2 + |ca|, cb)
  {
    var code := Emit(Alt(a, b), pc);
    var ca := Emit(a, pc + 1);
    var cb := Emit(b, pc + 2 + |ca|);
    assert p[pc] == code[0];
    assert p[pc + 1 + |ca|] == code[1 + |ca|];
    forall k | 0 <= k < |ca| ensures p[pc + 1 + k] == ca[k] {
      assert code[1 + k] == ca[k];
    }
    forall k | 0 <= k < |cb| ensures p[pc + 2 + |ca| + k] == cb[k] {
      assert code[2 + |ca| + k] == cb[k];
    }
  }

  lemma EmitLenAlt(a: Re, b: Re, pc: int)
    ensures var ca := Emit(a, pc + 1);
            |Emit(Alt(a, b), pc)| == 2 + |ca| + |Emit(b, pc + 2 + |ca|)|
  {
  }

  lemma LayoutCat(p: Prog, pc: int, a: Re, b: Re)
    requires CodeAt(p, pc, Emit(Cat(a, b), pc))
    ensures var ca := Emit(a, pc);
            var cb := Emit(b, pc + |ca|);
            CodeAt(p, pc, ca) && CodeAt(p, pc + |ca|, cb)
  {
    var code := Emit(Cat(a, b), pc);
    var ca := Emit(a, pc);
    var cb := Emit(b, pc + |ca|);
    forall k | 0 <= k < |ca| ensures p[pc + k] == ca[k] {
      assert code[k] == ca[k];
    }
    forall k | 0 <= k < |cb| ensures p[pc + |ca| + k] == cb[k] {
      assert code[|ca| + k] == cb[k];
    }
  }

  lemma LayoutStar(p: Prog, pc: int, a: Re)
    requires CodeAt(p, pc, Emit(Star(a), pc))
    ensures var ca := Emit(a, pc + 1);
            p[pc] == ISplit(pc + 1, pc + 2 + |ca|) && CodeAt(p, pc + 1, ca)
            && p[pc + 1 + |ca|] == IJmp(pc)
  {
    var code := Emit(Star(a), pc);
    var ca := Emit(a, pc + 1);
    assert p[pc] == code[0];
    assert p[pc + 1 + |ca|] == code[1 + |ca|];
    forall k | 0 <= k < |ca| ensures p[pc + 1 + k] == ca[k] {
      assert code[1 + k] == ca[k];
    }
  }
}

module R16_Thread {
  import opened RG_A1_Re
  import opened RG_A5_VM_Probe

  function Hop(p: Prog, ins: Inst): Inst
  {
    if ins.IJmp? && 0 <= ins.x < |p| && p[ins.x].IJmp? then IJmp(p[ins.x].x) else ins
  }

  function Shortcut(p: Prog): Prog
  {
    seq(|p|, i requires 0 <= i < |p| => Hop(p, p[i]))
  }

  lemma ToShortcut(p: Prog, pc: int, w: seq<char>, f: nat) returns (g: nat)
    requires Accepts(p, pc, w, f)
    ensures Accepts(Shortcut(p), pc, w, g)
    decreases f
  {
    var q := Shortcut(p);
    AcceptsInside(p, pc, w, f);
    var ins := p[pc];
    match ins
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
      if 0 <= a < |p| && p[a].IJmp? {
        AcceptsJmp(p, a, w, f - 1);
        var g1 := ToShortcut(p, p[a].x, w, f - 2);
        g := g1 + 1;
      } else {
        var g1 := ToShortcut(p, a, w, f - 1);
        g := g1 + 1;
      }
      AcceptsJmp(q, pc, w, g);
  }

  lemma FromShortcut(p: Prog, pc: int, w: seq<char>, f: nat) returns (g: nat)
    requires Accepts(Shortcut(p), pc, w, f)
    ensures Accepts(p, pc, w, g)
    decreases f
  {
    var q := Shortcut(p);
    AcceptsInside(q, pc, w, f);
    var ins := p[pc];
    match ins
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

  lemma ShortcutCorrect(p: Prog, pc: int, w: seq<char>)
    ensures AcceptsFrom(Shortcut(p), pc, w) <==> AcceptsFrom(p, pc, w)
  {
    if AcceptsFrom(p, pc, w) {
      var f: nat :| Accepts(p, pc, w, f);
      var g := ToShortcut(p, pc, w, f);
    }
    if AcceptsFrom(Shortcut(p), pc, w) {
      var f: nat :| Accepts(Shortcut(p), pc, w, f);
      var g := FromShortcut(p, pc, w, f);
    }
  }
}
