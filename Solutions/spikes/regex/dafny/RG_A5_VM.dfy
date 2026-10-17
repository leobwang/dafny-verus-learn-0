// DVR0 reference, layer A5 (author-only). Ships as dafny/given/R/RG_A5_VM.dfy, declared by
// R16 (PLAN §2.2, §2.5 step 7): the VM (Inst, Advance, the opaque fuelled Accepts and its four
// one-step lemmas) and CodeAt; the emitter (Emit, EmitProg), the layout lemmas over it and the
// correctness lemmas (EmitSound, EmitComplete, EmitCorrect and their per-constructor cases).
// Which of Emit and the layout lemmas ship given is DVR3's call (PLAN §2.2 lists the layout
// lemmas as given and the emitter as the learner's). Renamed from Step/Compile (PLAN §5.5).
module RG_A5_VM {
  import opened RG_A1_Re

  // ---------------------------------------------------------------------------
  // The VM (the frozen part of A5)
  // ---------------------------------------------------------------------------

  datatype Inst = IChar(c: char) | ISplit(x: int, y: int) | IJmp(x: int) | IMatch
  type Prog = seq<Inst>
  datatype VmThread = VmThread(pc: int, pos: nat)

  // The successors of one thread: none, one, or two (a Split).
  function Advance(p: Prog, s: seq<char>, t: VmThread): seq<VmThread>
  {
    if !(0 <= t.pc < |p|) then []
    else
      match p[t.pc]
      case IChar(c) => if t.pos < |s| && s[t.pos] == c then [VmThread(t.pc + 1, t.pos + 1)] else []
      case ISplit(x, y) => [VmThread(x, t.pos), VmThread(y, t.pos)]
      case IJmp(x) => [VmThread(x, t.pos)]
      case IMatch => []
  }

  predicate Final(p: Prog, s: seq<char>, t: VmThread)
  {
    0 <= t.pc < |p| && p[t.pc] == IMatch && t.pos == |s|
  }

  // Some path of at most `fuel` steps from t reaches a final thread.
  opaque predicate Accepts(p: Prog, s: seq<char>, t: VmThread, fuel: nat)
    decreases fuel
  {
    var ts := Advance(p, s, t);
    Final(p, s, t) ||
    (fuel > 0 && ((|ts| > 0 && Accepts(p, s, ts[0], fuel - 1)) ||
                  (|ts| > 1 && Accepts(p, s, ts[1], fuel - 1))))
  }

  // One step of Accepts at each kind of instruction (given with the VM).
  lemma AcceptsChar(p: Prog, s: seq<char>, pc: int, i: nat, fuel: nat)
    requires 0 <= pc < |p| && p[pc].IChar?
    ensures Accepts(p, s, VmThread(pc, i), fuel) <==>
            fuel > 0 && i < |s| && s[i] == p[pc].c && Accepts(p, s, VmThread(pc + 1, i + 1), fuel - 1)
  {
    reveal Accepts();
  }

  lemma AcceptsSplit(p: Prog, s: seq<char>, pc: int, i: nat, fuel: nat)
    requires 0 <= pc < |p| && p[pc].ISplit?
    ensures Accepts(p, s, VmThread(pc, i), fuel) <==>
            fuel > 0 && (Accepts(p, s, VmThread(p[pc].x, i), fuel - 1) ||
                         Accepts(p, s, VmThread(p[pc].y, i), fuel - 1))
  {
    reveal Accepts();
  }

  lemma AcceptsJmp(p: Prog, s: seq<char>, pc: int, i: nat, fuel: nat)
    requires 0 <= pc < |p| && p[pc].IJmp?
    ensures Accepts(p, s, VmThread(pc, i), fuel) <==> fuel > 0 && Accepts(p, s, VmThread(p[pc].x, i), fuel - 1)
  {
    reveal Accepts();
  }

  lemma AcceptsMatch(p: Prog, s: seq<char>, pc: int, i: nat, fuel: nat)
    requires 0 <= pc < |p| && p[pc] == IMatch
    ensures Accepts(p, s, VmThread(pc, i), fuel) <==> i == |s|
  {
    reveal Accepts();
  }

  ghost predicate VMAccepts(p: Prog, s: seq<char>)
  {
    exists fuel: nat :: Accepts(p, s, VmThread(0, 0), fuel)
  }

  // ---------------------------------------------------------------------------
  // The emitter: code placed at offset pc, falling through to pc + |code|
  // ---------------------------------------------------------------------------

  function Emit(r: Re, pc: int): seq<Inst>
    decreases r, pc
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

  // ---------------------------------------------------------------------------
  // Correctness
  // ---------------------------------------------------------------------------

