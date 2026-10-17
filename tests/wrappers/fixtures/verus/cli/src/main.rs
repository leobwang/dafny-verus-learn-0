//! Test fixture (tests/wrappers): the invented command line over the verified core
//! (trusted code outside `verus!`). `tally sum <a> <b>`, `tally twice <a>`; anything else
//! prints a usage line on stderr and exits 2.
use tcli::{sum_words, twice_word};

fn word(s: &str) -> Option<u32> {
    s.parse::<u32>().ok()
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let out = match args.iter().map(|s| s.as_str()).collect::<Vec<_>>().as_slice() {
        ["sum", a, b] => word(a).zip(word(b)).map(|(a, b)| sum_words(a, b)),
        ["twice", a] => word(a).map(twice_word),
        _ => None,
    };
    match out {
        Some(v) => println!("{v}"),
        None => {
            eprintln!("usage: tally sum <a> <b> | tally twice <a>");
            std::process::exit(2);
        }
    }
}
