//! Private parser port over positioned A3. Safety/completion contracts are
//! distinct from the independently exercised grammar fidelity oracle.
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a2::*;
use rg_re_a3::*;
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
pub fn parse_counted(s:&Vec<char>,j:usize,x:Syn)->(res:Result<(Syn,usize),PErr>)
 requires j<s.len(),s@[j as int]=='{',wf(x,s.len() as nat),x.span.hi==j,x.span.lo<j,
 ensures match res {
  Ok((y,k)) => j<k<=s.len() && wf(y,s.len() as nat) && y.span.lo==x.span.lo && y.span.hi==k,
  Err(e) => e.pos<=s.len(),
 },
 forall|n:nat,m:nat,k:int| #[trigger] counted_at(s@,j as int,n,m,k) ==> res==Ok::<(Syn,usize),PErr>((counted_node(x,n,m,k),k as usize)),
{
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
pub fn class_items(s:&Vec<char>,i:usize,mut acc:SpanClass)->(res:Result<(SpanClass,usize),PErr>)
 requires i<=s.len(),acc.valid() && class_valid(acc.ranges@),
 ensures match res {Ok((xs,k))=>i<k<=s.len() && xs.valid() && class_valid(xs.ranges@),Err(e)=>e.pos<=s.len()},
 forall|k:int| #[trigger] simple_class_body(s@,i as int,k) ==> res is Ok && res->Ok_0.1==k+1,
{
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
pub fn parse_alt(s:&Vec<char>,i:usize)->(res:Result<(Syn,usize),PErr>)
 requires i<=s.len(),
 ensures ok_span(res,i,s.len() as nat),
 no_special_from(s@,i as int) ==> res is Ok && res->Ok_0.1==s.len() && matches(lower(res->Ok_0.0),s@.subrange(i as int,s.len() as int)),
 decreases s.len()-i,3nat,
{
 let (mut x,mut j)=parse_cat(s,i)?;
 while j<s.len() && s[j]=='|'
  invariant i<=j<=s.len(),wf(x,s.len() as nat),x.span.lo==i,x.span.hi==j,
  no_special_from(s@,i as int) ==> j==s.len() && matches(lower(x),s@.subrange(i as int,s.len() as int)),
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
 no_special_from(s@,i as int) ==> res is Ok && res->Ok_0.1==s.len() && matches(lower(res->Ok_0.0),s@.subrange(i as int,s.len() as int)),
 decreases s.len()-i,2nat,
{
 let mut x=Syn {node:SyntaxKind::Eps,span:Span {lo:i,hi:i}};
 let mut j=i;
 let mut first=true;
 while j<s.len() && s[j]!=')' && s[j]!='|'
  invariant i<=j<=s.len(),wf(x,s.len() as nat),x.span.lo==i,x.span.hi==j,first ==> j==i,
  no_special_from(s@,i as int) ==> no_special_from(s@,j as int) && matches(lower(x),s@.subrange(i as int,j as int)),
  decreases s.len()-j,
 {
  let (y,k)=parse_post(s,j)?;
  proof {
   if no_special_from(s@,i as int) {
    reveal_with_fuel(lower,2);
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
 ensures no_special_from(s@,0) ==> res is Ok && matches(lower(res->Ok_0),s@),
 match res {Ok(t)=>wf(t,s.len() as nat) && t.span.lo==0 && t.span.hi==s.len(),Err(e)=>e.pos<=s.len()},
{
 let (x,j)=parse_alt(s,0)?;
 proof { assert(s@.subrange(0,s.len() as int) =~= s@); }
 if j==s.len() {Ok(x)} else {Err(PErr {pos:j,kind:ErrKind::UnexpectedChar})}
}
}
