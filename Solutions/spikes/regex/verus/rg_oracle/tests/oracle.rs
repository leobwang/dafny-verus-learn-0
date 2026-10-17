//! Differential oracle: the spike's verified matchers vs the Rust `regex` crate, anchored
//! whole-string matching. Run: `cargo test --release -p rg_oracle -- --nocapture --test-threads 1`.
//! Each test prints one `ORACLE <name> {json}` line with its counts and examples.
use regex::Regex;
use rg_oracle::*;
use rg_re_a1::Re;

const ALPHA: [char; 3] = ['a', 'b', 'é'];

fn anchored(p: &str) -> String {
    format!(r"\A(?:{})\z", p)
}

fn caret_dollar(p: &str) -> String {
    format!(r"^(?:{})$", p)
}

/// AST mode: random `Re`, printed in regex syntax; every verified matcher against the crate.
#[test]
fn ast_differential() {
    let seeds: Vec<u64> = std::env::var("ORACLE_SEEDS")
        .ok()
        .map(|s| s.split(',').map(|x| x.parse().unwrap()).collect())
        .unwrap_or(vec![1, 2, 3]);
    let per_seed: usize = std::env::var("ORACLE_N").ok().map(|s| s.parse().unwrap()).unwrap_or(1000);
    let strings = all_strings(&ALPHA, 4);
    let mut cmp = 0u64;
    let mut dis = std::collections::BTreeMap::<String, u64>::new();
    let mut examples: Vec<String> = vec![];
    let mut compile_err = 0u64;
    let mut none_results = 0u64;
    for &seed in &seeds {
        let mut rng = Rng(0x9E3779B97F4A7C15 ^ seed.wrapping_mul(0x100000001B3));
        for _ in 0..per_seed {
            let r = gen_re(&mut rng, 4, &ALPHA);
            let pat = to_regex_syntax(&r, "[a&&b]");
            let (rx, rx2) = match (Regex::new(&anchored(&pat)), Regex::new(&caret_dollar(&pat))) {
                (Ok(a), Ok(b)) => (a, b),
                _ => {
                    compile_err += 1;
                    continue;
                }
            };
            for s in &strings {
                let st: String = s.iter().collect();
                let want = rx.is_match(&st);
                let mut got = vec![
                    ("caret_dollar", rx2.is_match(&st)),
                    ("matches_vec", rg_re_a2::deriv_match(&r, s)),
                    ("matches_str", rg_re_a2::matches_str(&r, &st)),
                    ("matches_norm", rg_re_a4::matches_norm(to_norm(&r), s)),
                    ("cert_match", rg_re_a4::cert_match(&r, s)),
                ];
                match rg_rexc::rexc_match(&r, s) {
                    Some(b) => got.push(("rexc_match", b)),
                    None => none_results += 1,
                }
                match rg_arena::arena_match(&r, s) {
                    Some(b) => got.push(("arena_match", b)),
                    None => none_results += 1,
                }
                cmp += 1;
                for (name, b) in got {
                    if b != want {
                        *dis.entry(name.to_string()).or_insert(0) += 1;
                        if examples.len() < 10 {
                            examples.push(format!("{name}: {} on {:?}: regex={want} ours={b}", show(&r), st));
                        }
                    }
                }
            }
        }
    }
    println!(
        "ORACLE ast_differential {{\"seeds\": {:?}, \"regexes_per_seed\": {}, \"strings_per_regex\": {}, \"comparisons\": {}, \"crate_compile_errors\": {}, \"none_results\": {}, \"disagreements\": {:?}, \"examples\": {:?}}}",
        seeds, per_seed, strings.len(), cmp, compile_err, none_results, dis, examples
    );
    assert!(dis.is_empty(), "disagreements: {:?}", examples);
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
enum PatternOutcome {
    BothOkAgree,
    BothOkDisagree,
    OursOkCrateErr,
    OursErrCrateOk,
    BothErr,
}

fn classify_pattern(pat: &str, strings: &[Vec<char>]) -> (PatternOutcome, String) {
    let pv: Vec<char> = pat.chars().collect();
    let ours = rg_ref_r09::parse(&pv);
    let theirs = Regex::new(&anchored(pat));
    match (ours, theirs) {
        (Ok(x), Ok(rx)) => {
            let r = rg_ref_r09::lower_exec(&x);
            for s in strings {
                let st: String = s.iter().collect();
                let a = rg_re_a4::matches_norm(to_norm(&r), s);
                let b = rx.is_match(&st);
                if a != b {
                    return (PatternOutcome::BothOkDisagree, format!("on {:?}: ours={a} regex={b}", st));
                }
            }
            (PatternOutcome::BothOkAgree, String::new())
        },
        (Ok(_), Err(e)) => (PatternOutcome::OursOkCrateErr, format!("{}", e).lines().last().unwrap_or("").to_string()),
        (Err(e), Ok(_)) => (PatternOutcome::OursErrCrateOk, format!("pos {} {:?}", e.pos, kind(&e.kind))),
        (Err(e), Err(ce)) => (PatternOutcome::BothErr, format!("pos {} {:?} | crate: {}", e.pos, kind(&e.kind),
            format!("{}", ce).lines().filter(|l| l.starts_with("error")).next().unwrap_or(""))),
    }
}

fn kind(k: &rg_re_a3::ErrKind) -> &'static str {
    use rg_re_a3::ErrKind::*;
    match k {
        UnexpectedEnd => "UnexpectedEnd",
        UnexpectedChar => "UnexpectedChar",
        UnclosedParen => "UnclosedParen",
        NothingToRepeat => "NothingToRepeat",
        BoundsOrder => "BoundsOrder",
    }
}

