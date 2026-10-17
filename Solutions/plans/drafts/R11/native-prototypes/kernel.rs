use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a4::*;
verus! {
proof fn sound_word_r11(d:Derivation,r:Re,s:Seq<char>)
 requires valid_word_r10(d,r,s),
 ensures matches(r,s),
 decreases d,
{
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
proof fn complete_word_r11(r:Re,s:Seq<char>)
 requires s.len()<=usize::MAX,matches(r,s),
 ensures exists|d:Derivation| #[trigger] valid_word_r10(d,r,s),
 decreases r,s.len(),
{
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
pub tracked struct CertificateEvidenceR11 {
 pub ghost tree:Derivation,pub ghost pattern:Re,pub ghost word:Seq<char>,
}
proof fn consume_sound_r11(tracked evidence:CertificateEvidenceR11)
 requires valid_word_r10(evidence.tree,evidence.pattern,evidence.word),
 ensures matches(evidence.pattern,evidence.word),
 {sound_word_r11(evidence.tree,evidence.pattern,evidence.word);}
proof fn direct_evidence_r11(r:Re,s:Seq<char>)->(tracked out:CertificateEvidenceR11)
 requires s.len()<=usize::MAX,matches(r,s),
 ensures out.pattern==r,out.word==s,valid_word_r10(out.tree,r,s),
{
 complete_word_r11(r,s);
 let ghost tree=choose|d:Derivation| #[trigger] valid_word_r10(d,r,s);
 CertificateEvidenceR11 {tree,pattern:r,word:s}
}
proof fn slice_split_r11(s:Seq<char>,lo:int,hi:int,k:int)
 requires 0<=lo<=hi<=s.len(),0<=k<=hi-lo,
 ensures s.subrange(lo,hi).take(k)==s.subrange(lo,lo+k),
 s.subrange(lo,hi).skip(k)==s.subrange(lo+k,hi),
{
 assert(s.subrange(lo,hi).take(k)=~=s.subrange(lo,lo+k));
 assert(s.subrange(lo,hi).skip(k)=~=s.subrange(lo+k,hi));
}
fn check_certificate_r11(d:&Derivation,r:&Re,s:&Vec<char>,lo:usize,hi:usize)->(ok:bool)
 ensures ok==valid(*d,*r,s@,lo as int,hi as int),
 decreases d,
{
 if lo>hi || hi>s.len() {return false;}
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
