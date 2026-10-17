// Reference Solution.
/*! R11 — Theory. Standalone A1–A4, fixed relative certificate rules.
The core has T1 plus seven hand/project tasks in Dafny and nine in Verus;
the checkpoint has two tasks in each language. Preserve models and domains.
Compiled checks, metatheory and rule fidelity establish different properties.
Tracked evidence is proof data; runtime certificates are ordinary derivations.
*/
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a4::*;
verus! {
// reference-only
proof fn sound_word_r11(d:Derivation,r:Re,s:Seq<char>)
 requires valid_word_r10(d,r,s),
 ensures matches(r,s),
 decreases d,
{
 // did: unfold the fixed model for this constructor obligation.
 reveal_with_fuel(valid_word_r10,2);
 match d {
  Derivation::DAltL(child)=>{sound_word_r11(*child,*r->Alt_0,s);},
  Derivation::DAltR(child)=>{sound_word_r11(*child,*r->Alt_1,s);},
  Derivation::DCat(k,left,right)=>{
   sound_word_r11(*left,*r->Cat_0,s.take(k as int));
   sound_word_r11(*right,*r->Cat_1,s.skip(k as int));
   assert(s.take(k as int)=~=s.subrange(0,k as int));
   assert(s.skip(k as int)=~=s.subrange(k as int,s.len() as int));
  },
  Derivation::DStarCons(k,left,right)=>{
   sound_word_r11(*left,*r->Star_0,s.take(k as int));
   sound_word_r11(*right,r,s.skip(k as int));
   assert(s.take(k as int)=~=s.subrange(0,k as int));
   assert(s.skip(k as int)=~=s.subrange(k as int,s.len() as int));
  },
  _=>{},
 }
}
// reference-only
proof fn complete_word_r11(r:Re,s:Seq<char>)
 requires s.len()<=usize::MAX,matches(r,s),
 ensures exists|d:Derivation| #[trigger] valid_word_r10(d,r,s),
 decreases r,s.len(),
{
 // did: unfold the fixed model for this constructor obligation.
 reveal_with_fuel(valid_word_r10,2);
 match r {
  Re::Empty=>{},
  Re::Eps=>{assert(valid_word_r10(Derivation::DEps,r,s));},
  Re::Chr(c)=>{assert(s=~=seq![c]);assert(valid_word_r10(Derivation::DChr,r,s));},
  Re::Alt(a,b)=>{
   if matches(*a,s) {
    complete_word_r11(*a,s);
    let child=choose|d:Derivation| #[trigger] valid_word_r10(d,*a,s);
    assert(valid_word_r10(Derivation::DAltL(Box::new(child)),r,s));
   } else {
    complete_word_r11(*b,s);
    let child=choose|d:Derivation| #[trigger] valid_word_r10(d,*b,s);
    assert(valid_word_r10(Derivation::DAltR(Box::new(child)),r,s));
   }
  },
  Re::Cat(a,b)=>{
   let i=choose|i:int| 0<=i<=s.len() && matches(*a,#[trigger] s.subrange(0,i)) && matches(*b,s.subrange(i,s.len() as int));
   assert(s.take(i)=~=s.subrange(0,i));assert(s.skip(i)=~=s.subrange(i,s.len() as int));
   complete_word_r11(*a,s.take(i));complete_word_r11(*b,s.skip(i));
   let left=choose|d:Derivation| #[trigger] valid_word_r10(d,*a,s.take(i));
   let right=choose|d:Derivation| #[trigger] valid_word_r10(d,*b,s.skip(i));
   let k=i as usize;assert(k as int==i);
   assert(valid_word_r10(Derivation::DCat(k,Box::new(left),Box::new(right)),r,s));
  },
  Re::Star(a)=>{
   if s.len()==0 {assert(valid_word_r10(Derivation::DStarNil,r,s));}
   else {
    let i=choose|i:int| 0<i<=s.len() && matches(*a,#[trigger] s.subrange(0,i)) && matches(r,s.subrange(i,s.len() as int));
    assert(s.take(i)=~=s.subrange(0,i));assert(s.skip(i)=~=s.subrange(i,s.len() as int));
    complete_word_r11(*a,s.take(i));complete_word_r11(r,s.skip(i));
    let left=choose|d:Derivation| #[trigger] valid_word_r10(d,*a,s.take(i));
    let right=choose|d:Derivation| #[trigger] valid_word_r10(d,r,s.skip(i));
    let k=i as usize;assert(k as int==i);
    assert(valid_word_r10(Derivation::DStarCons(k,Box::new(left),Box::new(right)),r,s));
   }
  },
 }
}
// item: R11.W2v
pub tracked struct CertificateEvidenceR11 {
 pub ghost tree:Derivation,pub ghost pattern:Re,pub ghost word:Seq<char>,
}
// item: R11.H2v
// pair: R11.H2d
// uses: tracked
proof fn consume_sound_r11(tracked evidence:CertificateEvidenceR11)
 requires valid_word_r10(evidence.tree,evidence.pattern,evidence.word),
 ensures matches(evidence.pattern,evidence.word),
 {
 // did: implement the fixed R11.H2v model and its original domain.
let tracked owned=evidence;sound_word_r11(owned.tree,owned.pattern,owned.word);}
// item: R11.H3v
// pair: R11.H3d
// uses: tracked
proof fn direct_evidence_r11(r:Re,s:Seq<char>,tracked out:&mut CertificateEvidenceR11)
 requires s.len()<=usize::MAX,matches(r,s),
 ensures final(out).pattern==r,final(out).word==s,valid_word_r10(final(out).tree,r,s),
{
 // did: implement the fixed R11.H3v model and its original domain.

 complete_word_r11(r,s);
 let ghost tree=choose|d:Derivation| #[trigger] valid_word_r10(d,r,s);
 let tracked result=CertificateEvidenceR11 {tree,pattern:r,word:s};
 *out=result;
}
// item: R11.W1v
proof fn slice_split_r11(s:Seq<char>,lo:int,hi:int,k:int)
 requires 0<=lo<=hi<=s.len(),0<=k<=hi-lo,
 ensures s.subrange(lo,hi).take(k)==s.subrange(lo,lo+k),
 s.subrange(lo,hi).skip(k)==s.subrange(lo+k,hi),
{
 assert(s.subrange(lo,hi).take(k)=~=s.subrange(lo,lo+k));
 assert(s.subrange(lo,hi).skip(k)=~=s.subrange(lo+k,hi));
}
// item: R11.H1v
// pair: R11.H1d
// triv: { false }
fn check_certificate_r11(d:&Derivation,r:&Re,s:&Vec<char>,lo:usize,hi:usize)->(ok:bool)
 ensures ok==valid(*d,*r,s@,lo as int,hi as int),
 decreases d,
{
 // did: implement the fixed R11.H1v model and its original domain.

 if lo>hi || hi>s.len() {return false;}
 // did: unfold the fixed validity model at this executable constructor.
 proof {reveal_with_fuel(valid_word_r10,2);}
 match (d,r) {
  (Derivation::DEps,Re::Eps)=>lo==hi,
  (Derivation::DChr,Re::Chr(c))=>{
   let ok=lo<hi && hi-lo==1 && s[lo]==*c;
   proof {
    if ok {assert(s@.subrange(lo as int,hi as int)=~=seq![*c]);}
    else if valid(*d,*r,s@,lo as int,hi as int) {
     let word=s@.subrange(lo as int,hi as int);
     assert(valid_word_r10(*d,*r,word));
     assert(word==seq![*c]);assert(word.len()==1);
     assert(word[0]==s@[lo as int]);assert(s@[lo as int]==*c);
    }
   }
   ok
  },
  (Derivation::DAltL(child),Re::Alt(a,_))=>check_certificate_r11(child,a,s,lo,hi),
  (Derivation::DAltR(child),Re::Alt(_,b))=>check_certificate_r11(child,b,s,lo,hi),
  (Derivation::DCat(k,left,right),Re::Cat(a,b))=>{
   if *k>hi-lo {false} else {
    let mid=lo+*k;
    proof {slice_split_r11(s@,lo as int,hi as int,*k as int);}
    check_certificate_r11(left,a,s,lo,mid) && check_certificate_r11(right,b,s,mid,hi)
   }
  },
  (Derivation::DStarNil,Re::Star(_))=>lo==hi,
  (Derivation::DStarCons(k,left,right),Re::Star(a))=>{
   if *k==0 || *k>hi-lo {false} else {
    let mid=lo+*k;
    proof {slice_split_r11(s@,lo as int,hi as int,*k as int);}
    check_certificate_r11(left,a,s,lo,mid) && check_certificate_r11(right,r,s,mid,hi)
   }
  },
  _=>false,
 }
}
}
verus! {

// item: R11.H5v
// pair: R11.H5d
// triv: { None }
fn search_r11(r:&Re,s:&Vec<char>,lo:usize,hi:usize)->(out:Option<Derivation>)
 requires lo<=hi<=s.len(),
 ensures match out {Some(d)=>valid(d,*r,s@,lo as int,hi as int),None=>!matches(*r,s@.subrange(lo as int,hi as int))},
 decreases node_count(*r),hi-lo,1nat,
{
 // did: implement the fixed R11.H5v model and its original domain.

 // did: unfold the fixed validity model at this executable constructor.
 proof {reveal_with_fuel(valid_word_r10,2);}
 match r {
  Re::Empty=>None,
  Re::Eps=>if lo==hi {Some(Derivation::DEps)} else {None},
  Re::Chr(c)=>{
   if lo<hi && hi-lo==1 && s[lo]==*c {
    proof {assert(s@.subrange(lo as int,hi as int)=~=seq![*c]);}
    Some(Derivation::DChr)
   } else {None}
  },
  Re::Alt(a,b)=>{
   match search_r11(a,s,lo,hi) {
    Some(d)=>Some(Derivation::DAltL(Box::new(d))),
    None=>match search_r11(b,s,lo,hi) {
     Some(d)=>Some(Derivation::DAltR(Box::new(d))),None=>None,
    },
   }
  },
  Re::Cat(a,b)=>search_cat_r11(a,b,s,lo,hi),
  Re::Star(a)=>{
   if lo==hi {Some(Derivation::DStarNil)} else {search_star_r11(a,s,lo,hi)}
  },
 }
}
// item: R11.H6v
// pair: R11.H6d
// triv: { None }
#[verifier::loop_isolation(false)]
fn search_cat_r11(a:&Re,b:&Re,s:&Vec<char>,lo:usize,hi:usize)->(out:Option<Derivation>)
 requires lo<=hi<=s.len(),
 ensures match out {Some(d)=>valid(d,Re::Cat(Box::new(*a),Box::new(*b)),s@,lo as int,hi as int),None=>!matches(Re::Cat(Box::new(*a),Box::new(*b)),s@.subrange(lo as int,hi as int))},
 decreases node_count(Re::Cat(Box::new(*a),Box::new(*b))),hi-lo,0nat,
{
 // did: implement the fixed R11.H6v model and its original domain.

 let ghost word=s@.subrange(lo as int,hi as int);
 let n=hi-lo;let mut k:usize=0;
 loop
  invariant lo<=hi<=s.len(),n==hi-lo,k<=n,
   forall|j:int| 0<=j<k ==> !(matches(*a,#[trigger] word.subrange(0,j)) && matches(*b,word.subrange(j,word.len() as int))),
  decreases n-k,
 {
  let mid=lo+k;
  proof {slice_split_r11(s@,lo as int,hi as int,k as int);}
  match search_r11(a,s,lo,mid) {
   Some(left)=>{
    match search_r11(b,s,mid,hi) {
     Some(right)=>{
      proof {
       // did: unfold the fixed model for this constructor obligation.
       reveal_with_fuel(valid_word_r10,2);
       assert(valid_word_r10(Derivation::DCat(k,Box::new(left),Box::new(right)),Re::Cat(Box::new(*a),Box::new(*b)),word));
      }
      return Some(Derivation::DCat(k,Box::new(left),Box::new(right)));
     },
     None=>{},
    }
   },
   None=>{},
  }
  proof {
   assert(!(matches(*a,word.subrange(0,k as int)) && matches(*b,word.subrange(k as int,word.len() as int))));
   // did: prove each quantified index using the fixed previous-state facts.
   assert forall|j:int| 0<=j<=k implies !(matches(*a,#[trigger] word.subrange(0,j)) && matches(*b,word.subrange(j,word.len() as int))) by {
    if j<k {} else {assert(j==k);}
   }
  }
  if k==n {
   proof {
    if matches(Re::Cat(Box::new(*a),Box::new(*b)),word) {
     let j=choose|j:int| 0<=j<=word.len() && matches(*a,#[trigger] word.subrange(0,j)) && matches(*b,word.subrange(j,word.len() as int));
     assert(j<=k);assert(false);
    }
   }
   return None;
  }
  k=k+1;
 }
}
// item: R11.H7v
// pair: R11.H7d
// triv: { None }
#[verifier::loop_isolation(false)]
fn search_star_r11(a:&Re,s:&Vec<char>,lo:usize,hi:usize)->(out:Option<Derivation>)
 requires lo<hi<=s.len(),
 ensures match out {Some(d)=>valid(d,Re::Star(Box::new(*a)),s@,lo as int,hi as int),None=>!matches(Re::Star(Box::new(*a)),s@.subrange(lo as int,hi as int))},
 decreases node_count(Re::Star(Box::new(*a))),hi-lo,0nat,
{
 // did: implement the fixed R11.H7v model and its original domain.

 let ghost word=s@.subrange(lo as int,hi as int);
 let parent=Re::Star(Box::new(copy_re(a)));
 let n=hi-lo;let mut k:usize=1;
 loop
  invariant lo<hi<=s.len(),n==hi-lo,1<=k<=n,
   parent==Re::Star(Box::new(*a)),
   forall|j:int| 0<j<k ==> !(matches(*a,#[trigger] word.subrange(0,j)) && matches(parent,word.subrange(j,word.len() as int))),
  decreases n-k,
 {
  let mid=lo+k;
  proof {slice_split_r11(s@,lo as int,hi as int,k as int);}
  match search_r11(a,s,lo,mid) {
   Some(left)=>{
    match search_r11(&parent,s,mid,hi) {
     Some(right)=>{
      proof {
       // did: unfold the fixed model for this constructor obligation.
       reveal_with_fuel(valid_word_r10,2);
       assert(valid_word_r10(Derivation::DStarCons(k,Box::new(left),Box::new(right)),parent,word));
      }
      return Some(Derivation::DStarCons(k,Box::new(left),Box::new(right)));
     },
     None=>{},
    }
   },
   None=>{},
  }
  proof {
   assert(!(matches(*a,word.subrange(0,k as int)) && matches(parent,word.subrange(k as int,word.len() as int))));
   // did: prove each quantified index using the fixed previous-state facts.
   assert forall|j:int| 0<j<=k implies !(matches(*a,#[trigger] word.subrange(0,j)) && matches(parent,word.subrange(j,word.len() as int))) by {
    if j<k {} else {assert(j==k);}
   }
  }
  if k==n {
   proof {
    if matches(parent,word) {
     let j=choose|j:int| 0<j<=word.len() && matches(*a,#[trigger] word.subrange(0,j)) && matches(parent,word.subrange(j,word.len() as int));
     assert(j<=k);assert(false);
    }
   }
   return None;
  }
  k=k+1;
 }
}
}
use rg_re_a1b::*;
use rg_re_a2::*;
verus! {
#[verifier::opaque]
pub open spec fn residual_r11(r:Re,current:Re,prefix:Seq<char>)->bool {
 forall|tail:Seq<char>| #[trigger] matches(current,tail)==matches(r,prefix+tail)
}
proof fn residual_start_r11(r:Re)
 ensures residual_r11(r,r,Seq::empty()),
{
 // did: unfold the fixed model for this constructor obligation.
 reveal(residual_r11);
 // did: prove each quantified index using the fixed previous-state facts.
 assert forall|tail:Seq<char>| #[trigger] matches(r,tail)==matches(r,Seq::empty()+tail) by {
  assert(Seq::<char>::empty()+tail=~=tail);
 }
}
// item: R11.W3v
proof fn residual_step_r11(r:Re,current:Re,prefix:Seq<char>,c:char)
 requires residual_r11(r,current,prefix),
 ensures residual_r11(r,deriv(current,c),prefix+seq![c]),
{
 // did: unfold the fixed model for this constructor obligation.
 reveal(residual_r11);
 // did: prove each quantified index using the fixed previous-state facts.
 assert forall|tail:Seq<char>| #[trigger] matches(deriv(current,c),tail)==matches(r,(prefix+seq![c])+tail) by {
  lemma_deriv_correct(current,c,tail);
  assert(prefix+(seq![c]+tail)=~=(prefix+seq![c])+tail);
 }
}
proof fn residual_observe_r11(r:Re,current:Re,prefix:Seq<char>)
 requires residual_r11(r,current,prefix),
 ensures nullable(current)==matches(r,prefix),
{
 // did: unfold the fixed model for this constructor obligation.
 reveal(residual_r11);lemma_nullable_correct(current);
 assert(prefix+Seq::<char>::empty()=~=prefix);
}
pub struct PrefixReportR11 {pub accepted:bool,pub trace:Vec<bool>}
// item: R11.H4v
// pair: R11.H4d
// triv: { PrefixReportR11 {accepted:false,trace:Vec::new()} }
fn prefix_matches_r11(r:&Re,s:&Vec<char>)->(out:PrefixReportR11)
 ensures out.accepted==matches(*r,s@),out.trace@.len()==s@.len(),
 forall|j:int| 0<=j<s@.len() ==> out.trace@[j]==matches(*r,s@.take(j+1)),
{
 // did: implement the fixed R11.H4v model and its original domain.

 let mut current=copy_re(r);let mut i:usize=0;let mut trace:Vec<bool>=Vec::new();
 proof {assert(s@.take(0)=~=Seq::<char>::empty());residual_start_r11(*r);}
 while i<s.len()
  invariant i<=s.len(),trace@.len()==i,residual_r11(*r,current,s@.take(i as int)),
   forall|j:int| 0<=j<i ==> trace@[j]==matches(*r,s@.take(j+1)),
  decreases s.len()-i,
 {
  let c=s[i];
  proof {residual_step_r11(*r,current,s@.take(i as int),c);assert(s@.take(i as int)+seq![c]=~=s@.take(i as int+1));}
  current=deriv_exec(&current,c);i=i+1;
  proof {residual_observe_r11(*r,current,s@.take(i as int));}
  let bit=is_nullable(&current);trace.push(bit);
 }
 proof {residual_observe_r11(*r,current,s@.take(i as int));assert(s@.take(i as int)=~=s@);}
 let accepted=is_nullable(&current);PrefixReportR11{accepted,trace}
}
}
verus! {
pub struct ArenaNodeR11 {pub label:char,pub first:Option<usize>,pub second:Option<usize>}
pub struct ArenaR11 {pub nodes:Vec<ArenaNodeR11>}
pub open spec fn targets_valid_r11(node:ArenaNodeR11,len:int)->bool {
 (match node.first {Some(k)=>k<len,None=>true}) && (match node.second {Some(k)=>k<len,None=>true})
}
pub open spec fn arena_valid_r11(arena:ArenaR11)->bool {
 forall|i:int| 0<=i<arena.nodes@.len() ==> targets_valid_r11(#[trigger] arena.nodes@[i],arena.nodes@.len() as int)
}
proof fn targets_monotone_r11(node:ArenaNodeR11,old_len:int,new_len:int)
 requires targets_valid_r11(node,old_len),old_len<=new_len,
 ensures targets_valid_r11(node,new_len),
 {}
fn empty_arena_r11()->(out:ArenaR11)
 ensures arena_valid_r11(out),out.nodes@.len()==0,
 {ArenaR11{nodes:Vec::new()}}
// item: R11.H8v
// triv: { 0 }
fn append_node_r11(arena:&mut ArenaR11,label:char)->(index:usize)
 requires arena_valid_r11(*old(arena)),old(arena).nodes.len()<usize::MAX,
 ensures arena_valid_r11(*final(arena)),
 final(arena).nodes@.len()==old(arena).nodes@.len()+1,
 final(arena).nodes@.take(old(arena).nodes@.len() as int)==old(arena).nodes@,
 index==old(arena).nodes@.len(),
 final(arena).nodes@[index as int].label==label,
 final(arena).nodes@[index as int].first is None,final(arena).nodes@[index as int].second is None,
{
 // did: implement the fixed R11.H8v model and its original domain.

 let ghost before=arena.nodes@;let index=arena.nodes.len();
 arena.nodes.push(ArenaNodeR11{label,first:None,second:None});
 proof {
  assert(arena.nodes@.take(before.len() as int)=~=before);
  // did: prove each quantified index using the fixed previous-state facts.
  assert forall|i:int| 0<=i<arena.nodes@.len() implies targets_valid_r11(#[trigger] arena.nodes@[i],arena.nodes@.len() as int) by {
   if i<index {targets_monotone_r11(before[i],before.len() as int,arena.nodes@.len() as int);}
  }
 }
 index
}
// item: R11.H9v
// triv: { }
fn link_first_r11(arena:&mut ArenaR11,index:usize,target:usize)
 requires arena_valid_r11(*old(arena)),index<old(arena).nodes.len(),target<old(arena).nodes.len(),
 ensures arena_valid_r11(*final(arena)),final(arena).nodes@.len()==old(arena).nodes@.len(),
 final(arena).nodes@[index as int].label==old(arena).nodes@[index as int].label,
 final(arena).nodes@[index as int].first==Some(target),
 final(arena).nodes@[index as int].second==old(arena).nodes@[index as int].second,
 forall|j:int| 0<=j<old(arena).nodes@.len() && j!=index ==> final(arena).nodes@[j]==old(arena).nodes@[j],
{
 // did: implement the fixed R11.H9v model and its original domain.

 let ghost before=arena.nodes@;
 let label=arena.nodes[index].label;let second=arena.nodes[index].second;
 arena.nodes.set(index,ArenaNodeR11{label,first:Some(target),second});
 proof {
  // did: prove each quantified index using the fixed previous-state facts.
  assert forall|j:int| 0<=j<arena.nodes@.len() implies targets_valid_r11(#[trigger] arena.nodes@[j],arena.nodes@.len() as int) by {
   if j==index {} else {assert(arena.nodes@[j]==before[j]);}
  }
 }
}
}
verus! {
// item: R11.T1v
// pair: R11.T1d
// triv: { 0 }
fn wp_index_step_r11(i:usize,len:usize)->(next:usize)
 requires i<len,
 ensures next==i+1,next<=len,
 {
 // did: implement the fixed R11.T1v model and its original domain.
i+1}
}
