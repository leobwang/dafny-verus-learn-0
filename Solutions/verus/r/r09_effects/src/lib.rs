// Reference Solution.
/* R09 — Effects. Frozen A1/A1b/A2/A3; finite scalar-position parser.
Six holes per language: T1 cursor read, H1 counted suffix, H2 class body,
H3 bounded expansion cost, H4 repetition interval proof, H5 cursor update.
Complete infrastructure checks the logical tree-node cap before allocating
expanded regexes. Positions count Unicode scalars, classes are below0xD800,
finite counts are one character. Zero copies skip an unused oversized child.
Native proofs and finite compiled differential checks are separate evidence.
Live Claude/calibration remains recorded D45 debt, never a pass.
*/
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a3::*;
verus! {
// Existing guarantees only: these predicates do not define the full grammar.
pub open spec fn original_contract_r09(s:Seq<char>,r:Result<Syn,PErr>)->bool {
 &&& match r {Ok(t)=>wf(t,s.len()) && t.span.lo==0 && t.span.hi==s.len(),Err(e)=>e.pos<=s.len()}
 &&& no_special_from(s,0) ==> r is Ok && matches(lower(r->Ok_0),s) && lowering_nodes_r09(r->Ok_0)==(if s.len()==0 {1int} else {2*s.len()-1})
}
pub open spec fn transcribed_mirror_r09(s:Seq<char>,r:Result<Syn,PErr>)->bool {
 match r {
  Err(e)=>e.pos<=s.len() && !no_special_from(s,0),
  Ok(t)=>wf(t,s.len()) && t.span.lo==0 && t.span.hi==s.len() &&
   (no_special_from(s,0) ==> matches(lower(t),s) && lowering_nodes_r09(t)==(if s.len()==0 {1int} else {2*s.len()-1})),
 }
}
// Both implications are relative to this mirror, not to independent intent.
proof fn both_mirror_implications_r09(s:Seq<char>,r:Result<Syn,PErr>)
 ensures original_contract_r09(s,r) ==> transcribed_mirror_r09(s,r),
 transcribed_mirror_r09(s,r) ==> original_contract_r09(s,r),
 {match r {Ok(_)=>{},Err(_)=>{}}}
fn parse_relative_mirror_r09(s:&Vec<char>)->(r:Result<Syn,PErr>)
 ensures original_contract_r09(s@,r) && transcribed_mirror_r09(s@,r),
 {
 let r=parse(s);
 proof {both_mirror_implications_r09(s@,r);}
 r
 }
}