  // Where the pieces of emitted code sit.
  lemma LayoutAlt(p: Prog, pc: int, a: Re, b: Re)
    requires CodeAt(p, pc, Emit(Alt(a, b), pc))
    ensures var ca := Emit(a, pc + 1);
            var cb := Emit(b, pc + 2 + |ca|);
            p[pc] == ISplit(pc + 1, pc + 2 + |ca|) && CodeAt(p, pc + 1, ca)
            && p[pc + 1 + |ca|] == IJmp(pc + 2 + |ca| + |cb|) && CodeAt(p, pc + 2 + |ca|, cb)
  {
    // @hole-begin A5.LayoutAlt
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
    // @hole-end A5.LayoutAlt
  }

  lemma LayoutCat(p: Prog, pc: int, a: Re, b: Re)
    requires CodeAt(p, pc, Emit(Cat(a, b), pc))
    ensures var ca := Emit(a, pc);
            CodeAt(p, pc, ca) && CodeAt(p, pc + |ca|, Emit(b, pc + |ca|))
  {
    // @hole-begin A5.LayoutCat
    var code := Emit(Cat(a, b), pc);
    var ca := Emit(a, pc);
    var cb := Emit(b, pc + |ca|);
    forall k | 0 <= k < |ca| ensures p[pc + k] == ca[k] {
      assert code[k] == ca[k];
    }
    forall k | 0 <= k < |cb| ensures p[pc + |ca| + k] == cb[k] {
      assert code[|ca| + k] == cb[k];
    }
    // @hole-end A5.LayoutCat
  }

  lemma LayoutStar(p: Prog, pc: int, a: Re)
    requires CodeAt(p, pc, Emit(Star(a), pc))
    ensures var ca := Emit(a, pc + 1);
            p[pc] == ISplit(pc + 1, pc + 2 + |ca|) && CodeAt(p, pc + 1, ca)
            && p[pc + 1 + |ca|] == IJmp(pc)
  {
    // @hole-begin A5.LayoutStar
    var code := Emit(Star(a), pc);
    var ca := Emit(a, pc + 1);
    assert p[pc] == code[0];
    assert p[pc + 1 + |ca|] == code[1 + |ca|];
    forall k | 0 <= k < |ca| ensures p[pc + 1 + k] == ca[k] {
      assert code[1 + k] == ca[k];
    }
    // @hole-end A5.LayoutStar
  }

  // Soundness, generalized over the continuation at pc + |code|.
  lemma EmitSound(p: Prog, s: seq<char>, r: Re, pc: int, i: nat, fuel: nat)
    returns (j: nat, f: nat)
    requires CodeAt(p, pc, Emit(r, pc)) && i <= |s|
    requires Accepts(p, s, VmThread(pc, i), fuel)
    ensures i <= j <= |s| && f <= fuel && Matches(r, s[i..j])
    ensures Accepts(p, s, VmThread(pc + |Emit(r, pc)|, j), f)
    decreases fuel, r, 1
  {
    // @hole-begin A5.EmitSound
    match r
    case Empty =>
      assert p[pc] == Emit(r, pc)[0];
      AcceptsJmp(p, s, pc, i, fuel);
      j, f := EmitSound(p, s, r, pc, i, fuel - 1);
    case Eps =>
      j, f := i, fuel;
      assert s[i..j] == [];
    case Chr(c) =>
      assert p[pc] == Emit(r, pc)[0];
      AcceptsChar(p, s, pc, i, fuel);
      j, f := i + 1, fuel - 1;
      assert s[i..j] == [c];
    case Alt(a, b) =>
      j, f := SoundAlt(p, s, a, b, pc, i, fuel);
    case Cat(a, b) =>
      j, f := SoundCat(p, s, a, b, pc, i, fuel);
    case Star(a) =>
      j, f := SoundStar(p, s, a, pc, i, fuel);
    // @hole-end A5.EmitSound
  }

  lemma SoundAlt(p: Prog, s: seq<char>, a: Re, b: Re, pc: int, i: nat, fuel: nat)
    returns (j: nat, f: nat)
    requires CodeAt(p, pc, Emit(Alt(a, b), pc)) && i <= |s|
    requires Accepts(p, s, VmThread(pc, i), fuel)
    ensures i <= j <= |s| && f <= fuel && Matches(Alt(a, b), s[i..j])
    ensures Accepts(p, s, VmThread(pc + |Emit(Alt(a, b), pc)|, j), f)
    decreases fuel, Alt(a, b), 0
  {
    // @hole-begin A5.SoundAlt
    LayoutAlt(p, pc, a, b);
    var ca := Emit(a, pc + 1);
    AcceptsSplit(p, s, pc, i, fuel);
    if Accepts(p, s, VmThread(pc + 1, i), fuel - 1) {
      var j1, f1 := EmitSound(p, s, a, pc + 1, i, fuel - 1);
      AcceptsJmp(p, s, pc + 1 + |ca|, j1, f1);
      j, f := j1, f1 - 1;
    } else {
      j, f := EmitSound(p, s, b, pc + 2 + |ca|, i, fuel - 1);
    }
    // @hole-end A5.SoundAlt
  }

