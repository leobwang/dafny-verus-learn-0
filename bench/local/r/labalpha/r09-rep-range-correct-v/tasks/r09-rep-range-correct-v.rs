// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["lemma_copies_optional_r09"]},{"name":"c2","kind":"calls","callees":["lemma_copies_join_r09"]},{"name":"h1"},{"name":"c3","kind":"calls","callees":["lemma_copies_join_r09"]},{"name":"c4","kind":"calls","callees":["lemma_copies_optional_r09"]},{"name":"h2"}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_repetition_interval_r09","start":202,"end":221}]
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

pub open spec fn matches(r: Re, s: Seq<char>) -> bool
    decreases r, s.len(),
{
    match r {
        Re::Empty => false,
        Re::Eps => s.len() == 0,
        Re::Chr(c) => s.len() == 1 && s[0] == c,
        Re::Alt(a, b) => matches(*a, s) || matches(*b, s),
        Re::Cat(a, b) => exists|i: int|
            0 <= i <= s.len() && matches(*a, #[trigger] s.subrange(0, i)) && matches(
                *b,
                s.subrange(i, s.len() as int),
            ),
        Re::Star(a) => s.len() == 0 || exists|i: int|
            1 <= i <= s.len() && matches(*a, #[trigger] s.subrange(0, i)) && matches(
                r,
                s.subrange(i, s.len() as int),
            ),
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

// Provided fact (rg_re_a1b::lemma_cat_eps_left), complete.
pub proof fn lemma_cat_eps_left(r: Re, s: Seq<char>)
    ensures
        matches(Re::Cat(Box::new(Re::Eps), Box::new(r)), s) <==> matches(r, s),
{
    let e = Re::Cat(Box::new(Re::Eps), Box::new(r));
    assert(s.subrange(0, s.len() as int) =~= s);
    if matches(r, s) {
        assert(s.subrange(0, 0) =~= Seq::<char>::empty());
        assert(matches(Re::Eps, s.subrange(0, 0)));
    }
    if matches(e, s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(Re::Eps, #[trigger] s.subrange(0, i)) && matches(
                r,
                s.subrange(i, s.len() as int),
            );
        assert(s.subrange(0, i).len() == 0);
    }
}

// Provided fact (rg_re_a1b::lemma_cat_assoc), complete.
pub proof fn lemma_cat_assoc(a: Re, b: Re, c: Re, s: Seq<char>)
    ensures
        matches(Re::Cat(Box::new(Re::Cat(Box::new(a), Box::new(b))), Box::new(c)), s)
            <==> matches(Re::Cat(Box::new(a), Box::new(Re::Cat(Box::new(b), Box::new(c)))), s),
{
    let ab = Re::Cat(Box::new(a), Box::new(b));
    let bc = Re::Cat(Box::new(b), Box::new(c));
    if matches(Re::Cat(Box::new(ab), Box::new(c)), s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(ab, #[trigger] s.subrange(0, i)) && matches(
                c,
                s.subrange(i, s.len() as int),
            );
        let u = s.subrange(0, i);
        let k = choose|k: int|
            0 <= k <= u.len() && matches(a, #[trigger] u.subrange(0, k)) && matches(
                b,
                u.subrange(k, u.len() as int),
            );
        let v = s.subrange(k, s.len() as int);
        assert(u.subrange(0, k) =~= s.subrange(0, k));
        assert(u.subrange(k, u.len() as int) =~= v.subrange(0, i - k));
        assert(v.subrange(i - k, v.len() as int) =~= s.subrange(i, s.len() as int));
        assert(matches(bc, v));
    }
    if matches(Re::Cat(Box::new(a), Box::new(bc)), s) {
        let k = choose|k: int|
            0 <= k <= s.len() && matches(a, #[trigger] s.subrange(0, k)) && matches(
                bc,
                s.subrange(k, s.len() as int),
            );
        let v = s.subrange(k, s.len() as int);
        let j = choose|j: int|
            0 <= j <= v.len() && matches(b, #[trigger] v.subrange(0, j)) && matches(
                c,
                v.subrange(j, v.len() as int),
            );
        let u = s.subrange(0, k + j);
        assert(u.subrange(0, k) =~= s.subrange(0, k));
        assert(u.subrange(k, u.len() as int) =~= v.subrange(0, j));
        assert(v.subrange(j, v.len() as int) =~= s.subrange(k + j, s.len() as int));
        assert(matches(ab, u));
    }
}

// Provided fact (R09 reference helper lemma_cat_right_context_r09), complete.
proof fn lemma_cat_right_context_r09(a:Re,b:Re,c:Re,s:Seq<char>)
 requires forall|t:Seq<char>| matches(b,t)==matches(c,t),
 ensures matches(Re::Cat(Box::new(a),Box::new(b)),s)==matches(Re::Cat(Box::new(a),Box::new(c)),s),
{
 if matches(Re::Cat(Box::new(a),Box::new(b)),s) {
  let i=choose|i:int| 0<=i<=s.len() && matches(a,#[trigger] s.subrange(0,i)) && matches(b,s.subrange(i,s.len() as int));
  assert(matches(c,s.subrange(i,s.len() as int)));
 }
 if matches(Re::Cat(Box::new(a),Box::new(c)),s) {
  let i=choose|i:int| 0<=i<=s.len() && matches(a,#[trigger] s.subrange(0,i)) && matches(c,s.subrange(i,s.len() as int));
  assert(matches(b,s.subrange(i,s.len() as int)));
 }
}

// Provided fact (R09 reference lemma_copies_join_r09), complete.
proof fn lemma_copies_join_r09(r:Re,a:nat,b:nat,s:Seq<char>)
 ensures matches(copies(r,a+b),s)==matches(Re::Cat(Box::new(copies(r,a)),Box::new(copies(r,b))),s),
 decreases a,
{
 if a==0 {lemma_cat_eps_left(copies(r,b),s);}
 else {
  let aa=(a-1) as nat;
  lemma_cat_assoc(r,copies(r,aa),copies(r,b),s);
  let x=copies(r,aa+b);let y=Re::Cat(Box::new(copies(r,aa)),Box::new(copies(r,b)));
  assert forall|t:Seq<char>| matches(x,t)==matches(y,t) by {lemma_copies_join_r09(r,aa,b,t);}
  lemma_cat_right_context_r09(r,x,y,s);
 }
}

// Provided fact (R09 reference lemma_copies_optional_r09), complete.
proof fn lemma_copies_optional_r09(r:Re,j:nat,s:Seq<char>)
 ensures matches(copies_up_to(r,j),s)==(exists|k:nat| k<=j && #[trigger] matches(copies(r,k),s)),
 decreases j,
{
 if j>0 {
  let jm=(j-1) as nat;let u=copies_up_to(r,jm);
  if matches(copies_up_to(r,j),s) {
   if s.len()!=0 {
    assert(!matches(Re::Eps,s));
    assert(matches(Re::Cat(Box::new(r),Box::new(u)),s));
    let i=choose|i:int| 0<=i<=s.len() && matches(r,#[trigger] s.subrange(0,i)) && matches(u,s.subrange(i,s.len() as int));
    lemma_copies_optional_r09(r,jm,s.subrange(i,s.len() as int));
    let k=choose|k:nat| k<=jm && #[trigger] matches(copies(r,k),s.subrange(i,s.len() as int));
    assert(copies(r,k+1)==Re::Cat(Box::new(r),Box::new(copies(r,k))));
    assert(matches(copies(r,k+1),s));
   } else {assert(matches(copies(r,0),s));}
  }
  if exists|k:nat| k<=j && #[trigger] matches(copies(r,k),s) {
   let k=choose|k:nat| k<=j && #[trigger] matches(copies(r,k),s);
   if k>0 {
    let km=(k-1) as nat;
    assert(copies(r,k)==Re::Cat(Box::new(r),Box::new(copies(r,km))));
    let i=choose|i:int| 0<=i<=s.len() && matches(r,#[trigger] s.subrange(0,i)) && matches(copies(r,km),s.subrange(i,s.len() as int));
    lemma_copies_optional_r09(r,jm,s.subrange(i,s.len() as int));
    assert(exists|kk:nat| kk<=jm && #[trigger] matches(copies(r,kk),s.subrange(i,s.len() as int)));
    assert(matches(Re::Cat(Box::new(r),Box::new(u)),s));
   } else {assert(copies(r,0)==Re::Eps);}
   assert(matches(copies_up_to(r,j),s));
  }
 } else {
  assert(copies(r,0)==Re::Eps);
  if exists|k:nat| k<=j && #[trigger] matches(copies(r,k),s) {
   let k=choose|k:nat| k<=j && #[trigger] matches(copies(r,k),s);assert(k==0);
  }
 }
}

// The task (R09.H4 repetition interval): rep_range(r, n, m) matches exactly n..m copies.
proof fn lemma_repetition_interval_r09(r:Re,n:nat,m:nat,s:Seq<char>)
 requires n<=m,
 ensures matches(rep_range(r,n,m),s)==(exists|k:nat| n<=k<=m && #[trigger] matches(copies(r,k),s)),
{
 let extra=(m-n) as nat;
 if matches(rep_range(r,n,m),s) {
  let i=choose|i:int| 0<=i<=s.len() && matches(copies(r,n),#[trigger] s.subrange(0,i)) && matches(copies_up_to(r,extra),s.subrange(i,s.len() as int));
  /*R12_CALLS:c1*/
  let k=choose|k:nat| k<=extra && #[trigger] matches(copies(r,k),s.subrange(i,s.len() as int));
  /*R12_CALLS:c2*/
  assert(/*R12_HINT:h1*/ true);
 }
 if exists|k:nat| n<=k<=m && #[trigger] matches(copies(r,k),s) {
  let k=choose|k:nat| n<=k<=m && #[trigger] matches(copies(r,k),s);
  /*R12_CALLS:c3*/
  let i=choose|i:int| 0<=i<=s.len() && matches(copies(r,n),#[trigger] s.subrange(0,i)) && matches(copies(r,(k-n) as nat),s.subrange(i,s.len() as int));
  /*R12_CALLS:c4*/
  assert(/*R12_HINT:h2*/ true);
 }
}

} // verus!