verus! {
pub open spec fn range_nodes_r09(lo:char,hi:char)->nat {
 if range_valid(lo,hi) { (2*((hi as int)-(lo as int))+1) as nat } else {1}
}
pub open spec fn class_nodes_r09(xs:Seq<(char,char)>)->nat
 decreases xs.len(),
{
 if xs.len()==0 {1} else {1+range_nodes_r09(xs[0].0,xs[0].1)+class_nodes_r09(xs.drop_first())}
}
pub open spec fn lowering_nodes_r09(t:Syn)->nat
 decreases t,
{
 match t.node {
  SyntaxKind::Eps | SyntaxKind::Chr(_) => 1,
  SyntaxKind::Class(cc) => class_nodes_r09(cc.ranges@),
  SyntaxKind::Alt(a,b) | SyntaxKind::Cat(a,b) => 1+lowering_nodes_r09(*a)+lowering_nodes_r09(*b),
  SyntaxKind::Star(a) => 1+lowering_nodes_r09(*a),
  SyntaxKind::Plus(a) => 2+2*lowering_nodes_r09(*a),
  SyntaxKind::Opt(a) => 2+lowering_nodes_r09(*a),
  SyntaxKind::Group(a) => lowering_nodes_r09(*a),
  SyntaxKind::RepRange(a,n,m) => 3+(n as nat)*(lowering_nodes_r09(*a)+1)+((m as nat-n as nat) as nat)*(lowering_nodes_r09(*a)+3),
 }
}
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
proof fn lemma_range_nodes_r09(lo:char,hi:char)
 requires range_valid(lo,hi),
 ensures node_count(range_re(lo,hi))==range_nodes_r09(lo,hi),
 decreases (hi as int)-(lo as int),
{
 reveal_with_fuel(node_count,2);
 if lo<hi {
  let next=((lo as u32)+1) as char;
  assert((next as u32)==(lo as u32)+1);
  lemma_range_nodes_r09(next,hi);
 }
}
proof fn lemma_class_nodes_r09(xs:Seq<(char,char)>)
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
pub proof fn lemma_lowering_nodes_r09(t:Syn,len:nat)
 requires wf(t,len),
 ensures node_count(lower(t))==lowering_nodes_r09(t),
 decreases t,
{
 reveal_with_fuel(node_count,3);
 match t.node {
  SyntaxKind::Eps | SyntaxKind::Chr(_) => {},
  SyntaxKind::Class(cc) => {lemma_class_nodes_r09(cc.ranges@);},
  SyntaxKind::Alt(a,b) | SyntaxKind::Cat(a,b) => {lemma_lowering_nodes_r09(*a,len);lemma_lowering_nodes_r09(*b,len);},
  SyntaxKind::Star(a) | SyntaxKind::Plus(a) | SyntaxKind::Opt(a) | SyntaxKind::Group(a) => {lemma_lowering_nodes_r09(*a,len);},
  SyntaxKind::RepRange(a,n,m) => {
   lemma_lowering_nodes_r09(*a,len);
   lemma_copies_nodes_r09(lower(*a),n as nat);
   lemma_optional_nodes_r09(lower(*a),(m as nat-n as nat) as nat);
  },
 }
}
}
// Private parser port over positioned A3. Safety/completion contracts are
// distinct from the independently exercised grammar fidelity oracle.
use rg_re_a2::*;
verus! {
pub open spec fn no_special_from(s:Seq<char>,i:int)->bool {
 forall|k:int| i<=k<s.len() ==> !is_meta(s[k])
}
pub proof fn lemma_literal_append_r09(a:Re,u:Seq<char>,c:char)
 requires matches(a,u),
 ensures matches(Re::Cat(Box::new(a),Box::new(Re::Chr(c))),u+seq![c]),
{
 let w=u+seq![c];
 reveal_with_fuel(matches,2);
 assert(w.subrange(0,u.len() as int) =~= u);
 assert(w.subrange(u.len() as int,w.len() as int) =~= seq![c]);
 assert(exists|i:int| 0<=i<=w.len() && matches(a,#[trigger] w.subrange(0,i)) && matches(Re::Chr(c),w.subrange(i,w.len() as int))) by {
  let i=u.len() as int;
  assert(matches(a,w.subrange(0,i)));
  assert(matches(Re::Chr(c),w.subrange(i,w.len() as int)));
 }
}
pub open spec fn counted_node(x:Syn,n:nat,m:nat,k:int)->Syn {
 Syn { span:Span {lo:x.span.lo,hi:k as usize},node:SyntaxKind::RepRange(Box::new(x),n as u32,m as u32) }
}
// item: R09.H1v
// pair: R09.H1d
pub fn parse_counted(s:&Vec<char>,j:usize,x:Syn)->(res:Result<(Syn,usize),PErr>)
 requires j<s.len(),s@[j as int]=='{',wf(x,s.len() as nat),x.span.hi==j,x.span.lo<j,
 ensures match res {
  Ok((y,k)) => j<k<=s.len() && wf(y,s.len() as nat) && y.span.lo==x.span.lo && y.span.hi==k,
  Err(e) => e.pos<=s.len(),
 },
 forall|n:nat,m:nat,k:int| #[trigger] counted_at(s@,j as int,n,m,k) ==> res==Ok::<(Syn,usize),PErr>((counted_node(x,n,m,k),k as usize)),
{
 // did: implement the frozen R09.H1v statement using the printed worked interfaces.

 let len=s.len();
 if j+1>=len {return Err(PErr {pos:j+1,kind:ErrKind::UnexpectedEnd});}
 let d=s[j+1];
 if d<'0' || d>'9' {return Err(PErr {pos:j+1,kind:ErrKind::UnexpectedChar});}
 let lo=(d as u32)-('0' as u32);
 if j+2>=len {return Err(PErr {pos:j+2,kind:ErrKind::UnexpectedEnd});}
 if s[j+2]=='}' {
  let start=x.span.lo;return Ok((Syn {node:SyntaxKind::RepRange(Box::new(x),lo,lo),span:Span {lo:start,hi:j+3}},j+3));
 }
 if s[j+2]!=',' {return Err(PErr {pos:j+2,kind:ErrKind::UnexpectedChar});}
 if j+3>=len {return Err(PErr {pos:j+3,kind:ErrKind::UnexpectedEnd});}
 let e=s[j+3];
 if e<'0' || e>'9' {return Err(PErr {pos:j+3,kind:ErrKind::UnexpectedChar});}
 if j+4>=len {return Err(PErr {pos:j+4,kind:ErrKind::UnexpectedEnd});}
 if s[j+4]!='}' {return Err(PErr {pos:j+4,kind:ErrKind::UnexpectedChar});}
 let hi=(e as u32)-('0' as u32);
 if hi<lo {return Err(PErr {pos:j+3,kind:ErrKind::BoundsOrder});}
 let start=x.span.lo;
 Ok((Syn {node:SyntaxKind::RepRange(Box::new(x),lo,hi),span:Span {lo:start,hi:j+5}},j+5))
}
// item: R09.H2v
// pair: R09.H2d
pub fn class_items(s:&Vec<char>,i:usize,mut acc:SpanClass)->(res:Result<(SpanClass,usize),PErr>)
 requires i<=s.len(),acc.valid() && class_valid(acc.ranges@),
 ensures match res {Ok((xs,k))=>i<k<=s.len() && xs.valid() && class_valid(xs.ranges@),Err(e)=>e.pos<=s.len()},
 forall|k:int| #[trigger] simple_class_body(s@,i as int,k) ==> res is Ok && res->Ok_0.1==k+1,
{
 // did: implement the frozen R09.H2v statement using the printed worked interfaces.

 let mut j=i;
 while j<s.len()
  invariant i<=j<=s.len(),acc.valid() && class_valid(acc.ranges@),
   forall|k:int| #[trigger] simple_class_body(s@,i as int,k) ==> simple_class_body(s@,j as int,k),
  decreases s.len()-j,
 {
  if s[j]==']' {return Ok((acc,j+1));}
  let escaped=s[j]=='\\' && j+1<s.len();
  let c=if escaped {s[j+1]} else {s[j]};
  let k=if escaped {j+2} else {j+1};
  if k<s.len() && k+1<s.len() && s[k]=='-' && s[k+1]!=']' {
   let d=s[k+1];
   if d<c {return Err(PErr {pos:k+1,kind:ErrKind::ClassRange});}
   if (d as u32)>=CLASS_MAX {return Err(PErr {pos:k+1,kind:ErrKind::ClassRange});}
   let next=acc.class_insert(c,d);

   proof {
    assert forall|q:int| 0<=q<next.ranges@.len() implies range_valid(next.ranges@[q].0,next.ranges@[q].1) by {
     let h=next.ranges@[q].1;
     assert(next@.contains(h)) by { assert(ranges::in_range(next.ranges@[q],h)); }
     if !(c<=h<=d) {
      let k=choose|k:int| 0<=k<acc.ranges@.len() && ranges::in_range(#[trigger] acc.ranges@[k],h);
      assert((h as u32)<CLASS_MAX);
     }
    }
   }
   acc=next;j=k+2;
  } else {
   if (c as u32)>=CLASS_MAX {return Err(PErr {pos:j,kind:ErrKind::ClassRange});}
   let next=acc.class_insert(c,c);

   proof {
    assert forall|q:int| 0<=q<next.ranges@.len() implies range_valid(next.ranges@[q].0,next.ranges@[q].1) by {
     let h=next.ranges@[q].1;
     assert(next@.contains(h)) by { assert(ranges::in_range(next.ranges@[q],h)); }
     if !(c<=h<=c) {
      let k=choose|k:int| 0<=k<acc.ranges@.len() && ranges::in_range(#[trigger] acc.ranges@[k],h);
      assert((h as u32)<CLASS_MAX);
     }
    }
   }
   acc=next;j=k;
  }
 }
 Err(PErr {pos:j,kind:ErrKind::UnclosedClass})
}
// item: R09.W3v
pub fn parse_alt(s:&Vec<char>,i:usize)->(res:Result<(Syn,usize),PErr>)
 requires i<=s.len(),
 ensures ok_span(res,i,s.len() as nat),
 no_special_from(s@,i as int) ==> res is Ok && res->Ok_0.1==s.len() && matches(lower(res->Ok_0.0),s@.subrange(i as int,s.len() as int)) && lowering_nodes_r09(res->Ok_0.0)==(if i==s.len() {1int} else {2*(s.len()-i)-1}),
 decreases s.len()-i,3nat,
{
 let (mut x,mut j)=parse_cat(s,i)?;
 while j<s.len() && s[j]=='|'
  invariant i<=j<=s.len(),wf(x,s.len() as nat),x.span.lo==i,x.span.hi==j,
  no_special_from(s@,i as int) ==> j==s.len() && matches(lower(x),s@.subrange(i as int,s.len() as int)) && lowering_nodes_r09(x)==(if i==s.len() {1int} else {2*(s.len()-i)-1}),
  decreases s.len()-j,
 {
  let (y,k)=parse_cat(s,j+1)?;
  x=Syn {node:SyntaxKind::Alt(Box::new(x),Box::new(y)),span:Span {lo:i,hi:k}};j=k;
 }
 Ok((x,j))
}
pub fn parse_cat(s:&Vec<char>,i:usize)->(res:Result<(Syn,usize),PErr>)
 requires i<=s.len(),
 ensures ok_span(res,i,s.len() as nat),
 no_special_from(s@,i as int) ==> res is Ok && res->Ok_0.1==s.len() && matches(lower(res->Ok_0.0),s@.subrange(i as int,s.len() as int)) && lowering_nodes_r09(res->Ok_0.0)==(if i==s.len() {1int} else {2*(s.len()-i)-1}),
 decreases s.len()-i,2nat,
{
 let mut x=Syn {node:SyntaxKind::Eps,span:Span {lo:i,hi:i}};
 let mut j=i;
 let mut first=true;
 while j<s.len() && s[j]!=')' && s[j]!='|'
  invariant i<=j<=s.len(),wf(x,s.len() as nat),x.span.lo==i,x.span.hi==j,first <==> j==i,
  no_special_from(s@,i as int) ==> no_special_from(s@,j as int) && matches(lower(x),s@.subrange(i as int,j as int)) && lowering_nodes_r09(x)==(if j==i {1int} else {2*(j-i)-1}),
  decreases s.len()-j,
 {
  let (y,k)=parse_post(s,j)?;
  proof {
   if no_special_from(s@,i as int) {
    reveal_with_fuel(lower,2);
    reveal_with_fuel(lowering_nodes_r09,2);
    assert(y==(Syn {node:SyntaxKind::Chr(s@[j as int]),span:Span {lo:j,hi:(j+1) as usize}}) && k==j+1);
    assert(s@.subrange(i as int,j+1) =~= s@.subrange(i as int,j as int)+seq![s@[j as int]]);
    if first {
     assert(s@.subrange(i as int,k as int) =~= seq![s@[j as int]]);
     reveal_with_fuel(matches,2);
    } else {
     lemma_literal_append_r09(lower(x),s@.subrange(i as int,j as int),s@[j as int]);
    }
   }
  }
  x=if first {y} else {Syn {node:SyntaxKind::Cat(Box::new(x),Box::new(y)),span:Span {lo:i,hi:k}}};
  proof { if no_special_from(s@,i as int) {
   assert(no_special_from(s@,k as int));
   reveal_with_fuel(lower,2);
    reveal_with_fuel(lowering_nodes_r09,2);
   assert(matches(lower(x),s@.subrange(i as int,k as int)));
  } }
  first=false;j=k;
 }
 Ok((x,j))
}
pub fn parse_post(s:&Vec<char>,i:usize)->(res:Result<(Syn,usize),PErr>)
 requires i<s.len(),
 ensures ok_span(res,i,s.len() as nat),res is Ok ==> res->Ok_0.1>i,
 no_special_from(s@,i as int) ==> res==Ok::<(Syn,usize),PErr>((Syn {node:SyntaxKind::Chr(s@[i as int]),span:Span {lo:i,hi:(i+1) as usize}},(i+1) as usize)),
 decreases s.len()-i,1nat,
{
 let (mut x,mut j)=parse_atom(s,i)?;
 while j<s.len() && (s[j]=='*' || s[j]=='+' || s[j]=='?' || s[j]=='{')
  invariant i<j<=s.len(),wf(x,s.len() as nat),x.span.lo==i,x.span.hi==j,
  no_special_from(s@,i as int) ==> x==(Syn {node:SyntaxKind::Chr(s@[i as int]),span:Span {lo:i,hi:(i+1) as usize}}) && j==i+1,
  decreases s.len()-j,
 {
  let c=s[j];
  if c=='{' {let (y,k)=parse_counted(s,j,x)?;x=y;j=k;}
  else {
   x=Syn {node:if c=='*' {SyntaxKind::Star(Box::new(x))} else if c=='+' {SyntaxKind::Plus(Box::new(x))} else {SyntaxKind::Opt(Box::new(x))},span:Span {lo:i,hi:j+1}};
   j=j+1;
  }
 }
 Ok((x,j))
}
pub fn parse_atom(s:&Vec<char>,i:usize)->(res:Result<(Syn,usize),PErr>)
 requires i<s.len(),
 ensures ok_span(res,i,s.len() as nat),res is Ok ==> res->Ok_0.1>i,
 no_special_from(s@,i as int) ==> res==Ok::<(Syn,usize),PErr>((Syn {node:SyntaxKind::Chr(s@[i as int]),span:Span {lo:i,hi:(i+1) as usize}},(i+1) as usize)),
 decreases s.len()-i,0nat,
{
 let c=s[i];
 if c=='(' {
  let (x,j)=parse_alt(s,i+1)?;
  if j<s.len() && s[j]==')' {Ok((Syn {node:SyntaxKind::Group(Box::new(x)),span:Span {lo:i,hi:j+1}},j+1))}
  else {Err(PErr {pos:j,kind:ErrKind::UnclosedParen})}
 } else if c=='[' {
  let (xs,j)=class_items(s,i+1,SpanClass::class_empty())?;
  Ok((Syn {node:SyntaxKind::Class(xs),span:Span {lo:i,hi:j}},j))
 } else if c=='\\' {
  if i+1<s.len() {Ok((Syn {node:SyntaxKind::Chr(s[i+1]),span:Span {lo:i,hi:i+2}},i+2))}
  else {Err(PErr {pos:i+1,kind:ErrKind::UnexpectedEnd})}
 } else if c=='*' || c=='+' || c=='?' || c=='{' || c=='}' || c==']' || c==')' || c=='|' {
  Err(PErr {pos:i,kind:ErrKind::UnexpectedChar})
 } else {Ok((Syn {node:SyntaxKind::Chr(c),span:Span {lo:i,hi:i+1}},i+1))}
}
pub fn parse(s:&Vec<char>)->(res:Result<Syn,PErr>)
 ensures no_special_from(s@,0) ==> res is Ok && matches(lower(res->Ok_0),s@) && lowering_nodes_r09(res->Ok_0)==(if s.len()==0 {1int} else {2*s.len()-1}),
 match res {Ok(t)=>wf(t,s.len() as nat) && t.span.lo==0 && t.span.hi==s.len(),Err(e)=>e.pos<=s.len()},
{
 let (x,j)=parse_alt(s,0)?;
 proof { assert(s@.subrange(0,s.len() as int) =~= s@); }
 if j==s.len() {Ok(x)} else {Err(PErr {pos:j,kind:ErrKind::UnexpectedChar})}
}
}
use vstd::arithmetic::div_mod::{lemma_fundamental_div_mod,lemma_mod_bound};
use vstd::arithmetic::mul::lemma_mul_is_commutative;
verus! {
proof fn quotient_product_guard_r09(b:int,q:int,r:int,d:int)
 requires d>0,0<=r<d,
 ensures (b<=q)==(b*d<=q*d+r),
{
 assert((b<=q)==(b*d<=q*d+r)) by (nonlinear_arith)
  requires d>0,0<=r<d;
}
proof fn division_budget_guard_r09(base:int,space:int,copies:int)
 requires base>=0,space>=0,copies>0,
 ensures (base<=space/copies)==(base*copies<=space),
{
 lemma_fundamental_div_mod(space,copies);
 lemma_mod_bound(space,copies);
 quotient_product_guard_r09(base,space/copies,space%copies,copies);
 lemma_mul_is_commutative(copies,space/copies);
}

// item: R09.H3v
// pair: R09.H3d
fn repeat_expansion_budget_r09(base:u32,lo:u32,hi:u32,cap:u32)->(res:Option<u32>)
 requires lo<=hi<=9,
 ensures match res {
  Some(cost) => cost<=cap && (cost as int)==3+(base as int)*(hi as int)+(lo as int)+3*((hi as int)-(lo as int)),
  None => 3+(base as int)*(hi as int)+(lo as int)+3*((hi as int)-(lo as int))>(cap as int),
 },
{
 // did: implement the frozen R09.H3v statement using the printed worked interfaces.

 let overhead:u32=3+lo+3*(hi-lo);
 if overhead>cap {return None;}
 proof {
  if hi>0 { division_budget_guard_r09(base as int,(cap-overhead) as int,hi as int); }
 }
 if hi>0 && base>(cap-overhead)/hi {return None;}
 let cost:u32=base*hi+overhead;
 Some(cost)
}
}

verus! {
// item: R09.W2v
fn checked_add_cost_r09(a:u32,b:u32,extra:u32,cap:u32)->(res:Option<u32>)
 ensures match res {
  Some(n)=>n<=cap && (n as int)==(a as int)+(b as int)+(extra as int),
  None=>(a as int)+(b as int)+(extra as int)>(cap as int),
 },
{
 if extra>cap {return None;}
 if a>cap-extra {return None;}
 if b>cap-extra-a {return None;}
 Some(a+b+extra)
}
fn checked_class_cost_r09(cc:&SpanClass,cap:u32)->(res:Option<u32>)
 requires class_valid(cc.ranges@),
 ensures match res {Some(n)=>n<=cap && n==class_nodes_r09(cc.ranges@),None=>class_nodes_r09(cc.ranges@)>cap},
{
 proof {assert(class_nodes_r09(cc.ranges@)>=1);}
 if cap<1 {return None;}
 let mut cost:u32=1;let mut i:usize=0;
 proof {assert(cc.ranges@.subrange(0,cc.ranges.len() as int) =~= cc.ranges@);}
 while i<cc.ranges.len()
  invariant i<=cc.ranges.len(),cost<=cap,class_valid(cc.ranges@),
   (cost as nat)+class_nodes_r09(cc.ranges@.subrange(i as int,cc.ranges.len() as int))==class_nodes_r09(cc.ranges@)+1,
  decreases cc.ranges.len()-i,
 {
  let (lo,hi)=cc.ranges[i];
  let width=(hi as u32)-(lo as u32);
  let range:u32=2*width+1;
  proof {
   let suffix=cc.ranges@.subrange(i as int,cc.ranges.len() as int);
   let tail=cc.ranges@.subrange(i+1,cc.ranges.len() as int);
   assert(suffix[0]==cc.ranges@[i as int]);
   assert(suffix.drop_first() =~= tail);
   assert(class_nodes_r09(tail)>=1);
   assert(range==range_nodes_r09(lo,hi));
  }
  cost=checked_add_cost_r09(cost,range,1,cap)?;
  i=i+1;
 }
 proof {assert(cc.ranges@.subrange(cc.ranges.len() as int,cc.ranges.len() as int) =~= Seq::<(char,char)>::empty());}
 Some(cost)
}
proof fn lemma_repetition_cost_grows_r09(base:nat,n:nat,m:nat)
 requires n<=m,m>0,
 ensures 3+n*(base+1)+(m-n)*(base+3)>=base,
{
 assert(3+n*(base+1)+(m-n)*(base+3)>=base) by (nonlinear_arith)
  requires n<=m,m>0,base>=0,n>=0;
}
fn checked_lowering_cost_r09(t:&Syn,len:usize,cap:u32)->(res:Option<u32>)
 requires wf(*t,len as nat),
 ensures match res {Some(n)=>n<=cap && n==lowering_nodes_r09(*t),None=>lowering_nodes_r09(*t)>cap},
 decreases *t,
{
 reveal_with_fuel(lowering_nodes_r09,2);
 let result=match &t.node {
  SyntaxKind::Eps | SyntaxKind::Chr(_) => if cap>=1 {Some(1)} else {None},
  SyntaxKind::Class(cc)=>checked_class_cost_r09(cc,cap),
  SyntaxKind::Alt(a,b) | SyntaxKind::Cat(a,b)=>{
   let left=checked_lowering_cost_r09(a,len,cap)?;
   let right=checked_lowering_cost_r09(b,len,cap)?;
   checked_add_cost_r09(left,right,1,cap)
  },
  SyntaxKind::Star(a)=>{let child=checked_lowering_cost_r09(a,len,cap)?;checked_add_cost_r09(child,0,1,cap)},
  SyntaxKind::Plus(a)=>{let child=checked_lowering_cost_r09(a,len,cap)?;checked_add_cost_r09(child,child,2,cap)},
  SyntaxKind::Opt(a)=>{let child=checked_lowering_cost_r09(a,len,cap)?;checked_add_cost_r09(child,0,2,cap)},
  SyntaxKind::Group(a)=>checked_lowering_cost_r09(a,len,cap),
  SyntaxKind::RepRange(a,n,m)=>{
   if *m==0 {
    proof {let base=lowering_nodes_r09(**a) as int; assert(3+(*n as int)*(base+1)+((*m as int)-(*n as int))*(base+3)==3) by (nonlinear_arith) requires *m==0,*n==0; assert(lowering_nodes_r09(*t)==3);}
    checked_add_cost_r09(0,0,3,cap)
   }
   else {
    proof {lemma_repetition_cost_grows_r09(lowering_nodes_r09(**a),*n as nat,*m as nat);}
    let child=checked_lowering_cost_r09(a,len,cap)?;
    let result=repeat_expansion_budget_r09(child,*n,*m,cap);
    proof {
     let base=lowering_nodes_r09(**a) as int;
     assert(3+(*n as int)*(base+1)+((*m as int)-(*n as int))*(base+3) == 3+base*(*m as int)+(*n as int)+3*((*m as int)-(*n as int))) by (nonlinear_arith);
    }
    proof {assert(match result {Some(n)=>n<=cap && n==lowering_nodes_r09(*t),None=>lowering_nodes_r09(*t)>cap});}
    result
   }
  },
 };
 assert(match result {Some(n)=>n<=cap && n==lowering_nodes_r09(*t),None=>lowering_nodes_r09(*t)>cap});
 result
}
}
use vstd::utf8::*;
use vstd::string::{StrSliceExecFns,StringSliceAdditionalSpecFns};
verus! {
fn scalar_char_r09(n: u32) -> (c: char)
    requires is_scalar(n),
    ensures c as u32 == n, c == n as char,
{
    let ghost wanted=n as char;
    proof { assert(wanted as u32 == n); }
    let mut bytes: Vec<u8> = Vec::new();
    if n <= 0x7f {
        bytes.push((n & 0x7f) as u8);
    } else if n <= 0x7ff {
        bytes.push(0xc0 | ((n >> 6) & 0x1f) as u8);
        bytes.push(0x80 | (n & 0x3f) as u8);
    } else if n <= 0xffff {
        bytes.push(0xe0 | ((n >> 12) & 0xf) as u8);
        bytes.push(0x80 | ((n >> 6) & 0x3f) as u8);
        bytes.push(0x80 | (n & 0x3f) as u8);
    } else {
        bytes.push(0xf0 | ((n >> 18) & 0x7) as u8);
        bytes.push(0x80 | ((n >> 12) & 0x3f) as u8);
        bytes.push(0x80 | ((n >> 6) & 0x3f) as u8);
        bytes.push(0x80 | (n & 0x3f) as u8);
    }
    proof {
        assert(bytes@ =~= encode_scalar(n));
        assert(seq![wanted].drop_first() =~= Seq::<char>::empty());
        reveal_with_fuel(encode_utf8, 2);
        assert(encode_utf8(seq![wanted]) =~= encode_scalar(n));
        encode_utf8_valid_utf8(seq![wanted]);
    }
    let s=unsafe { str::from_utf8_unchecked(bytes.as_slice()) };
    proof {
        encode_utf8_decode_utf8(seq![wanted]);
        encode_utf8_decode_utf8(s@);
        assert(s@ =~= seq![wanted]);
    }
    s.get_char(0)
}


fn range_lower_exec_r09(lo:char,hi:char)->(out:Re)
 requires range_valid(lo,hi),
 ensures out==range_re(lo,hi),
{
 let low=lo as u32;
 let mut n=hi as u32;
 let mut out=Re::Chr(hi);
 while n>low
  invariant low==lo as u32,low<=n<=hi as u32,(hi as u32)<CLASS_MAX,
   out==range_re(n as char,hi),
  decreases n-low,
 {
  let ghost old_n=n;
  n=n-1;
  proof {assert(is_scalar(n));}
  let c=scalar_char_r09(n);
  proof {assert(((c as u32)+1) as char==old_n as char);}
  out=Re::Alt(Box::new(Re::Chr(c)),Box::new(out));
 }
 out
}
fn class_lower_exec_r09(cc:&SpanClass)->(out:Re)
 requires class_valid(cc.ranges@),
 ensures out==class_re(cc.ranges@),
{
 let mut i=cc.ranges.len();
 let mut out=Re::Empty;
 while i>0
  invariant i<=cc.ranges.len(),class_valid(cc.ranges@),
   out==class_re(cc.ranges@.subrange(i as int,cc.ranges.len() as int)),
  decreases i,
 {
  i=i-1;
  let (lo,hi)=cc.ranges[i];
  let first=range_lower_exec_r09(lo,hi);
  proof {
   let suffix=cc.ranges@.subrange(i as int,cc.ranges.len() as int);
   assert(suffix[0]==cc.ranges@[i as int]);
   assert(suffix.drop_first() =~= cc.ranges@.subrange(i+1,cc.ranges.len() as int));
  }
  out=Re::Alt(Box::new(first),Box::new(out));
 }
 proof {assert(cc.ranges@.subrange(0,cc.ranges.len() as int) =~= cc.ranges@);}
 out
}
fn copies_lower_exec_r09(r:&Re,k:u32)->(out:Re)
 ensures out==copies(*r,k as nat),
{
 let mut i:u32=0;let mut out=Re::Eps;
 while i<k
  invariant i<=k,out==copies(*r,i as nat),
  decreases k-i,
 {
  let first=copy_re(r);
  out=Re::Cat(Box::new(first),Box::new(out));i=i+1;
 }
 out
}
fn optional_lower_exec_r09(r:&Re,k:u32)->(out:Re)
 ensures out==copies_up_to(*r,k as nat),
{
 let mut i:u32=0;let mut out=Re::Eps;
 while i<k
  invariant i<=k,out==copies_up_to(*r,i as nat),
  decreases k-i,
 {
  let first=copy_re(r);
  out=Re::Alt(Box::new(Re::Eps),Box::new(Re::Cat(Box::new(first),Box::new(out))));i=i+1;
 }
 out
}
fn repetition_lower_exec_r09(r:&Re,n:u32,m:u32)->(out:Re)
 requires n<=m,
 ensures out==rep_range(*r,n as nat,m as nat),
{
 let fixed=copies_lower_exec_r09(r,n);
 let optional=optional_lower_exec_r09(r,m-n);
 Re::Cat(Box::new(fixed),Box::new(optional))
}
fn lowering_exec_r09(t:&Syn,len:usize)->(out:Re)
 requires wf(*t,len as nat),
 ensures out==lower(*t),
 decreases *t,
{
 match &t.node {
  SyntaxKind::Eps=>Re::Eps,
  SyntaxKind::Chr(c)=>Re::Chr(*c),
  SyntaxKind::Class(cc)=>class_lower_exec_r09(cc),
  SyntaxKind::Alt(a,b)=>{
   let left=lowering_exec_r09(a,len);let right=lowering_exec_r09(b,len);
   Re::Alt(Box::new(left),Box::new(right))
  },
  SyntaxKind::Cat(a,b)=>{
   let left=lowering_exec_r09(a,len);let right=lowering_exec_r09(b,len);
   Re::Cat(Box::new(left),Box::new(right))
  },
  SyntaxKind::Star(a)=>{let child=lowering_exec_r09(a,len);Re::Star(Box::new(child))},
  SyntaxKind::Plus(a)=>{
   let child=lowering_exec_r09(a,len);let second=copy_re(&child);
   Re::Cat(Box::new(child),Box::new(Re::Star(Box::new(second))))
  },
  SyntaxKind::Opt(a)=>{let child=lowering_exec_r09(a,len);Re::Alt(Box::new(Re::Eps),Box::new(child))},
  SyntaxKind::Group(a)=>lowering_exec_r09(a,len),
  SyntaxKind::RepRange(a,n,m)=>{
   if *m==0 {Re::Cat(Box::new(Re::Eps),Box::new(Re::Eps))}
   else {let child=lowering_exec_r09(a,len);repetition_lower_exec_r09(&child,*n,*m)}
  },
 }
}
}
verus! {
fn frontend_r09(s:&Vec<char>,cap:u32)->(res:Result<(Syn,Re),PErr>)
 ensures match res {
  Ok((tree,lowered)) => wf(tree,s.len() as nat) && tree.span.lo==0 && tree.span.hi==s.len()
    && lowered==lower(tree) && node_count(lowered)<=cap,
  Err(e) => e.pos<=s.len(),
 },
 no_special_from(s@,0) && (if s.len()==0 {1int} else {2*s.len()-1})<=cap ==>
   res is Ok && matches(res->Ok_0.1,s@),
{
 let tree=parse(s)?;
 match checked_lowering_cost_r09(&tree,s.len(),cap) {
  None=>Err(PErr {pos:0,kind:ErrKind::ExpansionBudget}),
  Some(_)=>{
   let lowered=lowering_exec_r09(&tree,s.len());
   proof {lemma_lowering_nodes_r09(tree,s.len() as nat);}
   Ok((tree,lowered))
  },
 }
}
}
use rg_re_a1b::*;
verus! {
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
// item: R09.W4v
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
// item: R09.H4v
// pair: R09.H4d
proof fn lemma_repetition_interval_r09(r:Re,n:nat,m:nat,s:Seq<char>)
 requires n<=m,
 ensures matches(rep_range(r,n,m),s)==(exists|k:nat| n<=k<=m && #[trigger] matches(copies(r,k),s)),
{
 // did: implement the frozen R09.H4v statement using the printed worked interfaces.

 let extra=(m-n) as nat;
 if matches(rep_range(r,n,m),s) {
  let i=choose|i:int| 0<=i<=s.len() && matches(copies(r,n),#[trigger] s.subrange(0,i)) && matches(copies_up_to(r,extra),s.subrange(i,s.len() as int));
  lemma_copies_optional_r09(r,extra,s.subrange(i,s.len() as int));
  let k=choose|k:nat| k<=extra && #[trigger] matches(copies(r,k),s.subrange(i,s.len() as int));
  lemma_copies_join_r09(r,n,k,s);assert(matches(copies(r,n+k),s));
 }
 if exists|k:nat| n<=k<=m && #[trigger] matches(copies(r,k),s) {
  let k=choose|k:nat| n<=k<=m && #[trigger] matches(copies(r,k),s);
  lemma_copies_join_r09(r,n,(k-n) as nat,s);
  let i=choose|i:int| 0<=i<=s.len() && matches(copies(r,n),#[trigger] s.subrange(0,i)) && matches(copies(r,(k-n) as nat),s.subrange(i,s.len() as int));
  lemma_copies_optional_r09(r,extra,s.subrange(i,s.len() as int));
  assert(matches(copies_up_to(r,extra),s.subrange(i,s.len() as int)));
 }
}
}
verus! {
pub struct EffectCursorR09 {pub text:Vec<char>,pub position:usize}
// item: R09.W1v
fn read_bound_r09(c:char,pos:usize,len:usize)->(res:Result<u32,PErr>)
 requires pos<=len,
 ensures match res {Ok(n)=>is_bound_char(c) && n==bound_value(c),Err(e)=>!is_bound_char(c) && e.pos==pos},
{
 if c<'0' || c>'9' {Err(PErr {pos,kind:ErrKind::UnexpectedChar})}
 else {Ok((c as u32)-('0' as u32))}
}
// item: R09.T1v
// pair: R09.T1d
// uses: error-propagation, old
fn read_bound_cursor_r09(cur:&mut EffectCursorR09)->(res:Result<u32,PErr>)
 requires old(cur).position<old(cur).text.len(),
 ensures final(cur).text@==old(cur).text@,
 final(cur).position==old(cur).position+1,
 match res {
  Ok(n)=>is_bound_char(old(cur).text@[old(cur).position as int]) && n==bound_value(old(cur).text@[old(cur).position as int]),
  Err(e)=>!is_bound_char(old(cur).text@[old(cur).position as int]) && e.pos==old(cur).position,
 },
{
 // did: implement the frozen R09.T1v statement using the printed worked interfaces.

 let start=cur.position;let c=cur.text[start];let len=cur.text.len();
 cur.position=start+1;
 let n=read_bound_r09(c,start,len)?;
 Ok(n)
}
// item: R09.H5v
// pair: R09.H5d
// uses: error-propagation, old
fn counted_cursor_r09(cur:&mut EffectCursorR09,x:Syn)->(res:Result<Syn,PErr>)
 requires old(cur).position<old(cur).text.len(),old(cur).text@[old(cur).position as int]=='{',
 wf(x,old(cur).text.len() as nat),x.span.hi==old(cur).position,x.span.lo<old(cur).position,
 ensures final(cur).text@==old(cur).text@,
 old(cur).position<=final(cur).position<=final(cur).text.len(),
 match res {
  Ok(y)=>wf(y,final(cur).text.len() as nat) && y.span.lo==x.span.lo && y.span.hi==final(cur).position && old(cur).position<final(cur).position,
  Err(e)=>final(cur).position==old(cur).position && e.pos<=final(cur).text.len(),
 },
 forall|n:nat,m:nat,k:int| #[trigger] counted_at(old(cur).text@,old(cur).position as int,n,m,k) ==> res==Ok::<Syn,PErr>(counted_node(x,n,m,k)) && final(cur).position==k,
{
 // did: implement the frozen R09.H5v statement using the printed worked interfaces.

 let start=cur.position;
 let (y,k)=parse_counted(&cur.text,start,x)?;
 cur.position=k;
 Ok(y)
}
}

// item: R09.C3v recognise:mut-ref
// A mutable borrow gives temporary mutation access; old/final describe state.
// item: R09.C6v recognise:result
// Result carries either payload or positioned error, not a Boolean success flag.