  lemma SoundCat(p: Prog, s: seq<char>, a: Re, b: Re, pc: int, i: nat, fuel: nat)
    returns (j: nat, f: nat)
    requires CodeAt(p, pc, Emit(Cat(a, b), pc)) && i <= |s|
    requires Accepts(p, s, VmThread(pc, i), fuel)
    ensures i <= j <= |s| && f <= fuel && Matches(Cat(a, b), s[i..j])
    ensures Accepts(p, s, VmThread(pc + |Emit(Cat(a, b), pc)|, j), f)
    decreases fuel, Cat(a, b), 0
  {
    // @hole-begin A5.SoundCat
    LayoutCat(p, pc, a, b);
    var ca := Emit(a, pc);
    var cb := Emit(b, pc + |ca|);
    assert |Emit(Cat(a, b), pc)| == |ca| + |cb|;
    var j1, f1 := EmitSound(p, s, a, pc, i, fuel);
    j, f := EmitSound(p, s, b, pc + |ca|, j1, f1);
    var w := s[i..j];
    assert w[..j1 - i] == s[i..j1];
    assert w[j1 - i..] == s[j1..j];
    assert Matches(a, w[..j1 - i]) && Matches(b, w[j1 - i..]);
    // @hole-end A5.SoundCat
  }

  lemma SoundStar(p: Prog, s: seq<char>, a: Re, pc: int, i: nat, fuel: nat)
    returns (j: nat, f: nat)
    requires CodeAt(p, pc, Emit(Star(a), pc)) && i <= |s|
    requires Accepts(p, s, VmThread(pc, i), fuel)
    ensures i <= j <= |s| && f <= fuel && Matches(Star(a), s[i..j])
    ensures Accepts(p, s, VmThread(pc + |Emit(Star(a), pc)|, j), f)
    decreases fuel, Star(a), 0
  {
    // @hole-begin A5.SoundStar
    LayoutStar(p, pc, a);
    var ca := Emit(a, pc + 1);
    AcceptsSplit(p, s, pc, i, fuel);
    if Accepts(p, s, VmThread(pc + 1, i), fuel - 1) {
      var j1, f1 := EmitSound(p, s, a, pc + 1, i, fuel - 1);
      AcceptsJmp(p, s, pc + 1 + |ca|, j1, f1);
      j, f := EmitSound(p, s, Star(a), pc, j1, f1 - 1);
      if j1 > i {
        assert s[i..j][..j1 - i] == s[i..j1];
        assert s[i..j][j1 - i..] == s[j1..j];
      } else {
        assert s[i..j] == s[j1..j];
      }
    } else {
      j, f := i, fuel - 1;
    }
    // @hole-end A5.SoundStar
  }

  // Completeness, generalized over the continuation at pc + |code|.
  lemma EmitComplete(p: Prog, s: seq<char>, r: Re, pc: int, i: nat, j: nat, f: nat)
    returns (f2: nat)
    requires CodeAt(p, pc, Emit(r, pc)) && i <= j <= |s|
    requires Matches(r, s[i..j]) && Accepts(p, s, VmThread(pc + |Emit(r, pc)|, j), f)
    ensures Accepts(p, s, VmThread(pc, i), f2)
    decreases r, j - i, 1
  {
    // @hole-begin A5.EmitComplete
    match r
    case Empty =>
    case Eps =>
      f2 := f;
    case Chr(c) =>
      assert p[pc] == Emit(r, pc)[0];
      assert s[i] == s[i..j][0];
      f2 := f + 1;
      AcceptsChar(p, s, pc, i, f2);
    case Alt(a, b) =>
      f2 := CompleteAlt(p, s, a, b, pc, i, j, f);
    case Cat(a, b) =>
      f2 := CompleteCat(p, s, a, b, pc, i, j, f);
    case Star(a) =>
      f2 := CompleteStar(p, s, a, pc, i, j, f);
    // @hole-end A5.EmitComplete
  }

