// Cheat-corpus fixture C-09 (Dafny): healthy control. Invented program.
module CorpusC09 {
  datatype Tree = Leaf | Node(left: Tree, value: int, right: Tree)

  function Size(t: Tree): nat {
    match t
    case Leaf => 0
    case Node(l, _, r) => Size(l) + 1 + Size(r)
  }

  function Mirror(t: Tree): Tree {
    match t
    case Leaf => Leaf
    case Node(l, v, r) => Node(Mirror(r), v, Mirror(l))
  }

  lemma MirrorSize(t: Tree)
    ensures Size(Mirror(t)) == Size(t)
  {
    match t
    case Leaf =>
    case Node(l, _, r) =>
      MirrorSize(l);
      MirrorSize(r);
  }

  @Test
  method MirrorCases() {
    var t := Node(Node(Leaf, 1, Leaf), 2, Leaf);
    expect Size(Mirror(t)) == 2;
    expect Mirror(Mirror(t)) == t;
  }
}
