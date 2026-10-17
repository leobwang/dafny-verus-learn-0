//! Helpers for the differential oracle: a seeded PRNG, random `Re` generation, printing `Re`
//! in the `regex` crate's syntax, and conversion to the smart-constructor form.
use rg_re_a1::Re;
use rg_re_a4::NormRe;

pub struct Rng(pub u64);

impl Rng {
    pub fn next(&mut self) -> u64 {
        // xorshift64*
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }
    pub fn pick(&mut self, n: u64) -> u64 {
        self.next() % n
    }
}

/// A random regex of depth at most `d` over `alpha`.
pub fn gen_re(rng: &mut Rng, d: u32, alpha: &[char]) -> Re {
    let leaf = d == 0 || rng.pick(4) == 0;
    if leaf {
        match rng.pick(8) {
            0 => Re::Empty,
            1 => Re::Eps,
            _ => Re::Chr(alpha[rng.pick(alpha.len() as u64) as usize]),
        }
    } else {
        match rng.pick(3) {
            0 => Re::Alt(Box::new(gen_re(rng, d - 1, alpha)), Box::new(gen_re(rng, d - 1, alpha))),
            1 => Re::Cat(Box::new(gen_re(rng, d - 1, alpha)), Box::new(gen_re(rng, d - 1, alpha))),
            _ => Re::Star(Box::new(gen_re(rng, d - 1, alpha))),
        }
    }
}

/// `r` in the `regex` crate's syntax; `empty` is the spelling used for the empty language.
pub fn to_regex_syntax(r: &Re, empty: &str) -> String {
    match r {
        Re::Empty => empty.to_string(),
        Re::Eps => "(?:)".to_string(),
        Re::Chr(c) => escape_char(*c),
        Re::Alt(a, b) => format!("(?:{}|{})", to_regex_syntax(a, empty), to_regex_syntax(b, empty)),
        Re::Cat(a, b) => format!("(?:{})(?:{})", to_regex_syntax(a, empty), to_regex_syntax(b, empty)),
        Re::Star(a) => format!("(?:{})*", to_regex_syntax(a, empty)),
    }
}

pub fn escape_char(c: char) -> String {
    let mut b = [0u8; 4];
    let s = c.encode_utf8(&mut b);
    let mut out = String::new();
    for ch in s.chars() {
        if "\\.+*?()|[]{}^$#&-~".contains(ch) {
            out.push('\\');
        }
        out.push(ch);
    }
    out
}

pub fn show(r: &Re) -> String {
    to_regex_syntax(r, "∅")
}

pub fn to_norm(r: &Re) -> NormRe {
    match r {
        Re::Empty => NormRe::empty(),
        Re::Eps => NormRe::eps(),
        Re::Chr(c) => NormRe::chr(*c),
        Re::Alt(a, b) => NormRe::alt(to_norm(a), to_norm(b)),
        Re::Cat(a, b) => NormRe::cat(to_norm(a), to_norm(b)),
        Re::Star(a) => NormRe::star(to_norm(a)),
    }
}

/// Every string over `alpha` of length at most `n`.
pub fn all_strings(alpha: &[char], n: usize) -> Vec<Vec<char>> {
    let mut out = vec![vec![]];
    let mut frontier = vec![vec![]];
    for _ in 0..n {
        let mut next = vec![];
        for s in &frontier {
            for &c in alpha {
                let mut t: Vec<char> = s.clone();
                t.push(c);
                next.push(t);
            }
        }
        out.extend(next.iter().cloned());
        frontier = next;
    }
    out
}