  lemma CompleteAlt(p: Prog, s: seq<char>, a: Re, b: Re, pc: int, i: nat, j: nat, f: nat)
    returns (f2: nat)
    requires CodeAt(p, pc, Emit(Alt(a, b), pc)) && i <= j <= |s|
    requires Matches(Alt(a, b), s[i..j]) && Accepts(p, s, VmThread(pc + |Emit(Alt(a, b), pc)|, j), f)
    ensures Accepts(p, s, VmThread(pc, i), f2)
    decreases Alt(a, b), j - i, 0
  {
    // @hole-begin A5.CompleteAlt
    LayoutAlt(p, pc, a, b);
    var ca := Emit(a, pc + 1);
    var f1;
    if Matches(a, s[i..j]) {
      AcceptsJmp(p, s, pc + 1 + |ca|, j, f + 1);
      f1 := EmitComplete(p, s, a, pc + 1, i, j, f + 1);
    } else {
      f1 := EmitComplete(p, s, b, pc + 2 + |ca|, i, j, f);
    }
    f2 := f1 + 1;
    AcceptsSplit(p, s, pc, i, f2);
    // @hole-end A5.CompleteAlt
  }

  lemma CompleteCat(p: Prog, s: seq<char>, a: Re, b: Re, pc: int, i: nat, j: nat, f: nat)
    returns (f2: nat)
    requires CodeAt(p, pc, Emit(Cat(a, b), pc)) && i <= j <= |s|
    requires Matches(Cat(a, b), s[i..j]) && Accepts(p, s, VmThread(pc + |Emit(Cat(a, b), pc)|, j), f)
    ensures Accepts(p, s, VmThread(pc, i), f2)
    decreases Cat(a, b), j - i, 0
  {
    // @hole-begin A5.CompleteCat
    LayoutCat(p, pc, a, b);
    var w := s[i..j];
    var k :| 0 <= k <= |w| && Matches(a, w[..k]) && Matches(b, w[k..]);
    assert w[..k] == s[i..i + k] && w[k..] == s[i + k..j];
    var f1 := EmitComplete(p, s, b, pc + |Emit(a, pc)|, i + k, j, f);
    f2 := EmitComplete(p, s, a, pc, i, i + k, f1);
    // @hole-end A5.CompleteCat
  }

  lemma CompleteStar(p: Prog, s: seq<char>, a: Re, pc: int, i: nat, j: nat, f: nat)
    returns (f2: nat)
    requires CodeAt(p, pc, Emit(Star(a), pc)) && i <= j <= |s|
    requires Matches(Star(a), s[i..j]) && Accepts(p, s, VmThread(pc + |Emit(Star(a), pc)|, j), f)
    ensures Accepts(p, s, VmThread(pc, i), f2)
    decreases Star(a), j - i, 0
  {
    // @hole-begin A5.CompleteStar
    LayoutStar(p, pc, a);
    var ca := Emit(a, pc + 1);
    var w := s[i..j];
    if w == [] {
      f2 := f + 1;
    } else {
      var k :| 0 < k <= |w| && Matches(a, w[..k]) && Matches(Star(a), w[k..]);
      assert w[..k] == s[i..i + k] && w[k..] == s[i + k..j];
      var f1 := EmitComplete(p, s, Star(a), pc, i + k, j, f);
      AcceptsJmp(p, s, pc + 1 + |ca|, i + k, f1 + 1);
      var f3 := EmitComplete(p, s, a, pc + 1, i, i + k, f1 + 1);
      f2 := f3 + 1;
    }
    AcceptsSplit(p, s, pc, i, f2);
    // @hole-end A5.CompleteStar
  }

  // The capstone statement: the emitted program accepts exactly the language.
  lemma EmitCorrect(r: Re, s: seq<char>)
    ensures VMAccepts(EmitProg(r), s) <==> Matches(r, s)
  {
    // @hole-begin A5.EmitCorrect
    var p := EmitProg(r);
    var code := Emit(r, 0);
    assert CodeAt(p, 0, code) by {
      forall k | 0 <= k < |code| ensures p[k] == code[k] {
      }
    }
    assert p[|code|] == IMatch;
    assert s[0..|s|] == s;
    if VMAccepts(p, s) {
      var fuel: nat :| Accepts(p, s, VmThread(0, 0), fuel);
      var j, f := EmitSound(p, s, r, 0, 0, fuel);
      AcceptsMatch(p, s, |code|, j, f);
    }
    if Matches(r, s) {
      AcceptsMatch(p, s, |code|, |s|, 0);
      var f2 := EmitComplete(p, s, r, 0, 0, |s|, 0);
      assert Accepts(p, s, VmThread(0, 0), f2);
    }
    // @hole-end A5.EmitCorrect
  }
}
