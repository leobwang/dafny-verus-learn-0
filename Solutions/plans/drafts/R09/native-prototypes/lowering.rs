use vstd::prelude::*;
use vstd::utf8::*;
use vstd::string::{StrSliceExecFns,StringSliceAdditionalSpecFns};
use rg_re_a1::*;
use rg_re_a3::*;
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
