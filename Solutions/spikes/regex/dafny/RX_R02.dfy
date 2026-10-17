// DVR0 reference (author-only): R02's structural holes over layer A1 (PLAN §6.2,
// R02.H2d, R02.H3d). Module references, never layer code.
module RX_R02 {
  import opened RG_A1_Re

  lemma {:induction false} NodeCountBackwards(r: Re)
    ensures NodeCount(r) >= 1 && NodeCount(Backwards(r)) == NodeCount(r)
    decreases r
  {
    // @hole-begin R02.NodeCountBackwards
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      NodeCountBackwards(a);
      NodeCountBackwards(b);
    case Cat(a, b) =>
      NodeCountBackwards(a);
      NodeCountBackwards(b);
    case Star(a) =>
      NodeCountBackwards(a);
    // @hole-end R02.NodeCountBackwards
  }

  lemma {:induction false} NullableBackwards(r: Re)
    ensures Nullable(Backwards(r)) == Nullable(r)
    decreases r
  {
    // @hole-begin R02.NullableBackwards
    match r
    case Empty =>
    case Eps =>
    case Chr(_) =>
    case Alt(a, b) =>
      NullableBackwards(a);
      NullableBackwards(b);
    case Cat(a, b) =>
      NullableBackwards(a);
      NullableBackwards(b);
    case Star(a) =>
      NullableBackwards(a);
    // @hole-end R02.NullableBackwards
  }
}
