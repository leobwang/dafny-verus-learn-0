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
 { #[verifier::proof_note("R11.H2v")] assume(false); }
// item: R11.H3v
// pair: R11.H3d
// uses: tracked
proof fn direct_evidence_r11(r:Re,s:Seq<char>,tracked out:&mut CertificateEvidenceR11)
 requires s.len()<=usize::MAX,matches(r,s),
 ensures final(out).pattern==r,final(out).word==s,valid_word_r10(final(out).tree,r,s),
{ #[verifier::proof_note("R11.H3v")] assume(false); }
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
#[verifier::external_body]
fn check_certificate_r11(d:&Derivation,r:&Re,s:&Vec<char>,lo:usize,hi:usize)->(ok:bool)
 ensures ok==valid(*d,*r,s@,lo as int,hi as int),
 decreases d,
{ unimplemented!() }
}
verus! {

// item: R11.H5v
// pair: R11.H5d
#[verifier::external_body]
fn search_r11(r:&Re,s:&Vec<char>,lo:usize,hi:usize)->(out:Option<Derivation>)
 requires lo<=hi<=s.len(),
 ensures match out {Some(d)=>valid(d,*r,s@,lo as int,hi as int),None=>!matches(*r,s@.subrange(lo as int,hi as int))},
 decreases node_count(*r),hi-lo,1nat,
{ unimplemented!() }
// item: R11.H6v
// pair: R11.H6d
#[verifier::external_body]
#[verifier::loop_isolation(false)]
fn search_cat_r11(a:&Re,b:&Re,s:&Vec<char>,lo:usize,hi:usize)->(out:Option<Derivation>)
 requires lo<=hi<=s.len(),
 ensures match out {Some(d)=>valid(d,Re::Cat(Box::new(*a),Box::new(*b)),s@,lo as int,hi as int),None=>!matches(Re::Cat(Box::new(*a),Box::new(*b)),s@.subrange(lo as int,hi as int))},
 decreases node_count(Re::Cat(Box::new(*a),Box::new(*b))),hi-lo,0nat,
{ unimplemented!() }
// item: R11.H7v
// pair: R11.H7d
#[verifier::external_body]
#[verifier::loop_isolation(false)]
fn search_star_r11(a:&Re,s:&Vec<char>,lo:usize,hi:usize)->(out:Option<Derivation>)
 requires lo<hi<=s.len(),
 ensures match out {Some(d)=>valid(d,Re::Star(Box::new(*a)),s@,lo as int,hi as int),None=>!matches(Re::Star(Box::new(*a)),s@.subrange(lo as int,hi as int))},
 decreases node_count(Re::Star(Box::new(*a))),hi-lo,0nat,
{ unimplemented!() }
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
#[verifier::external_body]
fn prefix_matches_r11(r:&Re,s:&Vec<char>)->(out:PrefixReportR11)
 ensures out.accepted==matches(*r,s@),out.trace@.len()==s@.len(),
 forall|j:int| 0<=j<s@.len() ==> out.trace@[j]==matches(*r,s@.take(j+1)),
{ unimplemented!() }
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
#[verifier::external_body]
fn append_node_r11(arena:&mut ArenaR11,label:char)->(index:usize)
 requires arena_valid_r11(*old(arena)),old(arena).nodes.len()<usize::MAX,
 ensures arena_valid_r11(*final(arena)),
 final(arena).nodes@.len()==old(arena).nodes@.len()+1,
 final(arena).nodes@.take(old(arena).nodes@.len() as int)==old(arena).nodes@,
 index==old(arena).nodes@.len(),
 final(arena).nodes@[index as int].label==label,
 final(arena).nodes@[index as int].first is None,final(arena).nodes@[index as int].second is None,
{ unimplemented!() }
// item: R11.H9v
#[verifier::external_body]
fn link_first_r11(arena:&mut ArenaR11,index:usize,target:usize)
 requires arena_valid_r11(*old(arena)),index<old(arena).nodes.len(),target<old(arena).nodes.len(),
 ensures arena_valid_r11(*final(arena)),final(arena).nodes@.len()==old(arena).nodes@.len(),
 final(arena).nodes@[index as int].label==old(arena).nodes@[index as int].label,
 final(arena).nodes@[index as int].first==Some(target),
 final(arena).nodes@[index as int].second==old(arena).nodes@[index as int].second,
 forall|j:int| 0<=j<old(arena).nodes@.len() && j!=index ==> final(arena).nodes@[j]==old(arena).nodes@[j],
{ unimplemented!() }
}
verus! {
// item: R11.T1v
// pair: R11.T1d
#[verifier::external_body]
fn wp_index_step_r11(i:usize,len:usize)->(next:usize)
 requires i<len,
 ensures next==i+1,next<=len,
 { unimplemented!() }
}