/// Concrete-syntax mode: random token strings through the verified parser and the crate.
#[test]
fn syntax_differential() {
    let toks = [
        "a", "b", "é", "a", "b", "|", "(", ")", "*", "+", "?", "{2}", "{0,2}", "{1,}", "{,2}", "\\*", ".",
        "}", "{", "()", "\\a",
    ];
    let strings = all_strings(&ALPHA, 3);
    let mut counts = std::collections::BTreeMap::<String, u64>::new();
    let mut ex = std::collections::BTreeMap::<String, Vec<String>>::new();
    for seed in 1..=3u64 {
        let mut rng = Rng(0xD1B54A32D192ED03 ^ seed.wrapping_mul(0x9E3779B97F4A7C15));
        for _ in 0..3000 {
            let len = 1 + rng.pick(6) as usize;
            let mut p = String::new();
            for _ in 0..len {
                p.push_str(toks[rng.pick(toks.len() as u64) as usize]);
            }
            let (o, detail) = classify_pattern(&p, &strings);
            let key = format!("{:?}", o);
            *counts.entry(key.clone()).or_insert(0) += 1;
            let e = ex.entry(key).or_default();
            if o != PatternOutcome::BothOkAgree && o != PatternOutcome::BothErr && e.len() < 12 {
                e.push(format!("{p:?} {detail}"));
            }
        }
    }
    println!("ORACLE syntax_differential {{\"counts\": {:?}, \"examples\": {:?}}}", counts, ex);
}

/// Directed probes on the deviations a whole-string spec cares about.
#[test]
fn directed_probes() {
    let strings = all_strings(&ALPHA, 3);
    let pats = [
        "", "a|", "|", "()", "(|a)", "a**", "a*?", "a+?", "a??", "a{2}{3}", "a{0}", "a{0,0}", "a{3,2}",
        "a{,2}", "a{2,}", "a{1000}", "a{1001}", "a{4294967295}", "a{4294967296}", "a{99999999999}",
        "a{", "a}", "{", "}", "a{x}", ".", "\\.", "\\d", "\\a", "\\b", "\\", "[a]", "^a", "a$", "(?:a)",
        "é*", "(a*)*", "(a|)*", "((a*)*)*b", "a{2,3}b{0,1}", "a{2}?", "a{1,2}?", "a{1000}{1000}",
        "(a{1000}){30}", "a{65535}", "a{65536}", "a{100000}", "d", "\\d",
    ];
    let mut rows = vec![];
    for p in pats {
        let (o, d) = classify_pattern(p, &strings);
        rows.push(format!("{p:?} => {:?} {d}", o));
    }
    // empty-language spellings and anchoring forms
    let mut extra = vec![];
    for e in ["[a&&b]", r"[^\s\S]", r"[^\x00-\x{10FFFF}]"] {
        extra.push(format!("{e:?} compiles={} matches_empty={}", Regex::new(&anchored(e)).is_ok(),
            Regex::new(&anchored(e)).map(|r| r.is_match("")).unwrap_or(false)));
    }
    for (p, s) in [("a", "a\n"), ("a", "\na"), ("", "\n")] {
        extra.push(format!("pattern {p:?} on {s:?}: \\A..\\z={} ^..$={} ours={}",
            Regex::new(&anchored(p)).unwrap().is_match(s), Regex::new(&caret_dollar(p)).unwrap().is_match(s),
            rg_re_a2::matches_str(&if p.is_empty() { Re::Eps } else { Re::Chr('a') }, s)));
    }
    // escapes outside the test alphabet, the u32-max bound, and the textual anchoring wrapper
    for (p, s) in [("\\d", "1"), ("\\d", "d"), ("a)|(b", "a)|(b"), ("a)|(b", "a")] {
        let pv: Vec<char> = p.chars().collect();
        let ours = rg_ref_r09::parse(&pv).map(|x| rg_re_a2::deriv_match(&rg_ref_r09::lower_exec(&x), &s.chars().collect()));
        extra.push(format!("pattern {p:?} on {s:?}: crate={:?} ours={:?}",
            Regex::new(&anchored(p)).map(|r| r.is_match(s)).map_err(|e| e.to_string().lines().last().unwrap_or("").to_string()),
            ours.map_err(|e| (e.pos, kind(&e.kind)))));
    }
    extra.push(format!("a{{4294967295}} crate error: {:?}", Regex::new(&anchored("a{4294967295}")).err().map(|e| e.to_string())));
    // astral char: one char for both sides
    let astral = "𝄞";
    let r = Re::Chr('𝄞');
    extra.push(format!("astral {astral:?}: regex={} ours_str={} ours_vec={}",
        Regex::new(&anchored(&escape_char('𝄞'))).unwrap().is_match(astral),
        rg_re_a2::matches_str(&r, astral), rg_re_a2::deriv_match(&r, &astral.chars().collect())));
    println!("ORACLE directed_probes {{\"rows\": {:?}, \"extra\": {:?}}}", rows, extra);
}
