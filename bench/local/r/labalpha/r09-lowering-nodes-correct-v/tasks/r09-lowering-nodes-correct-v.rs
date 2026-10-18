// R12_HINT_SITES: [{"name":"c1","identifiers":["cc","ranges_spec"],"kind":"calls","callees":["lemma_class_nodes_r09"]},{"name":"c2","identifiers":["a","b","len"],"kind":"calls","callees":["lemma_lowering_nodes_r09"]},{"name":"c3","identifiers":["a","len"],"kind":"calls","callees":["lemma_lowering_nodes_r09"]},{"name":"c4","identifiers":["a","len","n","m","lower","as","nat"],"kind":"calls","callees":["lemma_lowering_nodes_r09","lemma_copies_nodes_r09","lemma_optional_nodes_r09"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_lowering_nodes_r09","start":278,"end":299}]
use vstd::prelude::*;

verus! {

// Provided definitions: rg_re_a1 (layer A1), copied verbatim.
pub enum Re {
    Empty,
    Eps,
    Chr(char),
    Alt(Box<Re>, Box<Re>),
    Cat(Box<Re>, Box<Re>),
    Star(Box<Re>),
}

/// The number of nodes of `r`.
pub open spec fn node_count(r: Re) -> nat
    decreases r,
{
    match r {
        Re::Empty => 1,
        Re::Eps => 1,
        Re::Chr(_) => 1,
        Re::Alt(a, b) => 1 + node_count(*a) + node_count(*b),
        Re::Cat(a, b) => 1 + node_count(*a) + node_count(*b),
        Re::Star(a) => 1 + node_count(*a),
    }
}

// Provided definitions: rg_re_a3 (layer A3), counted repetition, copied verbatim.
pub open spec fn copies(r: Re, k: nat) -> Re
    decreases k,
{
    if k == 0 {
        Re::Eps
    } else {
        Re::Cat(Box::new(r), Box::new(copies(r, (k - 1) as nat)))
    }
}

pub open spec fn copies_up_to(r: Re, k: nat) -> Re
    decreases k,
{
    if k == 0 {
        Re::Eps
    } else {
        Re::Alt(Box::new(Re::Eps), Box::new(Re::Cat(Box::new(r), Box::new(copies_up_to(r, (k - 1) as nat)))))
    }
}

pub open spec fn rep_range(r: Re, n: nat, m: nat) -> Re {
    Re::Cat(Box::new(copies(r, n)), Box::new(copies_up_to(r, (m - n) as nat)))
}

// Provided definitions: rg_re_a2::char_class (layer A2), the class representation, copied verbatim.
/// Non-empty ranges, sorted and separated by at least one code.
pub open spec fn separated(rs: Seq<(u32, u32)>) -> bool {
    &&& forall|i: int| 0 <= i < rs.len() ==> (#[trigger] rs[i]).0 <= rs[i].1
    &&& forall|i: int, j: int| 0 <= i < j < rs.len() ==> (#[trigger] rs[i]).1 + 1 < (#[trigger] rs[j]).0
}

pub struct CharClass {
    ranges: Vec<(u32, u32)>,
}

impl CharClass {
    pub closed spec fn valid(&self) -> bool {
        separated(self.ranges@)
    }

    /// The range listing (the accessor's model).
    pub closed spec fn ranges_spec(&self) -> Seq<(u32, u32)> {
        self.ranges@
    }
}

pub const CLASS_MAX: u32 = 0xd800;

// Provided definitions: rg_re_a3 (layer A3), classes as regexes, copied verbatim.
/// A range that lowers: non-empty and below CLASS_MAX.
pub open spec fn range_valid(lo: u32, hi: u32) -> bool {
    lo <= hi && hi < CLASS_MAX
}

/// A range listing that lowers.
pub open spec fn class_valid(xs: Seq<(u32, u32)>) -> bool {
    forall|i: int| 0 <= i < xs.len() ==> range_valid(xs[i].0, xs[i].1)
}

/// The one place a code becomes a char (spec only): `lo < CLASS_MAX`, so it is a char's code.
pub open spec fn range_re(lo: u32, hi: u32) -> Re
    decreases hi - lo,
{
    if !range_valid(lo, hi) {
        Re::Empty
    } else if lo == hi {
        Re::Chr(lo as char)
    } else {
        Re::Alt(Box::new(Re::Chr(lo as char)), Box::new(range_re((lo + 1) as u32, hi)))
    }
}

pub open spec fn class_re(xs: Seq<(u32, u32)>) -> Re
    decreases xs.len(),
{
    if xs.len() == 0 {
        Re::Empty
    } else {
        Re::Alt(Box::new(range_re(xs[0].0, xs[0].1)), Box::new(class_re(xs.drop_first())))
    }
}

// Provided definitions: R09's size model, copied verbatim.
pub open spec fn range_nodes_r09(lo: u32, hi: u32) -> nat {
    if range_valid(lo, hi) {
        (2 * ((hi as int) - (lo as int)) + 1) as nat
    } else {
        1
    }
}
pub open spec fn class_nodes_r09(xs: Seq<(u32, u32)>) -> nat
    decreases xs.len(),
{
    if xs.len() == 0 {
        1
    } else {
        1 + range_nodes_r09(xs[0].0, xs[0].1) + class_nodes_r09(xs.drop_first())
    }
}

// Provided definitions: rg_re_a3 (layer A3), positioned syntax and lowering, copied verbatim.
pub const MAX_BOUND: u32 = 9;

pub struct Span {
    pub lo: usize,
    pub hi: usize,
}

pub struct Syn {
    pub node: SyntaxKind,
    pub span: Span,
}

pub enum SyntaxKind {
    Eps,
    Chr(char),
    Class(CharClass),
    Alt(Box<Syn>, Box<Syn>),
    Cat(Box<Syn>, Box<Syn>),
    Star(Box<Syn>),
    Plus(Box<Syn>),
    Opt(Box<Syn>),
    RepRange(Box<Syn>, u32, u32),
    Group(Box<Syn>),
}

pub open spec fn wf(t: Syn, len: nat) -> bool
    decreases t,
{
    &&& t.span.lo <= t.span.hi <= len
    &&& match t.node {
        SyntaxKind::Eps => t.span.lo == t.span.hi,
        SyntaxKind::Chr(_) => t.span.lo < t.span.hi,
        SyntaxKind::Class(xs) => t.span.lo < t.span.hi && xs.valid() && class_valid(xs.ranges_spec()),
        SyntaxKind::Alt(a, b) => wf(*a, len) && wf(*b, len) && a.span.lo == t.span.lo && a.span.hi < b.span.lo
            && b.span.hi == t.span.hi,
        SyntaxKind::Cat(a, b) => wf(*a, len) && wf(*b, len) && a.span.lo == t.span.lo && a.span.hi == b.span.lo
            && b.span.hi == t.span.hi,
        SyntaxKind::Star(a) | SyntaxKind::Plus(a) | SyntaxKind::Opt(a) => wf(*a, len) && a.span.lo == t.span.lo
            && a.span.hi < t.span.hi,
        SyntaxKind::RepRange(a, n, m) => wf(*a, len) && a.span.lo == t.span.lo && a.span.hi < t.span.hi && n <= m
            <= MAX_BOUND,
        SyntaxKind::Group(a) => wf(*a, len) && t.span.lo < a.span.lo && a.span.hi < t.span.hi,
    }
}

pub open spec fn lower(t: Syn) -> Re
    decreases t,
{
    match t.node {
        SyntaxKind::Eps => Re::Eps,
        SyntaxKind::Chr(c) => Re::Chr(c),
        SyntaxKind::Class(xs) => class_re(xs.ranges_spec()),
        SyntaxKind::Alt(a, b) => Re::Alt(Box::new(lower(*a)), Box::new(lower(*b))),
        SyntaxKind::Cat(a, b) => Re::Cat(Box::new(lower(*a)), Box::new(lower(*b))),
        SyntaxKind::Star(a) => Re::Star(Box::new(lower(*a))),
        SyntaxKind::Plus(a) => Re::Cat(Box::new(lower(*a)), Box::new(Re::Star(Box::new(lower(*a))))),
        SyntaxKind::Opt(a) => Re::Alt(Box::new(Re::Eps), Box::new(lower(*a))),
        SyntaxKind::RepRange(a, n, m) => rep_range(lower(*a), n as nat, m as nat),
        SyntaxKind::Group(a) => lower(*a),
    }
}

pub open spec fn lowering_nodes_r09(t:Syn)->nat
 decreases t,
{
 match t.node {
  SyntaxKind::Eps | SyntaxKind::Chr(_) => 1,
  SyntaxKind::Class(cc) => class_nodes_r09(cc.ranges_spec()),
  SyntaxKind::Alt(a,b) | SyntaxKind::Cat(a,b) => 1+lowering_nodes_r09(*a)+lowering_nodes_r09(*b),
  SyntaxKind::Star(a) => 1+lowering_nodes_r09(*a),
  SyntaxKind::Plus(a) => 2+2*lowering_nodes_r09(*a),
  SyntaxKind::Opt(a) => 2+lowering_nodes_r09(*a),
  SyntaxKind::Group(a) => lowering_nodes_r09(*a),
  SyntaxKind::RepRange(a,n,m) => 3+(n as nat)*(lowering_nodes_r09(*a)+1)+((m as nat-n as nat) as nat)*(lowering_nodes_r09(*a)+3),
 }
}

// Provided fact (R09 reference lemma_range_nodes_r09), complete.
proof fn lemma_range_nodes_r09(lo: u32, hi: u32)
    requires
        range_valid(lo, hi),
    ensures
        node_count(range_re(lo, hi)) == range_nodes_r09(lo, hi),
    decreases hi - lo,
{
    reveal_with_fuel(node_count, 2);
    if lo < hi {
        lemma_range_nodes_r09((lo + 1) as u32, hi);
    }
}

// Provided facts (R09 reference lemma_copies_nodes_r09, lemma_optional_nodes_r09, lemma_class_nodes_r09), complete.
proof fn lemma_copies_nodes_r09(r:Re,k:nat)
 ensures node_count(copies(r,k))==1+k*(node_count(r)+1),
 decreases k,
{
 reveal_with_fuel(node_count,2);
 reveal_with_fuel(copies,2);
 let b=node_count(r) as int;
 if k>0 {
  let km=(k-1) as nat;
  lemma_copies_nodes_r09(r,km);
  let total=node_count(copies(r,k)) as int;
  let child=node_count(copies(r,km)) as int;
  assert(total==1+b+child);
  assert(total==1+k*(b+1)) by (nonlinear_arith)
   requires total==1+b+child,child==1+km*(b+1),k==km+1;
 } else {
  assert(1+k*(b+1)==1) by (nonlinear_arith) requires k==0;
 }
}
proof fn lemma_optional_nodes_r09(r:Re,k:nat)
 ensures node_count(copies_up_to(r,k))==1+k*(node_count(r)+3),
 decreases k,
{
 reveal_with_fuel(node_count,3);
 reveal_with_fuel(copies_up_to,2);
 let b=node_count(r) as int;
 if k>0 {
  let km=(k-1) as nat;
  lemma_optional_nodes_r09(r,km);
  let total=node_count(copies_up_to(r,k)) as int;
  let child=node_count(copies_up_to(r,km)) as int;
  assert(total==3+b+child);
  assert(total==1+k*(b+3)) by (nonlinear_arith)
   requires total==3+b+child,child==1+km*(b+3),k==km+1;
 } else {
  assert(1+k*(b+3)==1) by (nonlinear_arith) requires k==0;
 }
}
proof fn lemma_class_nodes_r09(xs: Seq<(u32, u32)>)
 requires class_valid(xs),
 ensures node_count(class_re(xs))==class_nodes_r09(xs),
 decreases xs.len(),
{
 if xs.len()>0 {
  assert forall|i:int| 0<=i<xs.drop_first().len() implies range_valid(xs.drop_first()[i].0,xs.drop_first()[i].1) by {
   assert(xs.drop_first()[i]==xs[i+1]);
  }
  lemma_range_nodes_r09(xs[0].0,xs[0].1);
  lemma_class_nodes_r09(xs.drop_first());
 }
}

// The task (R09 lowering nodes): the logical size model counts the lowered regex.
pub proof fn lemma_lowering_nodes_r09(t:Syn,len:nat)
 requires wf(t,len),
 ensures node_count(lower(t))==lowering_nodes_r09(t),
 decreases t,
{
 reveal_with_fuel(node_count,3);
 match t.node {
  SyntaxKind::Eps | SyntaxKind::Chr(_) => {},
  SyntaxKind::Class(cc) => {
   /*R12_CALLS:c1*/
  },
  SyntaxKind::Alt(a,b) | SyntaxKind::Cat(a,b) => {
   /*R12_CALLS:c2*/
  },
  SyntaxKind::Star(a) | SyntaxKind::Plus(a) | SyntaxKind::Opt(a) | SyntaxKind::Group(a) => {
   /*R12_CALLS:c3*/
  },
  SyntaxKind::RepRange(a,n,m) => {
   /*R12_CALLS:c4*/
  },
 }
}

} // verus!
