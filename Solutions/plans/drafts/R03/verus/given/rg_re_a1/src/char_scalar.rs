//! PROVIDED scalar-neighbour infrastructure for inclusive interval APIs.
//! No regex theorem or exercise implementation is supplied. Public calls
//! require strict bounds; the surrogate gap is handled by the primitives.
//! The conversion proves the existing vstd UTF-8 contract, adding no axiom.
use vstd::prelude::*;
use vstd::utf8::*;
use vstd::string::{StrSliceExecFns, StringSliceAdditionalSpecFns};
verus! {
fn scalar_char(n: u32) -> (c: char)
    requires is_scalar(n),
    ensures c as u32 == n,
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

// PROVIDED scalar neighbours; strict bounds prevent underflow/overflow.
pub fn char_prev(c: char) -> (p: char)
    requires c > '\0',
    ensures p < c, p as u32 + 1 == c as u32 || (p == '\u{d7ff}' && c == '\u{e000}'),
{
    proof { char_is_scalar(c); }
    let n=c as u32;
    let p=if n == 0xe000 { '\u{d7ff}' } else { scalar_char(n-1) };
    p
}
pub fn char_next(c: char) -> (p: char)
    requires c < '\u{10ffff}',
    ensures c < p, c as u32 + 1 == p as u32 || (c == '\u{d7ff}' && p == '\u{e000}'),
{
    proof { char_is_scalar(c); }
    let n=c as u32;
    let p=if n == 0xd7ff { '\u{e000}' } else { scalar_char(n+1) };
    p
}
}
