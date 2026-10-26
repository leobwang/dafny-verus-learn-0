#!/usr/bin/env bash
# spoiler-guard.sh — PreToolUse hook. Layer 2 of the anti-spoiler guard
# (docs/design/spec4dafny-verus.md §7.2, DESIGN-PROPOSAL.md §13.2, CLAUDE.md
# §Roles). Ported from lean-learn-0's guard and extended for Dafny, Verus and
# Python.
#
# HONESTY CLAUSE. This is a tripwire, not a sandbox: string splitting, or a
# script that opens files itself, gets past it. The instructor contract forbids
# trying (layer 3); OS-level isolation is the sandbox's job. The threat it
# answers is ACCIDENTAL exposure: a tutor, grader or contractor stumbling on
# reference material. It is no defence against an agent that sets out to
# escalate, and the course requires no host hardening for it (design §4: H1
# and H2 are optional). Layer 1, the permission deny rules in
# .claude/settings.json, still holds with every hook switched off.
#
# Wiring. settings.json runs it as `bash "<path>"` (so the file's mode bits
# cannot disarm it) on PreToolUse for Read Grep Glob Bash PowerShell Monitor Edit
# Write MultiEdit NotebookEdit LSP Skill WebFetch WebSearch Workflow ScheduleWakeup,
# the local-file parser mcp__firecrawl__firecrawl_parse, and every verifier MCP or
# wrapper tool: mcp__vcheck__*, mcp__dafny*, mcp__verus*, and plugin-scoped
# mcp__plugin_*{dafny,verus,vcheck}*__*. The logic keys on tool_name, not on
# the matcher, so a looser matcher changes nothing; any other tool passes.
#
# Rules. Every one stands down in authoring mode (below). Each block message
# reads "spoiler-guard: blocked (rule <id>) — <reason>. <legal alternative>".
#   1   Spoiler names. The reference set: Solutions/ (dafny/ verus/ harness/
#       bench/ labs/ pins/ runs/ Challenges/Ref), paper/solutions/,
#       tests/instructor/leak_patterns/, tests/instructor/fixtures/ (the
#       grader calibration fixtures of spec §4.7: a gold fixture is a correct
#       answer set by design; no deny rule covers them, so this rule is their
#       only hard layer, and it matches their path forms only: the bare word
#       fixtures stays open), ~/.cache/dafny-verus-learn-0/ (grader
#       cache, unsealed data, author probe archive). Path-like fields (STRICT:
#       file_path, notebook_path, filePath, path, glob, command, Glob's
#       pattern, LSP's query, every string of a verifier MCP call) also block
#       the bare words Solutions/solutions and any identifier starting with
#       them (the reference crate and package names), leak_patterns,
#       <ID>_solutions and libsolutions. The one exception: on a shell line,
#       the registry's field solutions_policy and its value solutions-first
#       (spec §8.2), exactly and as whole words outside a path, so a skill may
#       extract the field by shell; the 1b build test stays exact, and so do
#       the file, search, LSP and MCP fields. Written content (TEXT: content,
#       new_string, edits[].new_string, new_source, Grep's pattern) blocks only
#       path forms and include/import forms: Dafny `include "…Solutions…"`;
#       Verus `mod solutions`, `use solutions…`, `solutions…::`, `extern crate
#       solutions`, `#[path = "…Solutions…"]`, `include!/include_str!/
#       include_bytes!`, a Cargo `path =`/`git =` dependency or `solutions = {`
#       key; dfyconfig `includes`/`base`/`library`; Python `import solutions`,
#       `from solutions`, import_module/__import__, sys.path or PYTHONPATH
#       naming it; `--extern/--import solutions`, `--library …Solutions…`.
#       Named files are resolved through ~, $HOME, the project dir, `..` and
#       symlinks. A source file (.dfy .rs .py .toml .pth .sh, and a
#       *.dfy.specimen or *.rs.specimen) named by a shell
#       command, an MCP call or the LSP tool has its first 64 KiB scanned for
#       those forms; its include/#[path]/include! targets, and the sibling
#       files a Rust `mod x;` or a Python `import x` pulls in, are resolved
#       through symlinks. Files of this checkout that no study session can
#       write (frozen, guard or build configuration, e.g. a workspace
#       Cargo.toml that excludes the reference) are not scanned, except the
#       cheat corpus tests/corpus/ (rule 2g, below), which is.
#   1b  Spoiler builds. A build or test tool (dafny, cargo, cargo-verus,
#       verus, rustc, vcheck, vaudit, specfreeze, pins.py, firsttry.sh,
#       firsttry.py, test_corpus.py, ci.sh, uv, pip, pytest, make; also run
#       through python or bash) on a line that names the reference;
#       `make paper-solutions`; pytest whose collection root reaches a
#       reference tree; an author-only step (spec §7.4; each also gates
#       itself on CI=true or the three-condition test): *reference_lint* and
#       update_rubric_pins.sh in any mode, pins.py --update or --ref, vcheck
#       --ref, vaudit --ref, specfreeze --pin, firsttry(.sh|.py) --empty-body,
#       test_corpus(.py) --update (also as python3 -m test_corpus),
#       mksandbox-run --author and --attest, get_bench(.sh) and dvl/bench.py
#       --pin and --pin-pool, and the fvh fixture recorder (the module fvh.tools.record in
#       any launcher: python -m, uv run [--directory harness] … -m, a cd into
#       harness/ first; or its file run by python), each option in every
#       spelling argparse accepts (a unique prefix: --re, --u, --p, --em;
#       test_corpus.py, mksandbox-run and bench.py take no abbreviation, and
#       their prefixes are refused all the same); a shell line that sets CI (CI=…,
#       export CI, env CI=…) or a script one-liner that puts it in the
#       environment (os.environ["CI"], {"CI": …}, $ENV{CI}, process.env.CI),
#       the switch those self-gates trust; a verifier MCP call with
#       ref/reference true or a --ref argument, a project outside this
#       checkout, or a target that is not a registry id, a learner or given
#       package, or a checkout path. The learner forms stay open: vcheck
#       [--gate] <unit|file>, vaudit <unit> (its --write FILE is a write
#       target, so expected/ is rule 2f), specfreeze --check/--hash,
#       firsttry.sh <ID> --check/--report/--record/--exit/--lint-hollow,
#       pins.py <ID> and --ci, test_corpus.py --list/--ci/--only <SEL>, and
#       scripts/ci.sh itself: it is the learner's
#       pre-merge check, readable and runnable in study mode, and its
#       reference steps skip themselves outside the author's worktree. Not
#       checked (accepted): CI set where the shell reads it later (an rc or
#       .env file), by read or printf -v, or by a script the line does not
#       name (a .py or .sh file named on the line has its first 64 KiB
#       scanned for the forms above, as for rule 1); there the self-gates
#       are the only layer.
#   1c  Held-out material. unseal, the hidden grader (qgrade, grade_hidden),
#       age/rage decryption, *.tar.age, and the bare word Hidden in any
#       path-like field — not even to exclude it from a search.
#   1d  Whole-tree readers and build outputs. A recursive search (grep -r,
#       egrep/fgrep/zgrep -r, ugrep/ug -r, pcregrep/pcre2grep -r, rg, rga, ag,
#       ack, git grep, the Grep tool with no path), a recursive diff (diff or
#       colordiff with -r/--recursive or a cluster holding r: every operand),
#       a find or fd feeding -exec/-x/-X/xargs/cpio/ctags -L/cscope -i or
#       substituted into a command ($(find …), `find …`), `git ls-files |
#       xargs`, a recursive tags or cross-reference index (ctags -R or
#       --recurse, cscope -R: it copies the definition lines of every file it
#       walks into ./tags or cscope.out), an archive or recursive copy
#       (tar zip 7z pax cp -r rsync -r scp -r ditto), or a glob, whose reach
#       takes in a reference tree. Build outputs count as reach: a recursive
#       reader rooted at or inside target/, build/, .verus-log/,
#       .verus-solver-log/, __pycache__/, TestResults/ or a Dafny *-py/,
#       *-go/ or *-java/ output dir; a direct read of
#       target/**/*.{vir,rlib,rmeta} (an exported .vir is a statement leak,
#       Δ26), of target/verus-partial/, of .verus-log/ or .verus-solver-log/
#       files, or of anything under build/. git show/log -p/diff <rev>/
#       format-patch/archive/bundle/cat-file -p need a learner pathspec,
#       because history carries the reference trees too. A path word's
#       leading ~, ~+, $HOME, $PWD, $CLAUDE_PROJECT_DIR (bare or braced) is
#       expanded, and $(pwd), `pwd`, $(realpath .), $(readlink -f .) and
#       $(git rev-parse --show-toplevel) count as $PWD or the checkout root,
#       for reach, globs and every write rule alike.
#   1e  Other sessions' Claude Code state: under ~/.claude (or
#       $CLAUDE_CONFIG_DIR) projects/ (transcripts *.jsonl, session dirs with
#       subagent transcripts and tool results, other projects' memory),
#       file-history/, history.jsonl, paste-cache/, debug/, sessions/, jobs/,
#       todos/, backups/; ~/.claude.json (it keeps each project's last
#       first prompt); /tmp/claude-<uid>/ (other sessions' scratchpads and
#       task output); the Claude Code credentials file (~/.claude/ or
#       $CLAUDE_CONFIG_DIR/.credentials.json); and the sandbox's run state
#       under $XDG_RUNTIME_DIR/dvl-runs/ (relay sockets, credential snapshots,
#       a per-run CA; DV4) — EXCEPT this session's own: its transcript and session dir
#       (session_id and transcript_path from the hook input), its scratch dir
#       (scratchpad_dir, or /tmp/claude-<uid>/<project slug>/<session_id>),
#       and this project's own memory dir. Named paths, and recursive readers
#       whose reach takes them in.
#   1f  Agent and container tripwire. As a command: docker, docker-compose,
#       dockerd*, podman, nerdctl, lxc, lxd, incus, ctr, buildah, runc,
#       crictl, opencode, codex, sudo, su, pkexec, doas, runuser, sg, newgrp;
#       anywhere on a shell line: DOCKER_HOST=, docker.sock (and podman or
#       containerd sockets), --unix-socket, http+unix:, the Python docker SDK
#       (import docker, docker.from_env), the local-assistant skill (its
#       script, or the Skill tool calling it); a nested `claude` unless it is
#       the course's tool-less policy form (`-p`/`--print` with `--tools ""`
#       and `--strict-mcp-config`, no `--mcp-config`) or --version/--help/
#       `auth status`. Container and agent runs go only through
#       scripts/mksandbox-run, scripts/contract_local.sh or the fvh harness.
#       Workflow and ScheduleWakeup calls are refused in study mode: the
#       session-hygiene contract forbids workflows and background jobs.
#       Those entry points are course files (frozen or guard class), which
#       this hook does not content-scan, so naming them passes; that only
#       they start containers, agents or sudo is checked at build time
#       instead (scripts/ci.sh's static job, scripts/check_single_route.py),
#       since narrowing the scan here would refuse ci.sh and the fixtures.
#   2   Learner-owned files: dafny/{Q,R}/, verus/{q,r}/, harness/{q,r}/ (minus
#       the solo gates), specimens/ (their header slots) and dafny/checks/
#       (their value-predict slots), slots/, paper/*_answers.tex, research/,
#       bench/local/{q,r}/**/{tasks,answers}/, tools/. Writes need the path on
#       .claude/state/contract-allowlist (written by /contract), lexically and
#       symlink-resolved. Bash writes count, best effort (below). The run
#       records research/runs/** and the ledger anchors
#       research/ledger-heads.jsonl are written only by fvh and
#       scripts/mksandbox-run: an allowlist line naming them is rejected
#       (rule 2), as /contract rejects it.
#   2c  Contract active (the allowlist is non-empty): no instructor/ writes
#       (OD13), no WebFetch/WebSearch, no reads of bench/public/**/answers/;
#       no git command that rewrites tracked files across the tree (checkout
#       or switch to a revision, reset --hard/--merge/--keep, stash other than
#       list/show, merge, pull, rebase, cherry-pick, revert, am), and no
#       patch or git apply whose input the hook cannot see (a pipe); and no
#       other agent or fetch: scripts/contract_local.sh,
#       scripts/mksandbox-run (except --check-access, --dry-run and the
#       read-only --build-verify, which prints a manifest and starts nothing),
#       scripts/get_bench.sh or dvl/bench.py (a network fetch, like the web
#       tools), the fvh subcommands that call a model (run, resume,
#       contract-local) and fvh unseal (it writes a sealed stratum's
#       cards; rule 1c refuses it in every study session too, and while a
#       contract runs this rule is checked first, so its reason is the one
#       given) in any launcher (fvh, python -m fvh, uv run … -m fvh, after
#       a cd), all named anywhere on the line.
#   2s  Solo work: Challenges/, agents/, Q's gate (harness/q/*/gate/), R16's
#       trust-report (a path under verus/r/, harness/r/ or dafny/R/ whose name
#       holds trust-report or trust_report) — never writable, allowlist or
#       not; an allowlist line naming them is itself rejected. R has no
#       harness gate class of its own: its gate is R16's trust-report (design
#       W11), so harness/r/**/gate/ is learner-owned like the rest of
#       harness/r/, matching design rule 2s and check_course_map.py's Q_GATE.
#   2f  Frozen: */given/** (dafny/given/, verus/given/), harness/fvh/**,
#       harness/tests/** (the author's acceptance tests for learner Python),
#       paper/rubrics/** (what /grade-paper grades against), expected/**,
#       challenge statements (Challenges/**/*Statement*), the benchmark
#       manifest bench/manifest.toml and the third-party sets
#       bench/public/** (scripts/get_bench.sh installs them); never
#       writable, an allowlist line naming them is rejected; checked before
#       2s and 2.
#   2g  The guard, the build and the files that steer a session: everything
#       under .claude/ (hooks, settings{,.local}.json, skills with CORE.md,
#       agents, commands) except .claude/state/, of which only the mode file;
#       tests/ (the guard's, the checker's and the grader's fixtures; the
#       grader's, tests/instructor/fixtures/, are also reference-class, so
#       rule 1 names them first, a write included; and the
#       cheat corpus tests/corpus/: learner-readable fixtures, run through
#       scripts/test_corpus.py, written only in authoring mode; unlike the
#       rest of 2g its files ARE content-scanned under rule 1, like learner
#       files, because its fixtures are adversarial on purpose, so its names
#       avoid the rule-1/1c words (no Solutions, solutions*, Hidden,
#       leak_patterns or unseal* in a path or a crate or package name) and
#       none of its includes, imports or dependencies reaches a reference
#       tree);
#       CLAUDE.md and CLAUDE.local.md at any depth (the learner writes the
#       contract block by hand, never Claude); MODULES.toml, scripts/, sandbox/,
#       .vscode/settings.json, .mcp.json, .toolchain/, dafny/options/,
#       .config/dotnet-tools.json, and at
#       any depth every dfyconfig.toml, Cargo.toml, Cargo.lock, .cargo/,
#       build.rs, rust-toolchain{,.toml}, pyproject.toml, uv.lock, conftest.py,
#       pytest.ini, setup.cfg, setup.py, tox.ini, sitecustomize.py,
#       usercustomize.py and *.pth;
#       Claude Code's user-level settings (~/.claude/settings{,.local}.json,
#       $CLAUDE_CONFIG_DIR/settings*.json, /etc/claude-code/; ~/.claude.json
#       is rule 1e);
#       mode bits included (chmod/chown). The checkout root itself, and any
#       directory that holds it, is 2g as a write target: rm -rf ., chmod -R
#       ., git checkout/restore ., git clean with no pathspec, find . -delete,
#       an archive extracted there or a directory's contents copied there
#       (a single file copied or moved there is judged by its own name). An
#       allowlist line naming a 2g path is rejected, as /contract does.
#       Also verifier poisoning on a shell
#       line: VERUS_Z3_PATH=, VERUS_EXTRA_ARGS=, RUSTC_WRAPPER=,
#       RUSTFLAGS=…verus_only/--cfg, a PATH= prefix on a verifier command,
#       Dafny --plugin, and --solver-path other than the pinned bundled Z3.
#       For the file-editing tools 2f, 2s and 2g are checked before rule 1's
#       content scan, so a guard-config edit reports 2g.
#
# Bash write detection (best effort), in order: drop heredoc bodies; join
# backslash-newline continuations (the line-level patterns of rules 1b, 1c,
# 1f and 2g test the joined line too); drop fd duplications; cut at && || ;
# | & ` ( ) $( (a cut inside a quoted string is undone for the fragment
# that opened the quote); peel wrappers (env command
# nice timeout stdbuf nohup time exec xargs eval, bash/sh -c, VAR=val, npx/
# bunx/uvx/pipx run, uv run [--directory D], if/then/do/while); check every
# existing path word and glob expansion; check redirect targets; per-command
# handlers: cd/pushd/popd (below), tee, sed/perl/ruby -i, cp/install/
# rsync/ln/scp/mv (into a directory: each source by its own name),
# rm/rmdir/unlink/shred/truncate, dd of=, chmod/chown/chgrp/chattr/setfacl,
# git checkout/switch/restore/rm/mv/clean, archive extraction (tar x with
# -C/--directory, unzip -d, 7z x/e -o: the members named, else the target
# directory itself), patch (its file, -o, -r, or every name its diff
# carries, read from -i, a < file or a heredoc, under -d), git apply/am (the
# names in the patch files, -p1 by default), ex/ed/vi/vim/nvim file
# operands, find -delete and find/fd -exec of a writing command (each start
# directory); and for script one-liners (python node ruby perl deno bun) that
# call a file-writing function, every protected path named anywhere in the
# text. Globs among write targets are expanded.
#
# The shell's directory, for reads and writes alike: cd DIR and pushd DIR move
# it; a bare cd goes to $HOME; cd -, cd ~-, popd, pushd with no directory or
# a stack rotation (+N/-N), and a directory the hook cannot resolve ($OLDPWD,
# a custom VAR, an unexpanded $(…)) reset it to the project root, the
# conservative choice (a recursive read of the root takes in the reference). A
# subshell — ( … ) or $( … ) — restores it at the closing parenthesis. A cd is
# followed whether or not it runs (inside if/case/||, or to a missing
# directory): accepted. A shell inside a reference tree is refused (rule 1)
# with "cd back to" the project root, unless the root itself lies in one (a
# checkout under an author lane's scratch): then the message says to run the
# session from a checkout outside (D20: a study clone under /tmp/dvl0-study-…/).
#
# Write gaps (accepted; a tripwire, not a sandbox). None of these is checked:
#   - whole-tree git with no contract active: checkout/switch <branch>,
#     reset --hard, stash, merge, pull, rebase, cherry-pick, revert (a
#     learner may ask Claude to switch branches or pull course updates; under
#     a contract they are rule 2c); git worktree and submodule updates;
#   - patch, git apply and git am fed on a pipe with no contract (the diff is
#     not on the line); a patch file is read to its first 1 MiB only;
#   - archive tools not parsed: cpio -i, ar x, jar x, pax -r, python -m
#     zipfile/tarfile, and decompressors writing beside their input
#     (gunzip, xz -d, zstd -d);
#   - writes inside a script file or an interpreter the hook does not parse
#     (awk system(), emacs --batch, a python script on disk), and writes fed
#     through xargs (find … | xargs rm);
#   - path spellings through other variables ($OLDPWD, ~-, a custom VAR),
#     parameter operators (${PWD%/*}, ${PWD:-x}) and command substitutions
#     other than the ones listed under rule 1d, as path words (as a cd
#     target they reset the shell's directory to the root, above);
#   - a find -exec of a wrapper script, and mkdir/touch (no content).
#
# False-positive policy (study mode). Block when an input NAMES a spoiler —
# those strings have no study-mode use — and otherwise stay out of the way.
#   allowed  vcheck on registry units and scratch files, cargo verus verify of
#            learner crates, uv run --directory harness pytest, reading
#            chapters, exercises and given layers, git status/log/diff with
#            pathspecs, searches scoped to named directories, instructor/ writes
#            (no contract active), allowlisted contract edits, /contract writing
#            and emptying its allowlist, this session's own scratchpad, tool
#            results and project memory, mksandbox-run/contract_local.sh/fvh,
#            scripts/ci.sh (the learner's pre-merge check), the learner forms
#            of vaudit/specfreeze/firsttry/pins.py (rule 1b), and reading and
#            running the cheat corpus (tests/corpus/, scripts/test_corpus.py
#            --list/--ci/--only; its --update is author-only, rule 1b).
#   costs    (accepted) a shell line or path field that merely mentions the
#            word solutions or Solutions (a commit message, `grep solutions
#            docs/`) is refused — rephrase, or use the Grep tool, whose
#            pattern is content (only the registry's solutions_policy and
#            solutions-first pass, on a shell line that runs no build or test
#            tool); a shell line, path field, written text or Grep pattern
#            that spells the path tests/instructor/fixtures is refused, a
#            commit message included — say "the calibration fixtures";
#            `ls *` at the root is refused (the glob
#            expands into Solutions/); only registry targets may be built
#            through MCP; a shell line naming *reference_lint* or
#            update_rubric_pins, or an author-only option after the name of
#            vcheck, vaudit, specfreeze, firsttry or pins.py, is refused even
#            to read it or search for it (`cat scripts/update_rubric_pins.sh`,
#            `grep -n 'vcheck --ref' docs/`) — use the Read or Grep tool; a shell
#            line that sets CI, and a one-liner that sets it in the
#            environment, is refused — CI is set only by the human or the
#            author's CI run (search for it with the Grep tool); reading build
#            outputs (target/*.vir, .verus-log/) is refused — read the raw_dir
#            that scripts/vcheck --json prints; a one-liner that writes
#            anywhere and names a protected path is refused — read and write in
#            separate commands; a heredoc whose text names a container tool
#            socket or the docker SDK is refused — use the Write tool for prose;
#            every sudo is refused (rule 1f) — privileged commands are the
#            human's; pytest from the checkout root is refused (it would
#            collect Solutions/harness) — run it from harness/ (uv run
#            --directory harness pytest); while a contract runs, instructor/
#            writes and the web tools are refused, even for a coach session
#            running beside it (the allowlist is the only role signal), and so
#            are branch switches, resets, stashes, merges and piped patches, and
#            any line naming contract_local.sh, get_bench.sh, bench.py,
#            mksandbox-run (other than --check-access, --dry-run or
#            --build-verify) or fvh
#            run/resume/contract-local, even to read one (use the Read tool); a
#            shell line naming fvh.tools.record or mksandbox-run with --author
#            or --attest is refused in study mode, as the other author-only
#            forms are;
#            whole-checkout writes (rm -rf ., git checkout ., git clean with no
#            pathspec, chmod -R ., an archive unpacked at the root) are refused
#            — name the directory you mean; an archive unpacked into a learner,
#            frozen or guard directory is refused even under a contract —
#            unpack into instructor/scratch/ or /tmp; a file copied into any
#            directory is judged by its own name (a Cargo.toml copied into
#            scratch is a crate manifest, rule 2g); ex/ed/vim on a learner file
#            is refused even to print it — use cat or the Read tool.
#   exposed  names only, accepted: a language server indexes the reference
#            tree, so a workspace-symbol search can list reference declaration
#            NAMES (never bodies); `ls -R`, `tree`, or `find`/`fd` without
#            -exec from the root lists reference FILE names, as the Glob tool
#            does. Reference-only helpers carry neutral names.
#   readers  (accepted; not checked) tree walkers the hook does not parse,
#            each unlikely as an accident or printing fragments only: ugrep
#            or ug with no FILE operand (it recurses only when its stdin is a
#            terminal); difft and GUI diff or merge tools (meld, kdiff3) given
#            two directories; linters and formatters that walk a tree and
#            print diagnostics, snippets or diffs (ruff check ., black --diff
#            ., flake8, pylint, mypy, semgrep, ast-grep, codespell) — run them
#            from harness/ or on named directories; gtags and jar c (an index
#            or archive the hook does not parse); xargs fed a saved or
#            hand-built file list (xargs -a LIST cat, ls -R | xargs cat); and
#            walks inside a script or an interpreter (os.walk, glob('**'),
#            python -m zipfile -c), as the honesty clause says.
#
# Authoring mode: .claude/state/mode containing "authoring" stands the guard
# down entirely, but only where git confirms all three: inside a checkout, a
# LINKED worktree (git-dir != git-common-dir), and HEAD not on a leobwang-*
# branch. Anywhere else the file is ignored and the guard stays armed;
# scripts/course_mode.sh refuses to write it there. The hook never trusts the
# flag file alone.
#
# Exit codes: 0 = allow (normal permission flow), 2 = block (stderr shown to
# Claude). Works without jq (grep/sed fallback parser; SPOILER_GUARD_NO_JQ=1
# forces it for testing). Never blocks on its own parse failure: empty or
# malformed input exits 0, which is safe only because layer 1 still holds.

set -u

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
ROOT="${ROOT%/}"
[ -n "$ROOT" ] || ROOT=/
MODE_FILE="$ROOT/.claude/state/mode"
ALLOWLIST="$ROOT/.claude/state/contract-allowlist"
COURSE=dafny-verus-learn-0
LEARNER_PREFIX=leobwang-

# --- Authoring mode: guardrails suspended while the course is being built. ---
authoring() {
  [ -f "$MODE_FILE" ] && grep -q "authoring" "$MODE_FILE" 2>/dev/null || return 1
  local gd cdir
  gd="$(git -C "$ROOT" rev-parse --git-dir 2>/dev/null)" || return 1        # not git: stay armed
  cdir="$(git -C "$ROOT" rev-parse --git-common-dir 2>/dev/null)" || return 1
  gd="$(cd "$ROOT" && cd "$gd" && pwd -P)" && cdir="$(cd "$ROOT" && cd "$cdir" && pwd -P)" || return 1
  [ "$gd" != "$cdir" ] || return 1                 # the primary worktree
  case "$(git -C "$ROOT" symbolic-ref --short -q HEAD 2>/dev/null)" in
    "$LEARNER_PREFIX"*) return 1 ;;                # a learner branch
  esac
  return 0
}
authoring && exit 0

INPUT="$(cat 2>/dev/null || true)"
[ -z "$INPUT" ] && exit 0

# --- Parse: tool name, cwd, session, and the fields each rule reads. ---------
#   STRICT  path-like fields (bare words block)   TEXT  written content
#   FPATHS  files a tool reads or writes           SPATHS  Grep/Glob search dir
TOOL_NAME="" CWD="" CMD="" FPATHS="" SPATHS="" STRICT="" TEXT="" PROJ="" TARGETS=""
SESSION_ID="" TRANSCRIPT="" SCRATCH="" URL="" SKILL="" REFFLAG=""
if [ -z "${SPOILER_GUARD_NO_JQ:-}" ] && command -v jq >/dev/null 2>&1; then
  eval "$(printf '%s' "$INPUT" | jq -r '
    def s: map(strings | select(. != ""));
    (.tool_name // "" | tostring) as $t
    | (.tool_input | if type == "object" then . else {} end) as $i
    | ($t | test("^mcp__(vcheck__|dafny|verus|plugin_.*(dafny|verus|vcheck))")) as $v
    | @sh "TOOL_NAME=\($t)",
      @sh "CWD=\(.cwd // "" | tostring)",
      @sh "SESSION_ID=\(.session_id // "" | tostring)",
      @sh "TRANSCRIPT=\(.transcript_path // "" | tostring)",
      @sh "SCRATCH=\(.scratchpad_dir // "" | tostring)",
      @sh "CMD=\($i.command // "" | tostring)",
      @sh "FPATHS=\([$i.file_path, $i.notebook_path, $i.filePath] | s | join("\n"))",
      @sh "SPATHS=\([$i.path] | s | join("\n"))",
      @sh "URL=\($i.url // ($i.ws | if type == "object" then .url else null end) // "" | tostring)",
      @sh "SKILL=\($i.skill // "" | tostring)",
      @sh "PROJ=\([$i.project, $i.project_path, $i.project_root, $i.manifest_path, $i.root, $i.workspace] | s | join("\n"))",
      @sh "TARGETS=\([$i.target, ($i.targets | arrays | .[]), $i.unit, ($i.units | arrays | .[]), $i.module, $i.package, $i.crate] | s | join("\n"))",
      @sh "REFFLAG=\(if ($i.ref == true or $i.reference == true) then "1" else "" end)",
      @sh "STRICT=\(if $v then [$i | .. ] | s
                    else [$i.file_path, $i.notebook_path, $i.filePath, $i.path, $i.glob,
                          $i.command, (if $t == "Glob" then $i.pattern else empty end),
                          (if $t == "LSP" then $i.query else empty end)] | s end
                    | join("\n"))",
      @sh "TEXT=\([$i.content, $i.new_string, $i.new_source,
                   ($i.edits | arrays | .[] | objects | .new_string),
                   (if $t == "Grep" then $i.pattern else empty end)] | s | join("\n"))"
  ' 2>/dev/null)" 2>/dev/null
else
  # POSIX sed: a newline in a replacement is backslash-newline and a tab is a
  # literal tab (GNU sed's \n and \t there are extensions BSD sed lacks).
  unescape() { sed -e $'s/\\\\n/\\\n/g' -e $'s/\\\\t/\t/g' -e 's/\\"/"/g' -e 's#\\/#/#g' -e 's/\\\\/\\/g'; }
  jvals() {   # every JSON string value of the given keys, roughly unescaped
    local k
    for k in "$@"; do
      printf '%s' "$INPUT" | grep -oE "\"$k\"[[:space:]]*:[[:space:]]*\"([^\"\\\\]|\\\\.)*\"" \
        | sed -E 's/^"[^"]*"[[:space:]]*:[[:space:]]*"//; s/"$//'
    done | unescape
  }
  TOOL_NAME="$(jvals tool_name | head -n 1)"
  CWD="$(jvals cwd | head -n 1)"
  SESSION_ID="$(jvals session_id | head -n 1)"
  TRANSCRIPT="$(jvals transcript_path | head -n 1)"
  SCRATCH="$(jvals scratchpad_dir | head -n 1)"
  CMD="$(jvals command)"
  FPATHS="$(jvals file_path notebook_path filePath)"
  SPATHS="$(jvals path)"
  URL="$(jvals url | head -n 1)"
  SKILL="$(jvals skill | head -n 1)"
  PROJ="$(jvals project project_path project_root manifest_path root workspace)"
  TARGETS="$(jvals target unit module package crate)"
  printf '%s' "$INPUT" | grep -Eq '"ref(erence)?"[[:space:]]*:[[:space:]]*true' && REFFLAG=1
  case "$TOOL_NAME" in
    mcp__vcheck__*|mcp__dafny*|mcp__verus*|mcp__plugin_*dafny*|mcp__plugin_*verus*|mcp__plugin_*vcheck*)
      # every string value: keys (a string followed by :) and the hook's own
      # top-level values are dropped
      STRICT="$(printf '%s' "$INPUT" | grep -oE '"([^"\\]|\\.)*"[[:space:]]*:?' | grep -v ':$' \
        | sed -E 's/^"//; s/"[[:space:]]*$//' | unescape \
        | grep -vxF -e "$TOOL_NAME" -e "${CWD:-/}" -e "${SESSION_ID:-/}" -e "${TRANSCRIPT:-/}" \
                    -e "${SCRATCH:-/}" -e PreToolUse)" ;;
    Glob) STRICT="$(jvals file_path notebook_path path glob command pattern)" ;;
    LSP)  STRICT="$(jvals filePath query)" ;;
    *)    STRICT="$(jvals file_path notebook_path filePath path glob command)" ;;
  esac
  TEXT="$(jvals content new_string new_source)"
  [ "$TOOL_NAME" = Grep ] && TEXT="$TEXT
$(jvals pattern)"
fi

# The shell line with every backslash-newline continuation removed, as the
# shell reads it: `scripts/vcheck Q04 \⏎ --ref` is one command. The
# line-level patterns test this form; bash_checks joins its own copy after
# dropping heredoc bodies.
CMDJ="${CMD//\\$'\n'/}"
IS_SHELL="" IS_MCP=""
case "$TOOL_NAME" in
  # Monitor runs a shell command (its command field, as Bash's) or opens a
  # WebSocket (ws.url, judged below as WebFetch's url is): DV6 fix round.
  Bash|PowerShell|Monitor) IS_SHELL=1 ;;
  Read|Grep|Glob|Edit|Write|MultiEdit|NotebookEdit|LSP|Skill|WebFetch|WebSearch|Workflow|ScheduleWakeup|mcp__firecrawl__firecrawl_parse) ;;
  mcp__vcheck__*|mcp__dafny*|mcp__verus*|mcp__plugin_*dafny*|mcp__plugin_*verus*|mcp__plugin_*vcheck*) IS_MCP=1 ;;
  *) exit 0 ;;
esac
[ -n "$CWD" ] || CWD="$ROOT"
RROOT="$(cd "$ROOT" 2>/dev/null && pwd -P || printf '%s' "$ROOT")"

block() { echo "spoiler-guard: blocked $*" >&2; exit 2; }

R1_MSG="(rule 1) — this names the reference material (Solutions/ or a solutions crate or package, paper/solutions/, tests/instructor/leak_patterns/, the grader calibration fixtures in tests/instructor/fixtures/, ~/.cache/$COURSE/, or an author lane's scratch under /tmp/dvl0-dv…/). Claude never reads, includes, imports, builds or searches it, in any role (CLAUDE.md §Roles). If the learner wants the answer, name the reference path in prose and stop; probes include or import the given layers and the learner's own files only."
R1D_HINT="Name the directories you mean (grep -rn PAT dafny/Q verus/q docs), give git a pathspec (git show HEAD -- dafny verus docs), or list files with git ls-files dafny verus docs."
R1E_HINT="This session's own scratchpad, tool results and this project's memory directory stay readable; other sessions' transcripts, file history and scratch directories are never read from a course session. For scratch space, use this session's scratchpad or instructor/scratch/."
R1B_CI="(rule 1b) — this line sets CI, the switch the author-only steps' self-gates trust (spec §7.4: a self-check is not a guard). Run scripts/ci.sh and the learner forms of the tools as they are: outside the author's worktree their reference steps skip themselves. CI is set only by the human or the author's CI run; to search for it, use the Grep tool."
R2C_MSG="a /contract session is active (.claude/state/contract-allowlist is non-empty), and a contractor never writes instructor/, never browses the web and never opens public benchmark answers (OD13). Finish or abandon the contract first: its close-out empties the allowlist."

# --- Patterns. B/E are identifier boundaries (POSIX ERE has no \b). ----------
B='(^|[^A-Za-z0-9_])'
E='([^A-Za-z0-9_]|$)'
# Path forms of the reference set (TEXT and STRICT).
RX_PATH="${B}Solutions/|/Solutions${E}|paper/solutions${E}|tests/instructor/leak_patterns|tests/instructor/fixtures${E}|\.cache/${COURSE}|XDG_CACHE_HOME\}?/${COURSE}|${COURSE}/unsealed"
# Include and import forms, per language (TEXT; also the 64 KiB file scan).
RX_IMP_DFY='^[[:space:]]*include[[:space:]]+"[^"]*[Ss]olutions|^[[:space:]]*import[[:space:]]+(opened[[:space:]]+)?[Ss]olutions'
RX_IMP_RS="^[[:space:]]*(pub(\([^)]*\))?[[:space:]]+)?mod[[:space:]]+[Ss]olutions|${B}use[[:space:]]+(::)?[Ss]olutions|${B}extern[[:space:]]+crate[[:space:]]+[Ss]olutions|${B}[Ss]olutions[A-Za-z0-9_]*::|#\[path[[:space:]]*=[[:space:]]*\"[^\"]*[Ss]olutions|${B}include(_str|_bytes)?![[:space:]]*\([^)]*[Ss]olutions"
RX_IMP_TOML='^[[:space:]]*[Ss]olutions[A-Za-z0-9_-]*[[:space:]]*=[[:space:]]*\{|(path|git|base|includes|library)[[:space:]]*=[[:space:]]*\[?[^]#]*[Ss]olutions|dependencies\.[Ss]olutions'
RX_IMP_PY="^[[:space:]]*(from|import)[[:space:]]+[Ss]olutions|(import_module|__import__)\\([[:space:]]*[\"'][Ss]olutions|sys\\.path.*[Ss]olutions|PYTHONPATH.*[Ss]olutions"
RX_IMP_CLI="--(extern|import)[[:space:]=]+[Ss]olutions|--library[[:space:]=]+[^[:space:]]*[Ss]olutions"
RX_TEXT="${RX_PATH}|${RX_IMP_DFY}|${RX_IMP_RS}|${RX_IMP_TOML}|${RX_IMP_PY}|${RX_IMP_CLI}"
# Bare words (STRICT only): the reference root, crate and package names.
RX_WORD="${B}([Ss]olutions|leak_patterns)|${B}[RQ][0-9][0-9]_solutions${E}|${B}libsolutions"
# The registry's solutions_policy field and its solutions-first value (spec
# §8.2) are the only spellings that start with the bare word and still pass,
# on a shell line only: exactly, as whole words, never as a path component.
RX_VOCAB="(^|[^A-Za-z0-9_/-])(solutions_policy|solutions-first)([^A-Za-z0-9_/-]|\$)"
# An import of anything named solutions… on a shell line (python -c, a Dafny
# or Rust one-liner) stays exact: the exemption above is for reading the
# registry field, never for importing a module that carries its name.
RX_IMP_SH="${B}(import|from)[[:space:]]+(opened[[:space:]]+)?[Ss]olutions|(import_module|__import__)\\([[:space:]]*[\"'][Ss]olutions"
# /tmp/dvl0-dv… is an author lane's scratch (CLAUDE.md: /tmp/dvl0-<phase>-<lane>/, every
# phase a dv… name), which can hold reference twins and sealed truth until it is
# archived and removed: a tripwire, never OS isolation (DV5c fix round).
RX_SPOIL_DIR="(/Solutions|/paper/solutions|/tests/instructor/leak_patterns|/tests/instructor/fixtures|/Hidden|/\\.cache/${COURSE}|/${COURSE}/unsealed|/tmp/dvl0-dv[0-9a-z]+-[^/]+)(/|\$)"
RX_HIDDEN="${B}unseal|${B}r?age[[:space:]]+(-[A-Za-z]*d[A-Za-z]*|--decrypt)|\\.tar\\.age${E}|${B}(qgrade|grade_hidden|q_grade_hidden)${E}|${B}Hidden${E}"
# A build or test tool in command position: at a line start or after ; & | ( ` ' " $(,
# behind VAR=val prefixes and simple wrappers (python and bash among them, so
# `python3 scripts/firsttry.py` counts), possibly invoked by its path.
CMDPOS="(^|[;&|(\`'\"]|\\\$\\()[[:space:]]*(([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*|env|nohup|nice|time|exec|command|timeout[[:space:]]+[0-9.]+[smhd]?|python[0-9.]*|bash|sh)[[:space:]]+)*([^[:space:];&|()'\"]*/)?"
RX_BUILD_TOOL="${CMDPOS}(dafny|cargo|cargo-verus|verus|rust_verify|rustc|vcheck|vaudit|specfreeze|pins\\.py|firsttry\\.sh|firsttry\\.py|test_corpus\\.py|ci\\.sh|challenge_gate\\.sh|pytest|py\\.test|uv|uvx|pip3?|make|just)([[:space:]]|\$)|-m[[:space:]]+pytest${E}"
RX_REFNAME="${B}[Ss]olutions|paper/solutions|${B}libsolutions"
# Author-only steps (spec §7.4, Δ85): each gates itself on CI=true or the
# three-condition test, and the hook refuses the line as well. An option
# matches in every spelling argparse accepts: any unique prefix (pins.py --u
# and --re, vcheck/vaudit --re, specfreeze --p, firsttry --em). test_corpus.py
# sets allow_abbrev=False, so only --update works; its --u… prefixes are
# refused anyway, should the parser ever accept them, and so is the module
# form (python3 -m test_corpus). scripts/ci.sh is not here: it is the
# learner's pre-merge check (rule 1b, header).
RX_AUTHOR="${B}(q_)?reference_lint|${B}update_rubric_pins${E}"
RX_AUTHOR+="|${B}pins\\.py${E}[^;&|]*--(u[a-z]*|ref?)${E}"
RX_AUTHOR+="|${B}(vcheck|vaudit)${E}[^;&|]*--re(f|ference)?${E}"
RX_AUTHOR+="|${B}specfreeze${E}[^;&|]*--p(i|in)?${E}"
RX_AUTHOR+="|${B}firsttry(\\.py|\\.sh)?${E}[^;&|]*--em[a-z-]*${E}"
RX_AUTHOR+="|${B}test_corpus(\\.py)?${E}[^;&|]*--u[a-z]*${E}"
# DV4: the sandbox's author forms, the benchmark pin and the fvh fixture recorder.
RX_AUTHOR+="|${B}mksandbox-run${E}[^;&|]*--a(u|t)[a-z]*${E}"
RX_AUTHOR+="|${B}(get_bench(\\.sh)?|bench\\.py)${E}[^;&|]*--p(i|in)?${E}"
RX_AUTHOR+="|${B}fvh\\.tools\\.record${E}|${B}python[0-9.]*${E}[^;&|]*fvh/tools/record\\.py${E}"
# Rule 2c (DV4): another agent, a container run or a network fetch while a
# contract runs; mksandbox-run's --check-access, --dry-run and --build-verify
# (DV5c: it prints one command's manifest and starts no container) stay open.
# fvh unseal (DV5d) is on the list: it writes a sealed stratum's cards.
RX_2C_AGENT="${B}contract_local(\\.sh)?${E}|${B}get_bench(\\.sh)?${E}|${B}bench\\.py${E}"
RX_2C_AGENT+="|(^|[[:space:];&|(/'\"])(-m[[:space:]]*)?fvh[[:space:]]+(-[^[:space:]]+[[:space:]]+)*(run|resume|contract-local|unseal)([[:space:];&|)'\"]|\$)"
RX_1F_ANY="${B}DOCKER_HOST=|docker\\.sock|podman\\.sock|containerd\\.sock|--(abstract-)?unix-socket|http\\+unix:|${B}local-assistant${E}|${B}(import|from)[[:space:]]+docker${E}|${B}docker\\.(from_env|DockerClient|APIClient)${E}"
RX_1F_SCRIPT="${RX_1F_ANY}|(^|[;&|[:space:]])(docker|podman|nerdctl|opencode|codex|sudo|pkexec|doas)[[:space:]]"
RX_POISON="${B}(VERUS_Z3_PATH|VERUS_EXTRA_ARGS|RUSTC_WRAPPER|RUSTC_WORKSPACE_WRAPPER)=|${B}(RUSTFLAGS|CARGO_ENCODED_RUSTFLAGS)=[^;&|]*(verus_only|--cfg)|(^|[[:space:]])--plugin([=[:space:]]|$)"
RX_CONSUMER='xargs|while[[:space:]]+read|-exec|\$\([[:space:]]*(git[[:space:]]+ls-|find[[:space:]])|`[[:space:]]*(git[[:space:]]+ls-|find[[:space:]])'
RX_CONSUMER+="|${B}(cpio|pax)${E}|${B}tar${E}[^|;&]*(-T|--files-from)|${B}zip${E}[^|;&]*-@"
RX_CONSUMER+="|${B}ctags[[:space:]]([^|;&]*[[:space:]])?-L|${B}cscope[[:space:]]([^|;&]*[[:space:]])?-i"   # an index fed a file list
RX_SCRIPT='(^|[^A-Za-z0-9_.-])(python[0-9.]*|node|ruby|perl|deno|bun)[[:space:]]'
_Q="'\""                                  # both quote characters, for brackets
# A script one-liner, or a script file a shell line names, that puts CI in
# the environment (rule 1b): CI=… (a shell assignment in a file, a Python
# keyword), os.environ["CI"] = … / {"CI": …} / setdefault("CI", …) /
# putenv("CI", …), perl's $ENV{CI} = …, node's process.env.CI = …. Reading
# it (os.environ.get("CI", "x"), print(os.environ["CI"])) passes. On the
# shell line itself, assignments (CI=…, export CI, env CI=…) are
# check_assign's.
RX_CI_SCRIPT="${B}CI[[:space:]]*:?=[^=]|[${_Q}]CI[${_Q}][[:space:]]*(\\][[:space:]]*=[^=]|:)|${B}(setdefault|putenv|setenv)[[:space:]]*\\([[:space:]]*[${_Q}]CI[${_Q}]|\\{[${_Q}]?CI[${_Q}]?\\}[[:space:]]*=[^=]|\\.CI[[:space:]]*=[^=]"
RX_SCRIPT_WRITES="open\\([^)]*[${_Q}][wax+]|${B}open[[:space:]]*\\(?[^;)]*,[[:space:]]*[${_Q}](\\+<|\\+?>)"
RX_SCRIPT_WRITES+="|${B}os\\.(remove|unlink|rename|renames|replace|truncate|chmod|lchmod|chown|lchown|symlink|link|rmdir|removedirs|utime|open)[[:space:]]*\\("
RX_SCRIPT_WRITES+="|${B}shutil\\.(copy|copy2|copyfile|copytree|copymode|copystat|copyfileobj|move|rmtree|chown)[[:space:]]*\\("
RX_SCRIPT_WRITES+="|\\.(write_text|write_bytes|unlink|rename|touch|chmod|lchmod|symlink_to|hardlink_to|rmdir|writeFileSync|appendFileSync|renameSync|unlinkSync|rmSync|copyFileSync|cpSync|chmodSync|chownSync|truncateSync|createWriteStream)[[:space:]]*\\("
RX_SCRIPT_WRITES+="|${B}fs(\\.promises)?\\.(writeFile|appendFile|rename|unlink|rm|rmdir|copyFile|cp|chmod|chown|truncate|symlink|link|createWriteStream|open)(Sync)?[[:space:]]*\\("
RX_SCRIPT_WRITES+="|${B}(File|IO)\\.(write|binwrite|delete|unlink|rename|chmod|chown|truncate|symlink|link)${E}|${B}FileUtils\\."
RX_SCRIPT_WRITES+="|${B}(unlink|rename|chmod|chown|truncate|symlink|link)[[:space:]]*[(${_Q}\$@0-9]"
# Protected paths a writing one-liner may name (each is then classified).
_P="[^[:space:]'\"\\\\)]*"
RX_PROT="(dafny/${_P}|verus/${_P}|harness/${_P}|slots/${_P}|research/${_P}|bench/local/${_P}|tools/${_P}|paper/[^[:space:]'\"/\\\\)]*_answers\\.tex|paper/rubrics/${_P}|Challenges/${_P}|agents/${_P}|expected/${_P}|instructor/${_P}|scripts/${_P}|sandbox/${_P}|\\.claude/(hooks|state|skills|agents|commands)/${_P}|specimens/${_P}|tests/${_P}|[^[:space:]'\"/]*CLAUDE(\\.local)?\\.md|(~|\\\$\\{?HOME\\}?|/[^[:space:]'\"]*)?/?\\.claude/settings(\\.local)?\\.json|\\.claude\\.json|/etc/claude-code/${_P}|MODULES\\.toml|\\.mcp\\.json|\\.vscode/settings\\.json|\\.cargo/${_P}|[^[:space:]'\"/]*(dfyconfig\\.toml|Cargo\\.(toml|lock)|build\\.rs|rust-toolchain(\\.toml)?|pyproject\\.toml|uv\\.lock|conftest\\.py))"
SCAN_EXT='\.(dfy|rs|py|toml|pth|sh|bash)(\.specimen)?$'

# unvocab TEXT: TEXT with the exempt registry words removed (see RX_VOCAB).
unvocab() {
  case "$1" in
    *solutions_policy*|*solutions-first*) printf '%s\n' "$1" | sed -E -e ':a' -e "s#${RX_VOCAB}#\\1\\3#" -e 'ta' ;;
    *) printf '%s\n' "$1" ;;
  esac
}

# --- Path helpers (set globals; no subshell, so block() exits the hook). ------
# normpath P → NORM: P (absolute) with ., .. and // folded; symlinks untouched.
normpath() {
  local IFS=/ c
  local -a parts out=()
  read -ra parts <<<"$1"
  for c in "${parts[@]}"; do
    case "$c" in
      ''|.) ;;
      ..) if [ "${BASH_VERSINFO[0]}" -ge 4 ]; then
            [ "${#out[@]}" -gt 0 ] && out=("${out[@]:0:${#out[@]}-1}")
          elif [ "${#out[@]}" -gt 0 ]; then
            unset "out[${#out[@]}-1]"   # bash 3.2 joins a slice of an array into one word under IFS=/
          fi ;;
      *) out+=("$c") ;;
    esac
  done
  if [ "${#out[@]}" -eq 0 ]; then NORM=/; else NORM="$(printf '/%s' "${out[@]}")"; fi
}
# xvar P → XV: P with a leading directory spelling expanded: ~, ~+ (the
# shell's working directory), $HOME, $PWD, $CLAUDE_PROJECT_DIR (bare or in
# braces). bash_checks has already rewritten $(pwd), `pwd`, $(realpath .),
# $(readlink -f .) and $(git rev-parse --show-toplevel) to $PWD or
# $CLAUDE_PROJECT_DIR. SHDIR is the shell's working directory as cd moved it,
# which a -C or --directory option does not change.
xvar() {
  local p="$1" d="${SHDIR:-${CWD:-/}}"
  case "$p" in
    '~') p="$HOME" ;;
    '~/'*) p="$HOME/${p#'~/'}" ;;
    '~+'|'~+/'*) p="$d${p#'~+'}" ;;
    '$HOME'|'$HOME/'*) p="$HOME${p#'$HOME'}" ;;
    '${HOME}'*) p="$HOME${p#'${HOME}'}" ;;
    '$PWD'|'$PWD/'*) p="$d${p#'$PWD'}" ;;
    '${PWD}'*) p="$d${p#'${PWD}'}" ;;
    '$CLAUDE_PROJECT_DIR'|'$CLAUDE_PROJECT_DIR/'*) p="$ROOT${p#'$CLAUDE_PROJECT_DIR'}" ;;
    '${CLAUDE_PROJECT_DIR}'*) p="$ROOT${p#'${CLAUDE_PROJECT_DIR}'}" ;;
  esac
  XV="$p"
}
# abspath P [BASE] → ABS: P made absolute against BASE (default CWD), with the
# xvar spellings expanded.
abspath() {
  local p b="${2:-$CWD}"
  xvar "$1"; p="$XV"
  case "$p" in /*) ;; *) p="$b/$p" ;; esac
  normpath "$p"; ABS="$NORM"
}
# realp P → REAL: P with symlinks resolved (P itself when that fails).
# Each attempt's output is kept only when it succeeds: a realpath without -m
# may print before it fails (busybox), and `a || b` would join both outputs.
realp() {
  REAL="$(realpath -m -- "$1" 2>/dev/null)" && [ -n "$REAL" ] && return 0
  REAL="$(readlink -f -- "$1" 2>/dev/null)" && [ -n "$REAL" ] && return 0
  REAL="$(realpath_m "$1")" && [ -n "$REAL" ] && return 0
  REAL="$1"
}
# realpath_m P: `realpath -m` where coreutils is absent (macOS): the longest
# existing prefix of P with its symlinks resolved, then the rest of P as written.
realpath_m() {
  local p="$1" rest="" d
  case "$p" in /*) ;; *) p="$PWD/$p" ;; esac
  while [ ! -e "$p" ] && [ ! -L "$p" ] && [ "$p" != / ] && [ -n "$p" ]; do
    rest="/${p##*/}$rest"; p="${p%/*}"
  done
  [ -n "$p" ] || p=/
  if [ -d "$p" ]; then d="$(cd -P -- "$p" 2>/dev/null && pwd -P)" || return 1
  else d="$(readlink -f -- "$p" 2>/dev/null)" || d="$p"; fi
  printf '%s\n' "${d%/}$rest"
}
in_spoiler() { [[ "$1" =~ $RX_SPOIL_DIR ]]; }
rel_of() {   # X → REL: X relative to the checkout (empty when outside it)
  REL=""
  case "$1" in "$ROOT"/*) REL="${1#"$ROOT"/}" ;; "$RROOT"/*) REL="${1#"$RROOT"/}" ;; esac
}

# --- Session identity (rule 1e). ---------------------------------------------
uid="$(id -u 2>/dev/null || echo 0)"
SID="$SESSION_ID"
[ -n "$SID" ] || SID="${CLAUDE_CODE_SESSION_ID:-}"
SLUG=""
case "$TRANSCRIPT" in
  */projects/*/*.jsonl)
    SLUG="${TRANSCRIPT%/*}"; SLUG="${SLUG##*/}"
    if [ -z "$SID" ]; then SID="${TRANSCRIPT##*/}"; SID="${SID%.jsonl}"; fi ;;
esac
[[ "$SID" =~ ^[A-Za-z0-9_-]+$ ]] || SID=""
[[ "$SLUG" =~ ^[A-Za-z0-9_.-]+$ ]] && [ "$SLUG" != . ] && [ "$SLUG" != .. ] \
  || SLUG="$(printf '%s' "$ROOT" | sed 's/[^A-Za-z0-9]/-/g')"
abspath "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" /; CH="$ABS"
TMPROOTS=() OWNTMP=()
if [ -n "$SCRATCH" ]; then
  abspath "$SCRATCH" /; OWNTMP+=("${ABS%/*}")
  t="${ABS%/*}"; t="${t%/*}"; t="${t%/*}"
  [ -n "$t" ] && [ "$t" != / ] && TMPROOTS+=("$t")
fi
for t in "${TMPDIR:-/tmp}" /tmp; do abspath "$t/claude-$uid" /; TMPROOTS+=("$ABS"); done
case "${OSTYPE:-}" in darwin*) TMPROOTS+=("/private/tmp/claude-$uid") ;; esac   # macOS: /tmp is /private/tmp
if [ -n "$SID" ]; then for t in "${TMPROOTS[@]}"; do OWNTMP+=("$t/$SLUG/$SID"); done; fi
STATE_DIRS=(file-history paste-cache debug sessions jobs todos backups)
# The sandbox's run state (DV4): relay sockets, credential snapshots, a CA key;
# and fvh's per-call state of policy runs (fvh.batch), which holds a derived
# credentials snapshot while a call runs (DV5c fix round).
RUNSTATE=()
for t in "${XDG_RUNTIME_DIR:-/run/user/$uid}" "/run/user/$uid"; do
  for d in dvl-runs fvh-claude-state fvh-qwen-state; do abspath "$t/$d" /; RUNSTATE+=("$ABS"); done
done
CREDS=("$CH/.credentials.json" "$HOME/.claude/.credentials.json")

# in_state X: is X another session's Claude Code state (rule 1e)?
in_state() {
  local x="$1" rel first t o
  case "$x/" in "$ROOT"/*|"$RROOT"/*) return 1 ;; esac   # the checkout itself, wherever it lives
  [ "$x" = "$CH/history.jsonl" ] && return 0
  case "$x" in "$HOME"/.claude.json|"$HOME"/.claude.json.*) return 0 ;; esac   # holds each project's lastSessionFirstPrompt
  for t in "${CREDS[@]}"; do [ "$x" = "$t" ] && return 0; done                 # the subscription's tokens
  for t in "${RUNSTATE[@]}"; do case "$x" in "$t"|"$t"/*) return 0 ;; esac; done   # sandbox run state
  case "$x" in
    "$CH"/projects/*)
      rel="${x#"$CH"/projects/}"
      case "$rel" in "$SLUG"|"$SLUG"/memory|"$SLUG"/memory/*) return 1 ;; esac
      if [ -n "$SID" ]; then
        case "$rel" in "$SLUG/$SID.jsonl"|"$SLUG/$SID"|"$SLUG/$SID"/*) return 1 ;; esac
      fi
      return 0 ;;
  esac
  for t in "${STATE_DIRS[@]}"; do
    case "$x" in
      "$CH/$t"/*)
        rel="${x#"$CH/$t"/}"; first="${rel%%/*}"
        if [ -n "$SID" ]; then case "$first" in "$SID"|"$SID".*|"$SID"-*) return 1 ;; esac; fi
        return 0 ;;
    esac
  done
  for t in "${TMPROOTS[@]}"; do
    case "$x" in
      "$t"/*)
        for o in ${OWNTMP[@]+"${OWNTMP[@]}"}; do case "$x" in "$o"|"$o"/*) return 1 ;; esac; done
        [ "${x#"$t"/}" = "$SLUG" ] && return 1      # naming this project's own scratch root
        return 0 ;;
    esac
  done
  return 1
}
# reaches_state D: does a recursive read of D take in another session's state?
reaches_state() {
  local d="$1" p o
  in_state "$d" && return 0
  for o in ${OWNTMP[@]+"${OWNTMP[@]}"}; do case "$d" in "$o"|"$o"/*) return 1 ;; esac; done
  case "$d" in "$CH/projects/$SLUG/memory"|"$CH/projects/$SLUG/memory"/*) return 1 ;; esac
  [ "$d" = "$CH/projects/$SLUG" ] && return 0
  for p in "${TMPROOTS[@]}"; do [ "$d" = "$p/$SLUG" ] && return 0; done
  for p in "$CH/projects" "$CH/history.jsonl" "$HOME/.claude.json" "${STATE_DIRS[@]/#/$CH/}" "${TMPROOTS[@]}" \
           "${CREDS[@]}" "${RUNSTATE[@]}"; do
    case "$p/" in "$d"/*) return 0 ;; esac
  done
  return 1
}
# state_words TEXT: path-like words of TEXT that name Claude Code state.
state_words() {
  printf '%s\n' "$1" | grep -oE "[^[:space:]'\"=;|&<>()\`,]+" \
    | grep -E "\\.claude|claude-[0-9]|history\\.jsonl|dvl-runs|fvh-claude-state|fvh-qwen-state|$(printf '%s' "$CH" | sed 's/[]\/$*.^[]/\\&/g')"
}

# --- Reach (rule 1d) and build outputs. --------------------------------------
build_out() {   # D: rooted at or inside a build-output directory of the checkout?
  rel_of "$1"; [ -n "$REL" ] || return 1
  case "$REL" in build|build/*) return 0 ;; esac
  case "/$REL/" in */target/*|*/.verus-log/*|*/.verus-solver-log/*|*/__pycache__/*|*/TestResults/*|*-py/*|*-go/*|*-java/*) return 0 ;; esac
  return 1
}
artifact() {    # X: a compiled or logged build output read directly?
  rel_of "$1"; [ -n "$REL" ] || return 1
  [ -d "$1" ] && return 1
  case "$REL" in build/*) return 0 ;; esac
  case "/$REL" in */.verus-log/*|*/.verus-solver-log/*|*/target/*.vir|*/target/*.rlib|*/target/*.rmeta|*/target/verus-partial/*) return 0 ;; esac
  return 1
}
# reaches D: does a recursive read of D take in a reference tree?
reaches() {
  local d="$1" r
  in_spoiler "$d" && return 0
  [ "$d" = / ] && return 0
  for r in "$ROOT" "$RROOT" "$HOME/.cache/$COURSE"; do
    case "$r/" in "$d"/*) return 0 ;; esac
  done
  build_out "$d" && return 0
  # The calibration fixtures' directory has a generic name (a pytest
  # fixtures/ directory is no reference): it counts only where it sits as
  # tests/instructor/fixtures, lexically or through a symlink.
  for r in fixtures instructor/fixtures tests/instructor/fixtures; do
    [ -d "$d/$r" ] || continue
    in_spoiler "$d/$r" && return 0
    in_spoiler "$(realp "$d/$r"; printf '%s' "$REAL")" && return 0
  done
  [ -d "$d/Solutions" ] || [ -d "$d/solutions" ] || [ -d "$d/Hidden" ] || [ -d "$d/leak_patterns" ] \
    || [ -d "$d/instructor/leak_patterns" ] || [ -d "$d/paper/solutions" ] \
    || [ -d "$d/tests/instructor/leak_patterns" ]
}
bench_answers() {   # X: under bench/public/**/answers/ (rule 2c, contract active)
  case "$1/" in "$ROOT"/bench/public/*/answers/*|"$RROOT"/bench/public/*/answers/*) return 0 ;; esac
  return 1
}
reaches_bench() {   # D: does a recursive read of D take in public benchmark answers?
  local d="$1" b
  for b in "$ROOT/bench/public" "$RROOT/bench/public"; do
    case "$b/" in "$d"/*) return 0 ;; esac
    case "$d/" in
      "$b"/*) bench_answers "$d" && return 0
              [ -n "$(find "$d" -type d -name answers -print -quit 2>/dev/null)" ] && return 0 ;;
    esac
  done
  return 1
}
trusted() {   # F: course infrastructure in this checkout (frozen or guard/build
              # configuration, which no study session can write), exempt from content scans
  rel_of "$1"; [ -n "$REL" ] || return 1
  # The cheat corpus is 2g for writes, but its fixtures are adversarial on
  # purpose and a study session runs them: scanned like learner files.
  case "$REL" in tests/corpus/*) return 1 ;; esac
  class_of "$REL"
  case "$CLASS" in 2f|2g) return 0 ;; esac
  return 1
}
# scan_file FILE NAME: rule 1 (and 1f for scripts) on a source file a tool is
# pointed at: include/import forms and path forms in its first 64 KiB, and its
# include / #[path] / include! targets resolved through symlinks.
scan_file() {
  local f="$1" name="$2" txt inc d c
  [ -f "$f" ] || return 0
  [[ "$f" =~ $SCAN_EXT ]] || return 0
  trusted "$f" && return 0
  txt="$(head -c 65536 -- "$f" 2>/dev/null)" || return 0
  if printf '%s\n' "$txt" | grep -Eq "$RX_TEXT"; then
    block "(rule 1) — '$name' includes, imports or names the reference material; checking, running or reading it prints reference code. Probe with a file that imports the given layers or the learner's own files only."
  fi
  d="${f%/*}"
  while IFS= read -r inc; do
    [ -n "$inc" ] || continue
    abspath "$inc" "$d"; realp "$ABS"
    if in_spoiler "$ABS" || in_spoiler "$REAL"; then
      block "(rule 1) — '$name' includes '$inc', which resolves into a reference tree. Probe with a file that includes the given layers or the learner's own files only."
    fi
  done <<EOF
$(printf '%s\n' "$txt" | grep -oE 'include[[:space:]]+"[^"]+"|#\[path[[:space:]]*=[[:space:]]*"[^"]+"|include(_str|_bytes)?![[:space:]]*\([[:space:]]*"[^"]+"' | sed -E 's/.*"([^"]+)"$/\1/')
EOF
  # Sibling modules a Rust `mod x;` or a Python `import x` pulls in: a
  # scratch symlink named like a module is the same read as an include.
  case "$f" in
    *.rs|*.py)
      while IFS= read -r inc; do
        [ -n "$inc" ] || continue
        for c in "$d/$inc.rs" "$d/$inc/mod.rs" "$d/$inc.py" "$d/$inc/__init__.py"; do
          [ -e "$c" ] || [ -L "$c" ] || continue
          realp "$c"
          in_spoiler "$REAL" && block "(rule 1) — '$name' pulls in module '$inc' ($c), which resolves into a reference tree. Probe with modules that are the learner's own or the given layers."
        done
      done <<EOF
$(printf '%s\n' "$txt" | grep -oE '^[[:space:]]*((pub(\([^)]*\))?[[:space:]]+)?mod[[:space:]]+[A-Za-z_][A-Za-z0-9_]*[[:space:]]*;|(from|import)[[:space:]]+[A-Za-z_][A-Za-z0-9_]*)' | sed -E 's/;$//; s/[[:space:]]+$//; s/.*[[:space:]]//')
EOF
      ;;
  esac
  case "$f" in
    *.py|*.sh|*.bash)
      if printf '%s\n' "$txt" | grep -Eq "$RX_1F_SCRIPT"; then
        block "(rule 1f) — '$name' runs a container tool, an agent CLI, sudo or the docker SDK. Container and agent runs go only through scripts/mksandbox-run, scripts/contract_local.sh or the fvh harness."
      fi
      if printf '%s\n' "$txt" | grep -Eq "$RX_CI_SCRIPT"; then
        block "(rule 1b) — '$name' sets CI, the switch the author-only steps' self-gates trust (spec §7.4). Run scripts/ci.sh and the learner forms of the tools as they are; CI is set only by the human or the author's CI run."
      fi ;;
  esac
  return 0
}
# check_named P BASE [scan]: rules 1, 1d, 1e and 2c on a file or dir a tool names.
check_named() {
  local x
  abspath "$1" "$2"; realp "$ABS"
  for x in "$ABS" "$REAL"; do
    in_spoiler "$x" && block "$R1_MSG"
    in_state "$x" && block "(rule 1e) — '$1' is another Claude Code session's state (a transcript, session directory, file history or scratch directory). $R1E_HINT"
    artifact "$x" && block "(rule 1d) — '$1' is a build output (compiled or logged verifier state: target/*.vir, *.rlib, *.rmeta, .verus-log/, build/), which can hold the reference's statements. Re-run scripts/vcheck on the learner's own unit and read the raw_dir it prints (--json)."
    if [ -n "$CONTRACT" ] && bench_answers "$x"; then block "(rule 2c) — '$1' is a public benchmark answer, and $R2C_MSG"; fi
  done
  [ "${3:-}" = scan ] && scan_file "$REAL" "$1"
  return 0
}

# --- Rule 2 helpers. ----------------------------------------------------------
CONTRACT=""
[ -f "$ALLOWLIST" ] && grep -q '[^[:space:]]' "$ALLOWLIST" 2>/dev/null && CONTRACT=1
# class_of REL → CLASS: 2f 2s 2g allowlist instructor learner none
class_of() {
  local r="$1" b="${1##*/}"
  CLASS=none
  if [[ "$r" =~ ^[^/]+/given(/|$) ]]; then CLASS=2f; return; fi
  case "$r" in
    harness/fvh|harness/fvh/*|harness/tests|harness/tests/*|paper/rubrics|paper/rubrics/*|expected|expected/*|bench/manifest.toml|bench/public|bench/public/*)
      CLASS=2f; return ;;
  esac
  if [[ "$r" =~ ^Challenges/(.*/)?[^/]*[Ss]tatement ]]; then CLASS=2f; return; fi
  case "$r" in Challenges|Challenges/*|agents|agents/*) CLASS=2s; return ;; esac
  # Q's gate, and R16's trust-report in any of the R trees (the Dafny R tree
  # is dafny/R/, upper case). R has no harness gate class of its own: its
  # gate is R16's trust-report (design W11, rule 2s), so a harness/r/**/gate
  # path is learner-owned unless its name carries trust-report.
  if [[ "$r" =~ ^harness/q/[^/]+/gate(/|\.py$|$) ]] \
     || [[ "$r" =~ ^(verus/r|harness/r|dafny/R)/(.*/)?[^/]*trust[-_]report ]]; then CLASS=2s; return; fi
  case "$r" in
    .claude/state/contract-allowlist) CLASS=allowlist; return ;;
    .claude/state|.claude/state/mode) CLASS=2g; return ;;
    .claude/state/*) ;;              # other machine-local state: by its name below
    .claude|.claude/*|tests|tests/*|MODULES.toml|scripts|scripts/*|sandbox|sandbox/*|.vscode/settings.json|.mcp.json|.toolchain|.toolchain/*|dafny/options|dafny/options/*|.config/dotnet-tools.json)
      CLASS=2g; return ;;
  esac
  case "$b" in
    CLAUDE.md|CLAUDE.local.md|dfyconfig.toml|Cargo.toml|Cargo.lock|build.rs|rust-toolchain|rust-toolchain.toml|pyproject.toml|uv.lock|conftest.py|pytest.ini|setup.cfg|setup.py|tox.ini|sitecustomize.py|usercustomize.py|*.pth)
      CLASS=2g; return ;;
  esac
  case "/$r/" in */.cargo/*) CLASS=2g; return ;; esac
  case "$r" in dafny|verus|harness|paper) CLASS=2f; return ;; esac   # they hold given layers, tests or rubrics
  case "$r" in instructor|instructor/*) CLASS=instructor; return ;; esac
  case "$r" in
    dafny/Q|dafny/Q/*|dafny/R|dafny/R/*|verus/q|verus/q/*|verus/r|verus/r/*|harness/q|harness/q/*|harness/r|harness/r/*|specimens|specimens/*|dafny/checks|dafny/checks/*|slots|slots/*|research|research/*|tools|tools/*|bench|bench/local|bench/local/q|bench/local/r|paper/*_answers.tex)
      CLASS=learner; return ;;
  esac
  if [[ "$r" =~ ^bench/local/[qr]/(.*/)?(tasks|answers)(/|$) ]]; then CLASS=learner; return; fi
}
allowlisted() {   # REL — is REL a line of the contract allowlist?
  local line
  [ -f "$ALLOWLIST" ] || return 1
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    line="${line#./}"; line="${line#"$ROOT"/}"
    [ "$line" = "$1" ] && return 0
  done <"$ALLOWLIST"
  return 1
}
# allowlist_lines TEXT: rules 2s, 2f and 2g on the lines (Write/Edit) or
# words (a shell command) being written into the contract allowlist. 2g
# lines unlock nothing (2g writes are refused anyway); rejecting them keeps
# the hook in step with /contract's own validation.
allowlist_lines() {
  local w where="a contract allowlist may not name"
  [ -n "$IS_SHELL" ] && where="this command writes the contract allowlist and names"
  while IFS= read -r w; do
    w="${w//\"/}"; w="${w//\'/}"
    case "$w" in ''|-*) continue ;; esac
    abspath "$w" "$ROOT"; rel_of "$ABS"; [ -n "$REL" ] || continue
    case "$REL" in .claude/state|.claude/state/contract-allowlist) continue ;; esac   # the allowlist's own path
    case "$REL" in
      research/runs|research/runs/*|research/ledger-heads.jsonl)
        block "(rule 2) — $where '$w', a run record or the ledger anchors (research/runs/, research/ledger-heads.jsonl): only fvh and scripts/mksandbox-run write them, so no contract lists them (a reset budget must be a visible edit by the learner, never a contractor's)." ;;
    esac
    class_of "$REL"
    case "$CLASS" in
      2f) [ -n "$IS_SHELL" ] && block "(rule 2f) — $where a frozen path ('$w': given layers, harness/fvh, harness/tests, a rubric, expected/, a challenge statement, the benchmark manifest or a public set); no contract edits them. If that path is only read elsewhere on the line, write the allowlist in a command of its own."
          block "(rule 2f) — $where a frozen path ('$w': given layers, harness/fvh, harness/tests, a rubric, expected/, a challenge statement, the benchmark manifest or a public set): every learner shares them, so no contract edits them." ;;
      2s) [ -n "$IS_SHELL" ] && block "(rule 2s) — $where a solo path ('$w': Challenges/, agents/, Q's gate or R16's trust-report); solo work has no contractor. If that path is only read elsewhere on the line, write the allowlist in a command of its own."
          block "(rule 2s) — $where a solo path ('$w': Challenges/, agents/, Q's gate or R16's trust-report): solo work has no contractor." ;;
      2g) [ -n "$IS_SHELL" ] && block "(rule 2g) — $where guard or build configuration ('$w': .claude/, tests/, scripts/, sandbox/, CLAUDE.md, the registry, a project, crate, toolchain or Python build file); no contract edits it. If that path is only read elsewhere on the line, write the allowlist in a command of its own."
          block "(rule 2g) — $where guard or build configuration ('$w': .claude/, tests/, scripts/, sandbox/, CLAUDE.md, the registry, a project, crate, toolchain or Python build file): no contract edits it." ;;
    esac
  done <<EOF
$(if [ -n "$IS_SHELL" ]; then printf '%s\n' "$1" | grep -oE "[^[:space:]'\";|&<>()\`=\\\\]+"; else printf '%s\n' "$1"; fi)
EOF
  return 0
}
classify_write() {   # REL TEXT [early] — rules 2f, 2s, 2g, 2c, 2 on one repo-relative target
  local rel="$1"
  class_of "$rel"
  case "$CLASS" in
    2f) block "(rule 2f) — '$rel' is frozen (a given layer, harness/fvh, the acceptance tests in harness/tests, a rubric, expected/, a challenge statement, or the benchmark manifest and public sets, which scripts/get_bench.sh installs). Claude never writes it in study mode, allowlist or not, and /contract never lists it. Work in the module's own files." ;;
    2s) block "(rule 2s) — '$rel' is solo work (Challenges/, agents/, Q's gate, R16's trust-report). Claude never writes it in study mode, allowlist or not, and /contract refuses solo modules: the learner writes solo work by hand." ;;
    2g) block "(rule 2g) — '$rel' is guard or build configuration, or a file that steers a session (the hook and its settings, the mode file, .claude/ skills, agents and commands, tests/, CLAUDE.md, the registry, scripts/, sandbox/, a project, crate, toolchain or Python build file). Claude never writes it in study mode: the learner edits CLAUDE.md's contract block by hand, and every other change is the author's." ;;
    allowlist) [ "${3:-}" = early ] || allowlist_lines "$2" ;;
    instructor)
      [ "${3:-}" = early ] && return 0
      [ -n "$CONTRACT" ] && block "(rule 2c) — '$rel' is instructor state, and $R2C_MSG" ;;
    learner)
      [ "${3:-}" = early ] && return 0
      allowlisted "$rel" || block "(rule 2) — '$rel' is learner-owned course material (dafny/{Q,R}/, verus/{q,r}/, harness/{q,r}/, specimens/, dafny/checks/, slots/, paper/*_answers.tex, research/, bench/local/, tools/): its holes and slots are the learner's to fill. It may only be edited inside a /contract session, and only when the path is listed in .claude/state/contract-allowlist. The tutor never solves the learner's exercises." ;;
  esac
  return 0
}
# user_config ABS — rule 2g on Claude Code's own settings outside the checkout:
# their disableAllHooks key switches off every hook, this one included.
user_config() {
  local x="$1" c=""
  if [ -n "${CLAUDE_CONFIG_DIR:-}" ]; then abspath "$CLAUDE_CONFIG_DIR" /; c="$ABS"; fi
  case "$x" in
    "$HOME"/.claude/settings.json|"$HOME"/.claude/settings.local.json|"$HOME"/.claude.json|/etc/claude-code|/etc/claude-code/*) ;;
    *) case "$c" in '') return 0 ;; esac
       case "$x" in "$c"/settings.json|"$c"/settings.local.json) ;; *) return 0 ;; esac ;;
  esac
  block "(rule 2g) — '$x' is Claude Code's own configuration: its disableAllHooks key would switch off this guard in every project. Claude never writes it from this checkout; settings changes are the human's to make."
}
# holds_root X: is X the checkout root, or a directory that holds it?
holds_root() {
  [ "$1" = / ] && return 0
  case "$ROOT/" in "$1"/*) return 0 ;; esac
  case "$RROOT/" in "$1"/*) return 0 ;; esac
  return 1
}
check_write() {   # PATH BASE TEXT [early] — classify a write target, lexically and through symlinks
  local x
  abspath "$1" "$2"; realp "$ABS"
  for x in "$ABS" "$REAL"; do
    user_config "$x"
    in_state "$x" && block "(rule 1e) — '$1' is another Claude Code session's state. $R1E_HINT"
    # The root itself (rm -rf ., chmod -R . , git checkout ., an archive
    # extracted into it): every class at once, the guard's own files included.
    holds_root "$x" && block "(rule 2g) — '$1' is the checkout root (or a directory that holds it). Removing, restoring, extracting into or changing the mode of it takes in the guard (.claude/), the registry, the frozen layers and every learner file at once. Name the file or directory you mean (instructor/scratch/<name> is scratch space); whole-checkout operations are the human's to run."
    rel_of "$x"; [ -n "$REL" ] || continue
    classify_write "$REL" "$3" "${4:-}"
  done
  return 0
}

# write_word WORD [BASE] — a write target word: each file a glob expands to
# (the shell expands it in the working directory), or the word itself.
write_word() {
  local r b="${2:-$CURDIR}"
  case "$1" in
    *'*'*|*'?'*|*'['*)
      while IFS= read -r r; do [ -n "$r" ] && check_write "$r" "$b" "$CMD"; done <<EOF
$(glob_paths "$1")
EOF
      ;;
    *) check_write "$1" "$b" "$CMD" ;;
  esac
  return 0
}
# extract_into DIR [MEMBER...] — an archive unpacked into DIR (tar -C, unzip
# -d, 7z -o, or the working directory): with members named, each member
# under DIR; otherwise any name at all, so DIR itself is classified (the
# checkout root: rule 2g; a learner tree: rule 2 even under a contract).
extract_into() {
  local d="$1" m
  shift
  if [ "$#" -eq 0 ]; then check_write "$d" / "$CMD"; return 0; fi
  for m in "$@"; do
    case "$m" in
      *'*'*|*'?'*|*'['*) check_write "$d" / "$CMD" ;;   # a wildcard member: any name
      *) check_write "$m" "$d" "$CMD" ;;
    esac
  done
  return 0
}
# copy_writes KIND — cp, install, rsync, ln, scp, mv: the destination is a
# write, and so is every moved source. Into a directory, each source lands as
# DIR/<its name>, which is classified too (a Cargo.toml copied into scratch
# is still a crate manifest); a source spelled DIR/ or DIR/. writes its
# contents into the destination itself. The checkout root as a destination
# is judged by those names alone.
copy_writes() {
  local kind="$1" i=1 t tdir="" dd=0 dest isdir=0 s nm opts=" " r
  local -a ops=() srcs=()
  case "$kind" in
    install) opts=" -m -o -g -S --mode --owner --group --suffix " ;;
    cp|ln|mv) opts=" -S --suffix " ;;
    rsync) opts=" -e -f -T -B -M --rsh --filter --include --exclude --include-from --exclude-from --files-from --temp-dir --compare-dest --copy-dest --link-dest --block-size --log-file --partial-dir --backup-dir --suffix --chmod --chown --usermap --groupmap --rsync-path --timeout --contimeout --port --password-file --bwlimit --max-size --min-size --max-delete --modify-window --remote-option --out-format --log-file-format --info --debug " ;;
    scp) opts=" -c -F -i -J -l -o -P -S -D -X " ;;
  esac
  while [ "$i" -lt "${#TK[@]}" ]; do
    t="${TK[$i]}"; i=$((i+1))
    if [ "$dd" = 0 ]; then
      case "$t" in
        --) dd=1; continue ;;
        -t|--target-directory) tdir="${TK[$i]:-}"; i=$((i+1)); continue ;;
        --target-directory=*) tdir="${t#*=}"; continue ;;
        -*) case "$opts" in *" $t "*) i=$((i+1)) ;; esac; continue ;;
      esac
    fi
    ops+=("$t")
  done
  if [ -n "$tdir" ]; then
    dest="$tdir"; isdir=1
  else
    [ "${#ops[@]}" -gt 0 ] || return 0
    if [ "$kind" = ln ] && [ "${#ops[@]}" -eq 1 ]; then
      dest=.                            # ln -s TARGET: a link named like it, here
    else
      dest="${ops[${#ops[@]}-1]}"; ops=("${ops[@]:0:${#ops[@]}-1}")
    fi
    abspath "$dest" "$CURDIR"
    { [ -d "$ABS" ] || [ "$dest" = . ]; } && isdir=1
    case "$dest" in */) isdir=1 ;; esac
  fi
  for s in ${ops[@]+"${ops[@]}"}; do   # each source, through its glob
    case "$s" in
      *'*'*|*'?'*|*'['*) while IFS= read -r r; do [ -n "$r" ] && srcs+=("$r"); done <<EOF
$(glob_paths "$s")
EOF
        ;;
      *) srcs+=("$s") ;;
    esac
  done
  if [ "$kind" = mv ]; then for s in ${srcs[@]+"${srcs[@]}"}; do check_write "$s" "$CURDIR" "$CMD"; done; fi
  if [ "$isdir" = 0 ]; then check_write "$dest" "$CURDIR" "$CMD"; return 0; fi
  abspath "$dest" "$CURDIR"
  holds_root "$ABS" || check_write "$dest" "$CURDIR" "$CMD"
  for s in ${srcs[@]+"${srcs[@]}"}; do
    case "$s" in
      *:*) case "$kind" in scp|rsync) s="${s#*:}" ;; esac ;;   # host:path, by its name
    esac
    case "$s" in
      .|*/|*/.) check_write "$dest" "$CURDIR" "$CMD" ;;        # its contents, into dest itself
      *) nm="${s##*/}"; [ -n "$nm" ] && check_write "$dest/$nm" "$CURDIR" "$CMD" ;;
    esac
  done
  return 0
}
# unzip_check — the extraction directory (-d, else here) or the members named;
# the list, test, comment and pipe modes write nothing.
unzip_check() {
  local i=1 t base="$CURDIR" arch="" excl=0 ro=0
  local -a mem=()
  while [ "$i" -lt "${#TK[@]}" ]; do
    t="${TK[$i]}"; i=$((i+1))
    case "$t" in
      -d) abspath "${TK[$i]:-.}" "$CURDIR"; base="$ABS"; i=$((i+1)); excl=0 ;;
      -d?*) abspath "${t#-d}" "$CURDIR"; base="$ABS"; excl=0 ;;
      -x) excl=1 ;;
      -P|-I|-O) i=$((i+1)) ;;
      -*) case "$t" in -*[lvtzZpc]*) ro=1 ;; esac ;;
      '<'*|'>'*|*'>'*) ;;
      *) if [ -z "$arch" ]; then arch="$t"; elif [ "$excl" = 0 ]; then mem+=("$t"); fi ;;
    esac
  done
  [ "$ro" = 1 ] || [ -z "$arch" ] && return 0
  extract_into "$base" ${mem[@]+"${mem[@]}"}
}
# patch_names FILE... — the file names a diff carries (unified, context and
# git headers), from each readable patch file (its first 1 MiB) and from the
# command text itself (a heredoc patch). A git rename or copy line comes out
# as =PATH: it is never stripped.
patch_names() {
  local f
  {
    for f in "$@"; do
      if [ -f "$f" ] && [ -r "$f" ]; then head -c 1048576 -- "$f" 2>/dev/null; printf '\n'; fi
    done
    printf '%s\n' "$CMD"
  } | sed -nE \
      -e 's/^(\+\+\+|---|\*\*\*)[[:space:]]+"?([^"[:space:]]+)"?.*$/\2/p' \
      -e 's/^diff --git[[:space:]]+"?([^"[:space:]]+)"?[[:space:]]+"?([^"[:space:]]+)"?.*$/\1\n\2/p' \
      -e 's/^(rename|copy) (from|to) (.+)$/=\3/p' \
      -e 's/^Index:[[:space:]]+(.+)$/\1/p' \
    | grep -vx -e /dev/null -e '' -e = | sort -u | head -n 300
}
# patch_writes BASE STRIP FILE... — every file a patch names is a write,
# under BASE after STRIP leading components (no STRIP: every suffix, the
# base name included, since patch without -p may use any of them). Returns 1
# when the patch names no file the hook can see (it came on a pipe).
patch_writes() {
  local base="$1" strip="$2" n c k found=1
  shift 2
  while IFS= read -r n; do
    [ -n "$n" ] || continue
    found=0
    case "$n" in =*) check_write "${n#=}" "$base" "$CMD"; continue ;; esac
    c="$n"
    if [[ "$strip" =~ ^[0-9]+$ ]]; then
      for ((k = 0; k < strip; k++)); do [[ "$c" == */* ]] || break; c="${c#*/}"; done
      [ -n "$c" ] && check_write "$c" "$base" "$CMD"
    else
      while :; do
        [ -n "$c" ] && check_write "$c" "$base" "$CMD"
        [[ "$c" == */* ]] || break
        c="${c#*/}"
      done
    fi
  done <<EOF
$(patch_names "$@")
EOF
  return "$found"
}
# patch_check — patch(1): the file it patches, its -o output and reject
# file, or every file its diff names (-d DIR first, as patch does).
patch_check() {
  local i=1 t dir="$CURDIR" strip="" orig="" out="" input="" redir="" n=0 dry=0 rej=""
  local -a pf=()
  while [ "$i" -lt "${#TK[@]}" ]; do
    t="${TK[$i]}"; i=$((i+1))
    case "$t" in
      -d|--directory) abspath "${TK[$i]:-.}" "$CURDIR"; dir="$ABS"; i=$((i+1)) ;;
      --directory=*) abspath "${t#*=}" "$CURDIR"; dir="$ABS" ;;
      -d?*) abspath "${t#-d}" "$CURDIR"; dir="$ABS" ;;
      -p|--strip) strip="${TK[$i]:-}"; i=$((i+1)) ;;
      -p?*) strip="${t#-p}" ;;
      --strip=*) strip="${t#*=}" ;;
      -i|--input) input="${TK[$i]:-}"; i=$((i+1)) ;;
      -i?*) input="${t#-i}" ;;
      --input=*) input="${t#*=}" ;;
      -o|--output) out="${TK[$i]:-}"; i=$((i+1)) ;;
      -o?*) out="${t#-o}" ;;
      --output=*) out="${t#*=}" ;;
      -r|--reject-file) rej="${TK[$i]:-}"; i=$((i+1)) ;;
      --reject-file=*) rej="${t#*=}" ;;
      --dry-run|-C|--check) dry=1 ;;
      -B|--prefix|-Y|--basename-prefix|-z|--suffix|-D|--ifdef|-F|--fuzz|-V|--version-control|--quoting-style|-g|--get) i=$((i+1)) ;;
      '<'|0'<') redir="${TK[$i]:-}"; i=$((i+1)) ;;
      '<'?*) redir="${t#<}" ;;
      '>'|'>>'|[0-9]'>'|[0-9]'>>') i=$((i+1)) ;;
      *'>'*) ;;
      -*) ;;
      *) n=$((n+1))
         [ "$n" = 1 ] && orig="$t"
         [ "$n" = 2 ] && [ -z "$input" ] && input="$t" ;;
    esac
  done
  [ "$dry" = 1 ] && return 0
  [ -n "$rej" ] && check_write "$rej" "$dir" "$CMD"
  if [ -n "$out" ]; then check_write "$out" "$dir" "$CMD"; return 0; fi
  if [ -n "$orig" ]; then check_write "$orig" "$dir" "$CMD"; return 0; fi
  if [ -n "$input" ]; then abspath "$input" "$dir"; pf+=("$ABS"); fi
  if [ -n "$redir" ]; then abspath "$redir" "$CURDIR"; pf+=("$ABS"); fi
  if ! patch_writes "$dir" "$strip" ${pf[@]+"${pf[@]}"} && [ -n "$CONTRACT" ]; then
    block "(rule 2c) — this patch arrives on a pipe, so the hook cannot see which files it writes, and a /contract session is active: a contractor edits only the files on the allowlist. Save the patch to a file and run patch -i <file>, or edit the allowlisted files directly."
  fi
  return 0
}

# --- Bash: rules 1, 1b, 1d, 1e, 1f, 2, one shell segment at a time. ----------
CURDIR="$CWD"   # where relative words resolve (cd, and -C/--directory for one command)
SHDIR="$CWD"    # the shell's own working directory ($PWD, ~+): cd only
SEG_NEXT=""     # the cut that ends the segment being checked ($(, `, ;, …)
TK=()
TOK_ST=0        # set by tokenize: the quote state the line ended in (0 = none)
# tokenize LINE → TK: the shell words of one simple command, quotes removed, so
# a quoted phrase stays one word (`rg "if bit then"` is a pattern and no path)
# and "" stays an empty word. Handles 'single', "double" (\" \\ \$ \`
# unescaped), $'ansi-c' (\' \\ \" \?), backslash escapes and # comments.
# Linear time: the line is cut into pieces — each blank, quote, backslash and $
# on its own — and read by one state machine. A quote left open (the segment
# splitter cut a quoted string) runs to the end of the line.
tokenize() {   # LINE [STATE] — STATE: the quote the line starts inside (default 0)
  local LC_ALL=C t="$1" c p nx nl=$'\n' cur="" st="${2:-0}" have=0 j=0 np
  [ "$st" = 0 ] || have=1
  local -a P
  TK=()
  if [ "${BASH_VERSINFO[0]}" -ge 4 ]; then
    for c in '\' "'" '"' '$' ' ' $'\t'; do t="${t//"$c"/"$nl$c$nl"}"; done
  else   # bash 3.2 (macOS) keeps quotes inside a ${x//p/r} replacement literally
    local rep
    for c in '\' "'" '"' '$' ' ' $'\t'; do rep="$nl$c$nl"; t="${t//"$c"/$rep}"; done
  fi
  IFS=$'\n' read -rd '' -a P <<<"$t" || true
  np="${#P[@]}"
  while [ "$j" -lt "$np" ]; do
    p="${P[j]}"; j=$((j+1))
    case "$st$p" in
      0' '|0$'\t')                      # a blank outside quotes ends the word
        [ "$have" = 1 ] && TK+=("$cur")
        cur="" have=0 ;;
      0\') st=1 have=1 ;;
      0\") st=2 have=1 ;;
      0\$) have=1                       # $'…' is ANSI-C quoting; else a plain $
        if [ "${P[j]:-}" = "'" ]; then st=3; j=$((j+1)); else cur+='$'; fi ;;
      0\\) have=1                       # \x is x, even a blank; a final \ stays
        if [ "$j" -lt "$np" ]; then
          cur+="${P[j]:0:1}"; P[j]="${P[j]:1}"; [ -n "${P[j]}" ] || j=$((j+1))
        else cur+='\'; fi ;;
      1\'|2\"|3\') st=0 ;;
      2\\|3\\)
        nx="${P[j]:-}"; nx="${nx:0:1}"
        case "$st$nx" in
          2\"|2\\|2\$|2\`|3\'|3\\|3\"|3\?)
            cur+="$nx"; P[j]="${P[j]:1}"; [ -n "${P[j]}" ] || j=$((j+1)) ;;
          *) cur+='\' ;;
        esac ;;
      0*) [ "$have" = 0 ] && [ "${p:0:1}" = '#' ] && break   # a comment
        cur+="$p"; have=1 ;;
      *) cur+="$p" ;;                   # inside quotes everything else is literal
    esac
  done
  if [ "$have" = 1 ] || [ "$st" != 0 ]; then TK+=("$cur"); fi
  TOK_ST="$st"
  return 0
}
has_tok() {   # WORD — is WORD one of the segment's words (not part of a quoted one)?
  local x
  for x in "${TK[@]}"; do [ "$x" = "$1" ] && return 0; done
  return 1
}
consumer() {   # is a file list piped into something that opens the files?
  [[ "$CMD" =~ $RX_CONSUMER ]]
}
glob_paths() {   # GLOB → one expansion per line, as the shell would expand it in CURDIR
  xvar "$1"       # "$PWD"/S*, ~+/*, $CLAUDE_PROJECT_DIR/*: compgen does not expand them
  (cd "$CURDIR" 2>/dev/null && compgen -G "$XV" 2>/dev/null | head -n 500)
}
# reach_one ABS WORD WHAT RULE — a recursive read rooted at ABS
reach_one() {
  reaches "$1" && block "($4) — $3 '$2' takes in a reference tree (or a build output that can hold one). $R1D_HINT"
  reaches_state "$1" && block "(rule 1e) — $3 '$2' takes in other Claude Code sessions' state (transcripts, file history, scratch directories). $R1E_HINT"
  if [ -n "$CONTRACT" ] && reaches_bench "$1"; then block "(rule 2c) — $3 '$2' takes in public benchmark answers, and $R2C_MSG"; fi
  return 0
}
check_reach() {   # PATH WHAT [RULE] — rule 1d (or RULE): a recursive read rooted at PATH
  local g rule="${3:-rule 1d}"
  case "$1" in
    *'*'*|*'?'*|*'['*)
      while IFS= read -r g; do
        [ -n "$g" ] || continue
        abspath "$g" "$CURDIR"; reach_one "$ABS" "$1" "$2" "$rule"
      done <<EOF
$(glob_paths "$1")
EOF
      ;;
    *) abspath "$1" "$CURDIR"; reach_one "$ABS" "$1" "$2" "$rule" ;;
  esac
  return 0
}
search_check() {   # TOOL START — recursive search: pattern, then paths
  local tool="$1" i="$2" t vo have_e=0 skip=0 pat=0 dd=0 named=0
  local -a paths=()
  if [ "$tool" = rg ] && has_tok --files; then
    consumer || return 0
    have_e=1                          # no pattern: every operand is a path
  fi
  case "$tool" in
    rg)  vo=" -e -f -m -A -B -C -d -g -t -T -E -j -M -r --regexp --file --max-count --context --after-context --before-context --glob --iglob --type --type-not --type-add --type-clear --encoding --engine --threads --max-columns --max-filesize --dfa-size-limit --regex-size-limit --replace --max-depth --maxdepth --sort --sortr --colors --color --context-separator --field-context-separator --field-match-separator --hyperlink-format --pre --pre-glob --ignore-file --path-separator " ;;
    ag)  vo=" -A -B -C -G -g -m -p -W --ignore --ignore-dir --file-search-regex --path-to-ignore --depth --context --pager --workers --width " ;;
    git) vo=" -e -f -A -B -C -m -O --max-depth --threads --open-files-in-pager " ;;
    ugrep) vo=" -e -f -m -A -B -C -d -D -g -t -J -K -M -N -O --regexp --file --max-count --context --after-context --before-context --include --exclude --include-dir --exclude-dir --include-from --exclude-from --include-fs --exclude-fs --glob --iglob --file-type --file-extension --file-magic --neg-regexp --and --andnot --not --depth --range --label --binary-files --devices --directories --group-separator --separator --encoding --format --filter --jobs --sort --tabs --width --max-files --colors --tag --view --pager --hexdump --index --save-config " ;;
    *)   vo=" -e -f -m -A -B -C -d -D --regexp --file --max-count --context --after-context --before-context --include --exclude --exclude-dir --exclude-from --label --binary-files --devices --directories --group-separator " ;;
  esac
  for t in "${TK[@]:$i}"; do
    if [ "$skip" = 1 ]; then skip=0; continue; fi
    if [ "$dd" = 0 ]; then
      case "$t" in
        --) dd=1; continue ;;
        -e|--regexp|-f|--file) have_e=1; skip=1; continue ;;
        --regexp=*|--file=*) have_e=1; continue ;;
        -*=*) continue ;;
        -*) case "$vo" in *" $t "*) skip=1 ;; esac; continue ;;
      esac
    fi
    if [ "$have_e" = 0 ] && [ "$pat" = 0 ]; then pat=1; continue; fi
    if [ "$tool" = git ]; then          # git grep: only real paths limit it
      abspath "$t" "$CURDIR"; [ -e "$ABS" ] || [ "$dd" = 1 ] || continue
    fi
    paths+=("$t")
  done
  [ "${#paths[@]}" -gt 0 ] || paths=(".")
  for t in "${paths[@]}"; do check_reach "$t" "a recursive search of"; done
  # Only an operand that names something limits the reach: an existing path,
  # a glob, or a word the hook cannot resolve ($VAR, `cmd`, {a,b}). When every
  # operand is a missing word, the line was misread (an option's argument or a
  # cut-up pattern taken for a path) and the search runs in the working dir.
  [ "$tool" = git ] && return 0       # git grep keeps real paths only, above
  for t in "${paths[@]}"; do
    case "$t" in *'$'*|*'`'*|*'{'*|*'*'*|*'?'*|*'['*) named=1; break ;; esac
    abspath "$t" "$CURDIR"
    if [ -e "$ABS" ] || [ -L "$ABS" ]; then named=1; break; fi
  done
  if [ "$named" = 0 ]; then
    abspath . "$CURDIR"
    reaches "$ABS" && block "(rule 1d) — no operand of this recursive search names an existing path ('${paths[*]}'), so it searches the working directory, which takes in a reference tree. $R1D_HINT"
  fi
  return 0
}
# git_whole SUB — a git command that rewrites tracked files across the tree
# (branch switch, reset --hard, stash, merge, pull, rebase, cherry-pick,
# revert, am, a patch the hook cannot see): rule 2c while a contract is
# active, since a contractor edits only allowlisted files. With no contract
# these stay an accepted cost (header): the learner may ask for them.
git_whole() {
  [ -n "$CONTRACT" ] || return 0
  case "$gdir/" in "$ROOT"/*|"$RROOT"/*) ;; *) return 0 ;; esac   # another repository
  block "(rule 2c) — 'git $1' rewrites tracked files across the whole checkout, and a /contract session is active (.claude/state/contract-allowlist is non-empty): a contractor edits only the files on the allowlist. Finish or abandon the contract first (its close-out empties the allowlist); branch switches, resets, stashes, merges and patch applications are the learner's to run."
}
git_check() {
  local i=1 t sub gdir="$CURDIR" dd=0 ps=0 bad=0 stat=0 patch=0 rev=0 obj=0 n=0 dry=0 strip=1 pre="" chk=0 app=0
  local -a pf=()
  while [ "$i" -lt "${#TK[@]}" ]; do
    case "${TK[$i]}" in
      -C) abspath "${TK[$((i+1))]:-.}" "$CURDIR"; gdir="$ABS"; i=$((i+2)) ;;
      -c|--git-dir|--work-tree|--namespace) i=$((i+2)) ;;
      -*) i=$((i+1)) ;;
      *) break ;;
    esac
  done
  sub="${TK[$i]:-}"; i=$((i+1))
  case "$sub" in
    grep) local saved="$CURDIR"; CURDIR="$gdir"; search_check git "$i"; CURDIR="$saved"; return 0 ;;
    checkout|switch)
      # Paths are writes (rule 2 and up). A revision with no path after it
      # switches the whole tree (rule 2c under a contract); `checkout REV --
      # PATH` only restores PATH. -b/-B/-c/-C/--orphan NAME alone names a new
      # branch at HEAD.
      local newb=0 skipn=0 np=0
      for t in "${TK[@]:$i}"; do
        if [ "$skipn" = 1 ]; then skipn=0; continue; fi
        if [ "$dd" = 1 ]; then np=$((np+1)); write_word "$t" "$gdir"; continue; fi
        case "$t" in
          --) dd=1 ;;
          -b|-B|-c|-C|--orphan|--create|--force-create) newb=1; skipn=1 ;;
          -*) ;;
          *) # a path (a deleted one too) is checked as a write; a word that
             # names nothing here may be a revision
             [ "$sub" = checkout ] && write_word "$t" "$gdir"
             abspath "$t" "$gdir"
             if [ -e "$ABS" ] || [ -L "$ABS" ]; then np=$((np+1)); else n=$((n+1)); fi ;;
        esac
      done
      if [ "$sub" = switch ]; then [ "$newb" = 0 ] && git_whole switch
      elif [ "$n" -gt 0 ] && [ "$np" = 0 ] && [ "$dd" = 0 ]; then git_whole "checkout (a branch or revision)"; fi
      return 0 ;;
    restore|rm|mv)
      for t in "${TK[@]:$i}"; do
        case "$t" in -*) ;; *) write_word "$t" "$gdir" ;; esac
      done
      return 0 ;;
    clean)
      # No pathspec cleans the whole working directory (the root, from the
      # root: rule 2g); -n/--dry-run only lists.
      local skipe=0
      for t in "${TK[@]:$i}"; do
        if [ "$skipe" = 1 ]; then skipe=0; continue; fi
        case "$t" in
          -e|--exclude) skipe=1 ;;
          -n|--dry-run) dry=1 ;;
          --) ;;
          --*) ;;
          -*) case "$t" in -*n*) dry=1 ;; esac ;;
          *) n=$((n+1)); write_word "$t" "$gdir" ;;
        esac
      done
      [ "$dry" = 0 ] && [ "$n" = 0 ] && check_write "$gdir" / "$CMD"
      return 0 ;;
    reset)
      for t in "${TK[@]:$i}"; do case "$t" in --hard|--merge|--keep) git_whole "reset $t" ;; esac; done
      return 0 ;;
    stash)
      case "${TK[$i]:-}" in list|show) return 0 ;; esac
      git_whole stash; return 0 ;;
    merge|pull|rebase|cherry-pick|revert|am)
      git_whole "$sub"
      [ "$sub" = am ] || return 0 ;;
    apply) ;;
    show|log|whatchanged|diff|format-patch|archive|bundle|cat-file|ls-files|ls-tree) ;;
    *) return 0 ;;
  esac
  if [ "$sub" = apply ] || [ "$sub" = am ]; then
    # git apply / am: every file the patch names is a write, from the
    # top of the tree with -p1 by default. A patch on stdin is invisible.
    local skipa="" base="$gdir"
    case "$gdir/" in "$ROOT"/*|"$RROOT"/*) base="$ROOT" ;; esac
    for t in "${TK[@]:$i}"; do
      if [ -n "$skipa" ]; then
        case "$skipa" in p) strip="$t" ;; d) pre="$t" ;; esac
        skipa=""; continue
      fi
      case "$t" in
        -p) skipa=p ;;
        -p*) strip="${t#-p}" ;;
        --directory) skipa=d ;;
        --directory=*) pre="${t#*=}" ;;
        --exclude|--include|-C|--whitespace) skipa=x ;;
        --check|--stat|--numstat|--summary) chk=1 ;;
        --apply) app=1 ;;
        --cached) [ "$sub" = apply ] && return 0 ;;   # the index only
        --abort|--continue|--skip|--quit|--show-current-patch*|--resolved|-r) return 0 ;;
        -) ;;
        -*) ;;
        *) abspath "$t" "$gdir"; pf+=("$ABS") ;;
      esac
    done
    [ "$chk" = 1 ] && [ "$app" = 0 ] && return 0          # reports only
    [ -n "$pre" ] && base="$base/$pre"
    if ! patch_writes "$base" "$strip" ${pf[@]+"${pf[@]}"}; then git_whole "$sub (a patch on stdin)"; fi
    return 0
  fi
  for t in "${TK[@]:$i}"; do
    if [ "$dd" = 1 ]; then
      ps=1; abspath "$t" "$gdir"; reaches "$ABS" && bad=1; continue
    fi
    case "$t" in
      --) dd=1 ;;
      --stat*|--shortstat|--numstat|--name-only|--name-status|--no-patch|-s|--raw|--dirstat*|--summary|--compact-summary) stat=1 ;;
      -p|-u|--patch|--patch-with-stat|--patch-with-raw|--cc|-c|-m|--full-diff|--word-diff*|--color-words*|-L*|--textconv|--filters|--batch*) patch=1 ;;
      -*) ;;
      *:*) obj=1 ;;                     # rev:path names one object
      *) abspath "$t" "$gdir"
         if [ -e "$ABS" ]; then ps=1; reaches "$ABS" && bad=1
         elif [ "$t" != HEAD ]; then rev=1; fi ;;
    esac
  done
  [ "$patch" = 1 ] && stat=0
  local narrowed=0
  [ "$ps" = 1 ] && [ "$bad" = 0 ] && narrowed=1
  local msg="(rule 1d) — 'git $sub' without a learner pathspec prints history of the whole tree, reference solutions included. $R1D_HINT"
  case "$sub" in
    show) [ "$stat" = 1 ] || [ "$obj" = 1 ] || [ "$narrowed" = 1 ] || block "$msg" ;;
    log|whatchanged) [ "$patch" = 0 ] || [ "$narrowed" = 1 ] || block "$msg" ;;
    diff) [ "$rev" = 0 ] || [ "$stat" = 1 ] || [ "$narrowed" = 1 ] || block "$msg" ;;
    format-patch|archive|bundle) [ "$narrowed" = 1 ] || block "$msg" ;;
    cat-file) [ "$patch" = 0 ] && [[ ! " ${TK[*]} " =~ [[:space:]](blob|tree|commit)[[:space:]] ]] || block "$msg" ;;
    ls-files|ls-tree) consumer && [ "$narrowed" = 0 ] && block "(rule 1d) — piping an unscoped 'git $sub' into a reader opens every tracked file, reference solutions included. $R1D_HINT" ;;
  esac
  return 0
}
find_check() {
  local i=1 t w=0
  local -a starts=()
  while [ "$i" -lt "${#TK[@]}" ]; do
    case "${TK[$i]}" in -H|-L|-P|-O*) i=$((i+1)) ;; -D) i=$((i+2)) ;; *) break ;; esac
  done
  while [ "$i" -lt "${#TK[@]}" ]; do
    case "${TK[$i]}" in -*|'('|'!'|'\('|',') break ;; esac
    starts+=("${TK[$i]}"); i=$((i+1))
  done
  [ "${#starts[@]}" -gt 0 ] || starts=(".")
  if [[ " ${TK[*]} " =~ [[:space:]]-(exec|execdir|ok|okdir)[[:space:]] ]] || consumer; then
    for t in "${starts[@]}"; do check_reach "$t" "find feeding a reader from"; done
  fi
  # -delete, or -exec of a command that writes the files it is handed, is a
  # write anywhere under each start: the start is classified like rm -r's
  # operand (the checkout root: rule 2g; a learner tree: rule 2).
  for ((; i < ${#TK[@]}; i++)); do
    case "${TK[$i]}" in
      -delete) w=1 ;;
      -exec|-execdir|-ok|-okdir) exec_writes $((i+1)) && w=1 ;;
    esac
  done
  if [ "$w" = 1 ]; then for t in "${starts[@]}"; do write_word "$t"; done; fi
  return 0
}
# exec_writes I — does the command at TK[I] (find -exec's, fd -x's) write the
# files it is handed (rm, mv, chmod, …, or sed/perl/ruby -i before the {})?
exec_writes() {
  local i="$1" t
  t="${TK[$i]:-}"; t="${t##*/}"
  case "$t" in
    rm|rmdir|unlink|shred|truncate|mv|cp|install|ln|chmod|chown|chgrp|tee|dd|patch|ed|ex) return 0 ;;
    sed|gsed|perl|ruby)
      t=" ${TK[*]:$((i+1))} "; t="${t%% \{\} *}"
      [[ "$t " =~ [[:space:]](-[A-Za-z]*i[^[:space:]]*|--in-place[^[:space:]]*)[[:space:]] ]] && return 0 ;;
  esac
  return 1
}
# fd_check — fd (fdfind) walks each search path; -x/-X (--exec/--exec-batch)
# run a command on every match, find -exec's read (rule 1d), and a writing
# command there writes under each search path, as find's does. Search paths:
# the operands after the pattern and every --search-path, resolved against
# --base-directory when one is given; none means the working directory. With
# no exec and no consumer, fd lists names only (header: exposed).
fd_check() {
  local i=1 t c j ex=0 skip=0 dd=0 pat=0 base="$CURDIR" saved
  local -a starts=()
  while [ "$i" -lt "${#TK[@]}" ]; do
    t="${TK[$i]}"; i=$((i+1))
    if [ "$skip" = 1 ]; then skip=0; continue; fi
    if [ "$dd" = 0 ]; then
      case "$t" in
        --) dd=1; continue ;;
        -x|-X|--exec|--exec-batch) ex=1; break ;;          # the command follows
        --base-directory) abspath "${TK[$i]:-.}" "$CURDIR"; base="$ABS"; i=$((i+1)); continue ;;
        --base-directory=*) abspath "${t#*=}" "$CURDIR"; base="$ABS"; continue ;;
        --search-path) starts+=("${TK[$i]:-.}"); i=$((i+1)); continue ;;
        --search-path=*) starts+=("${t#*=}"); continue ;;
        --extension|--type|--exclude|--max-depth|--min-depth|--exact-depth|--size|--changed-within|--changed-before|--change-newer-than|--change-older-than|--newer|--older|--owner|--format|--batch-size|--ignore-file|--color|--threads|--max-buffer-time|--max-results|--path-separator|--and)
          skip=1; continue ;;
        --*) continue ;;
        -?*)                                                # a cluster: -He dfy, -Hx cat
          for ((j = 1; j < ${#t}; j++)); do
            c="${t:j:1}"
            case "$c" in
              x|X) ex=1; break 2 ;;
              [etEdSojc]) [ $((j + 1)) -eq "${#t}" ] && skip=1; break ;;
            esac
          done
          continue ;;
      esac
    fi
    if [ "$pat" = 0 ]; then pat=1; continue; fi
    starts+=("$t")
  done
  [ "$ex" = 1 ] || consumer || return 0
  [ "${#starts[@]}" -gt 0 ] || starts=(".")
  saved="$CURDIR"; CURDIR="$base"
  for t in "${starts[@]}"; do check_reach "$t" "fd feeding a reader from"; done
  if [ "$ex" = 1 ] && exec_writes "$i"; then for t in "${starts[@]}"; do write_word "$t" "$base"; done; fi
  CURDIR="$saved"
  return 0
}
# diff_check — diff (and colordiff, which hands its words to diff) with -r,
# --recursive or a short-option cluster holding r (-ru, -Nr, -rq): each
# operand is a tree read whole, and the bodies of the files that differ are
# printed (with -N, against any tree at all), so each operand's reach is
# grep -r's. A diff without -r compares only the files directly inside two
# directories, and is left alone.
diff_check() {
  local t c j rec=0 skip=0 dd=0
  local -a ops=()
  for t in "${TK[@]:1}"; do
    case "$skip" in
      1) skip=0; continue ;;                                # an option's argument
      2) skip=0; ops+=("$t"); continue ;;                   # --from-file/--to-file DIR
    esac
    if [ "$dd" = 0 ]; then
      case "$t" in
        --) dd=1; continue ;;
        --rec*) rec=1; continue ;;                          # --recursive (or a prefix of it)
        --from-file=*|--to-file=*) ops+=("${t#*=}"); continue ;;
        --from-file|--to-file) skip=2; continue ;;
        --*=*) continue ;;
        --exclude|--exclude-from|--ignore-matching-lines|--label|--starting-file|--show-function-line|--ifdef|--horizon-lines|--width|--tabsize|--palette|--*line-format|--*group-format)
          skip=1; continue ;;
        --*|-) continue ;;
        -*)                                                 # a cluster; C D F I L S U W X x take an argument
          for ((j = 1; j < ${#t}; j++)); do
            c="${t:j:1}"
            case "$c" in
              r) rec=1 ;;
              [CDFILSUWXx]) [ $((j + 1)) -eq "${#t}" ] && skip=1; break ;;
            esac
          done
          continue ;;
      esac
    fi
    ops+=("$t")
  done
  [ "$rec" = 1 ] || return 0
  for t in ${ops[@]+"${ops[@]}"}; do check_reach "$t" "a recursive diff of"; done
  return 0
}
# index_check KIND — ctags -R/--recurse and cscope -R build an index of every
# file they walk, copying definition lines (ctags) or each symbol's source
# line (cscope) into ./tags or cscope.out, so their reach is grep -r's. Each
# operand (none: the working directory) and each cscope -s directory counts.
# Without recursion they read the files named, which the path checks cover.
index_check() {
  local kind="$1" t c j rec=0 skip=0 dd=0 argl
  local -a ops=() sdirs=()
  case "$kind" in ctags) argl="fohILD" ;; *) argl="fiIspFP0123456789" ;; esac
  for t in "${TK[@]:1}"; do
    case "$skip" in
      1) skip=0; continue ;;
      2) skip=0; sdirs+=("$t"); continue ;;
    esac
    if [ "$dd" = 0 ]; then
      case "$t" in
        --) dd=1; continue ;;
        --recurse|--recurse=yes|--recurse=1|--recurse=on) rec=1; continue ;;
        --*) continue ;;
        -?*)
          for ((j = 1; j < ${#t}; j++)); do
            c="${t:j:1}"
            [ "$c" = R ] && { rec=1; continue; }
            case "$argl" in
              *"$c"*)
                if [ "$kind:$c" = cscope:s ]; then
                  if [ $((j + 1)) -lt "${#t}" ]; then sdirs+=("${t:j+1}"); else skip=2; fi
                elif [ $((j + 1)) -eq "${#t}" ]; then skip=1; fi
                break ;;
            esac
          done
          continue ;;
      esac
    fi
    ops+=("$t")
  done
  [ "$rec" = 1 ] || return 0
  [ "${#ops[@]}" -gt 0 ] || ops=(".")
  for t in "${ops[@]}" ${sdirs[@]+"${sdirs[@]}"}; do check_reach "$t" "a recursive $kind index of"; done
  return 0
}
# copy_reach KIND — rule 1d for archivers and recursive copies: each source
# operand is read whole, so a source whose reach takes in a reference tree is
# the same read as `grep -r`. TK holds the segment's words (command first).
copy_reach() {
  local kind="$1" t i=1 rec=0 create=0 skip=0 dd=0 base="$CURDIR" tdir=0 opts="" last_opt="" fl xt=0 tout=0
  local -a ops=() mem=()
  local what="an archive or recursive copy of"
  case "$kind" in
    tar) opts=" -f -C -T -X -b -K -N -V -g -H -L -I --file --directory --files-from --exclude-from --exclude --label --format --listed-incremental --use-compress-program --transform --owner --group --mode --mtime --newer --after-date " ;;
    zip) opts=" -b -n -t -tt -O -P -s -sp -Z -TT --out --temp-path --suffixes --password --split-size --compression-method " ;;
    7z)  opts=" " ;;
    pax) opts=" -f -s -o -x -b -B -G -T -U " ;;
    rsync) opts=" -e -f -T -B -M --rsh --filter --include --exclude --include-from --exclude-from --files-from --temp-dir --compare-dest --copy-dest --link-dest --block-size --log-file --partial-dir --backup-dir --suffix --chmod --chown --usermap --groupmap --rsync-path --timeout --contimeout --port --password-file --bwlimit --max-size --min-size --max-delete --modify-window --remote-option --out-format --log-file-format --info --debug " ;;
    cp)  opts=" -S --suffix " ;;
    scp) opts=" -c -F -i -J -l -o -P -S -D -X " ;;
  esac
  while [ "$i" -lt "${#TK[@]}" ]; do
    t="${TK[$i]}"; i=$((i+1))
    if [ "$skip" = 1 ]; then
      skip=0
      [ "$kind:$last_opt" = "tar:-C" ] || [ "$kind:$last_opt" = "tar:--directory" ] && { abspath "$t" "$CURDIR"; base="$ABS"; }
      continue
    fi
    if [ "$dd" = 0 ]; then
      case "$t" in
        --) dd=1; continue ;;
        --*=*)
          case "$kind:${t%%=*}" in
            tar:--directory) abspath "${t#*=}" "$CURDIR"; base="$ABS" ;;
            tar:--to-command) tout=1 ;;
            cp:--target-directory) tdir=1 ;;
          esac
          continue ;;
        -*)
          last_opt="$t"
          case "$opts" in *" $t "*) skip=1; continue ;; esac
          case "$kind:$t" in
            tar:--create|tar:--append|tar:--update|tar:--concatenate) create=1 ;;
            tar:--extract|tar:--get) xt=1 ;;
            tar:--to-stdout) tout=1 ;;
            7z:-o?*) abspath "${t#-o}" "$CURDIR"; base="$ABS" ;;
            cp:--recursive|cp:--archive|rsync:--recursive|rsync:--archive|zip:--recurse-paths) rec=1 ;;
            cp:-t|cp:--target-directory) tdir=1; skip=1 ;;
            tar:--*|cp:--*|rsync:--*|zip:--*|scp:--*|pax:--*|7z:-*) ;;
            tar:-*) case "$t" in -*[cruA]*) create=1 ;; esac
                    case "$t" in -*x*) xt=1 ;; esac
                    case "$t" in -*O*) tout=1 ;; esac
                    case "$t" in -*f) skip=1 ;; esac ;;
            cp:-*|scp:-*) case "$t" in -*[rRa]*) rec=1 ;; esac ;;
            rsync:-*) case "$t" in -*[ra]*) rec=1 ;; esac ;;
            zip:-*) case "$t" in -*[rR]*) rec=1 ;; esac ;;
            pax:-*) case "$t" in -*w*) create=1 ;; esac ;;
          esac
          continue ;;
      esac
    fi
    if [ "$kind" = tar ] && [ "$i" = 2 ] && [[ "$t" =~ ^[A-Za-z]+$ ]]; then
      # old-style bundle, the first word only: tar cf ARCHIVE …
      case "$t" in *[cruA]*) create=1 ;; esac
      case "$t" in *x*) xt=1 ;; esac
      case "$t" in *O*) tout=1 ;; esac
      fl="${t//[^fbCTXKNVgHL]/}"      # each of these letters takes the next word
      while [ -n "$fl" ] && [ "$i" -lt "${#TK[@]}" ]; do
        [ "${fl:0:1}" = C ] && { abspath "${TK[$i]}" "$CURDIR"; base="$ABS"; }
        i=$((i+1)); fl="${fl:1}"
      done
      continue
    fi
    ops+=("$t")
  done
  # Extraction writes: tar x / --extract (not to stdout), 7z x|e.
  if [ "$kind" = tar ] && [ "$xt" = 1 ] && [ "$tout" = 0 ]; then
    skip=0
    for t in ${ops[@]+"${ops[@]}"}; do
      if [ "$skip" = 1 ]; then skip=0; continue; fi
      case "$t" in
        '<'|'>'|'>>'|[0-9]'>'|[0-9]'>>') skip=1 ;;      # a redirect and its file
        '<'*|'>'*|*'>'*|-) ;;
        *) mem+=("$t") ;;
      esac
    done
    extract_into "$base" ${mem[@]+"${mem[@]}"}
  fi
  if [ "$kind" = 7z ]; then
    case "${ops[0]:-}" in x|e) extract_into "$base" "${ops[@]:2}" ;; esac
  fi
  [ "${#ops[@]}" -gt 0 ] || return 0
  case "$kind" in
    tar|pax) [ "$create" = 1 ] || return 0 ;;
    zip) [ "$rec" = 1 ] || return 0; ops=("${ops[@]:1}") ;;            # first operand: the archive
    7z) case "${ops[0]}" in a|u) ops=("${ops[@]:2}") ;; *) return 0 ;; esac ;;
    cp|scp|rsync)
      [ "$rec" = 1 ] || return 0
      [ "$tdir" = 1 ] || ops=("${ops[@]:0:${#ops[@]}-1}") ;;           # last operand: the destination
    ditto) ops=("${ops[@]:0:${#ops[@]}-1}") ;;
  esac
  local saved="$CURDIR"; CURDIR="$base"
  for t in ${ops[@]+"${ops[@]}"}; do
    case "$t" in *:*) [ "$kind" = scp ] || [ "$kind" = rsync ] && continue ;; esac   # host:path is remote
    check_reach "$t" "$what"
  done
  CURDIR="$saved"
  return 0
}
pytest_check() {   # START — rule 1b: pytest collects from its operands, or the working dir
  local i="$1" t skip=0
  local -a ops=()
  for t in "${TK[@]:$i}"; do
    if [ "$skip" = 1 ]; then skip=0; continue; fi
    case "$t" in
      -k|-m|-p|-o|-W|-c|-r|-n|--rootdir|--confcutdir|--basetemp|--deselect|--ignore|--ignore-glob|--junitxml|--junit-xml|--maxfail|--tb|--durations|--cov|--cov-report|--log-file|--override-ini|--import-mode|--capture|--color|--dist) skip=1 ;;
      -*) ;;
      *) ops+=("${t%%::*}") ;;          # a node id path::test collects from its path
    esac
  done
  [ "${#ops[@]}" -gt 0 ] || ops=(".")
  for t in "${ops[@]}"; do check_reach "$t" "pytest collecting from" "rule 1b"; done
  return 0
}
claude_ok() {   # TK = claude … — the tool-less policy form, or a harmless query
  local i n="${#TK[@]}" t p=0 tools=0 strict=0 mcp=0
  if [ "$n" -eq 2 ]; then case "${TK[1]}" in --version|-v|--help|-h) return 0 ;; esac; fi
  [ "${TK[1]:-}" = auth ] && [ "${TK[2]:-}" = status ] && return 0
  for ((i = 1; i < n; i++)); do
    t="${TK[i]}"
    case "$t" in
      -p|--print) p=1 ;;
      --tools) [ -z "${TK[i+1]-x}" ] && tools=1 ;;
      --tools=) tools=1 ;;
      --strict-mcp-config) strict=1 ;;
      --mcp-config|--mcp-config=*) mcp=1 ;;
    esac
  done
  [ "$p" = 1 ] && [ "$tools" = 1 ] && [ "$strict" = 1 ] && [ "$mcp" = 0 ]
}
check_assign() {   # NAME=VALUE — environment that changes how the verifier runs (2g) or reaches a daemon (1f)
  local n="${1%%=*}" v="${1#*=}"
  case "$n" in
    VERUS_Z3_PATH|VERUS_EXTRA_ARGS|RUSTC_WRAPPER|RUSTC_WORKSPACE_WRAPPER)
      block "(rule 2g) — $n changes how the verifier runs (a substituted solver or compiler is a fake-green vector). Run the pinned toolchain through scripts/vcheck with a clean environment." ;;
    RUSTFLAGS|CARGO_ENCODED_RUSTFLAGS)
      case "$v" in *verus_only*|*--cfg*) block "(rule 2g) — $n with --cfg/verus_only changes what the verifier sees. Run the pinned toolchain through scripts/vcheck with a clean environment." ;; esac ;;
    DOCKER_HOST) block "(rule 1f) — DOCKER_HOST points a container client at a daemon. Container runs go only through scripts/mksandbox-run." ;;
    CI) block "$R1B_CI" ;;
    PATH) PATHSET=1 ;;
  esac
  return 0
}
verifier_flags() {   # rule 2g: --plugin and an unpinned --solver-path on a Dafny command
  local i n="${#TK[@]}" t v
  for ((i = 1; i < n; i++)); do
    t="${TK[i]}" v=""
    case "$t" in
      --plugin|--plugin=*) block "(rule 2g) — Dafny --plugin loads an assembly that rewrites the program before verification. Verify through scripts/vcheck with the pinned options." ;;
      --solver-path) v="${TK[i+1]:-}" ;;
      --solver-path=*) v="${t#*=}" ;;
      *) continue ;;
    esac
    abspath "$v" "$CURDIR"; realp "$ABS"
    case "$REAL" in
      */.toolchain/dafny-4.11.0/dafny/z3/bin/z3-4.12.1|*/.toolchain/dafny-4.11.0/dafny/z3/bin/z3-4.14.1) ;;
      *) block "(rule 2g) — --solver-path '$v' is not the pinned bundled Z3 (.toolchain/dafny-4.11.0/dafny/z3/bin/z3-4.12.1 or z3-4.14.1); a substituted solver is a fake-green vector." ;;
    esac
  done
  return 0
}
# vaudit_writes I — vaudit's --write FILE (any unique prefix, --w…) writes the
# pinned audit report: FILE is a write target (expected/ is rule 2f, so a
# study session cannot re-pin an audit it fails). TK[I] is the vaudit word.
vaudit_writes() {
  local j t
  for ((j = $1 + 1; j < ${#TK[@]}; j++)); do
    t="${TK[j]}"
    case "$t" in
      --w|--wr|--wri|--writ|--write) [ -n "${TK[j+1]:-}" ] && check_write "${TK[j+1]}" "$CURDIR" "$CMD" ;;
      --w=*|--wr=*|--wri=*|--writ=*|--write=*) check_write "${t#*=}" "$CURDIR" "$CMD" ;;
    esac
  done
  return 0
}
seg_check() {   # SEGMENT — one simple command of the shell line
  local t i n=0 cmd r inplace last tdir seg_saved="$CURDIR" j g
  local -a rest
  PATHSET=0
  tokenize "$1"
  # Peel wrappers until the command word.
  while [ "${#TK[@]}" -gt 0 ]; do
    case "${TK[0]}" in
      ''|'{'|'}'|'!'|'['|'[['|builtin|exec|nohup|time|then|do|else|elif|if|while|until)
        TK=("${TK[@]:1}") ;;
      eval)                           # eval re-reads its words as a command line
        t="${TK[*]:1}"; tokenize "$t" ;;
      export|declare|typeset|local|readonly)
        # NAME=VALUE words, and a bare CI (exporting a CI set earlier).
        for t in "${TK[@]:1}"; do case "$t" in [A-Za-z_]*=*) check_assign "$t" ;; CI) check_assign "CI=" ;; esac; done
        break ;;
      env|command|nice|timeout|stdbuf)
        t="${TK[0]}"; TK=("${TK[@]:1}")
        while [ "${#TK[@]}" -gt 0 ]; do
          case "$t:${TK[0]}" in         # options whose argument is the next word
            env:-[uC]|nice:-n|timeout:-[sk]|stdbuf:-[ioe]) TK=("${TK[@]:2}") ;;
            env:[A-Za-z_]*=*) check_assign "${TK[0]}"; TK=("${TK[@]:1}") ;;
            *:-*) TK=("${TK[@]:1}") ;;
            *) break ;;
          esac
        done
        [ "$t" = timeout ] && TK=("${TK[@]:1}") ;;
      xargs)
        TK=("${TK[@]:1}")
        while [ "${#TK[@]}" -gt 0 ]; do
          case "${TK[0]}" in
            -I|-n|-P|-L|-d|-s|-a|-E|--max-args|--max-procs|--delimiter) TK=("${TK[@]:2}") ;;
            -*) TK=("${TK[@]:1}") ;;
            *) break ;;
          esac
        done ;;
      npx|bunx|pnpx|uvx)
        TK=("${TK[@]:1}")
        while [ "${#TK[@]}" -gt 0 ]; do
          case "${TK[0]}" in -p|--package|--from|--with) TK=("${TK[@]:2}") ;; -*) TK=("${TK[@]:1}") ;; *) break ;; esac
        done ;;
      pipx)
        [ "${TK[1]:-}" = run ] || break
        TK=("${TK[@]:2}")
        while [ "${#TK[@]}" -gt 0 ] && [ "${TK[0]#-}" != "${TK[0]}" ]; do TK=("${TK[@]:1}"); done ;;
      uv)                             # uv [opts] run [opts] CMD …: CMD is the command
        j=1
        while [ "$j" -lt "${#TK[@]}" ]; do
          case "${TK[j]}" in
            --directory) abspath "${TK[j+1]:-.}" "$CURDIR"; CURDIR="$ABS"; j=$((j+2)) ;;
            --directory=*) abspath "${TK[j]#*=}" "$CURDIR"; CURDIR="$ABS"; j=$((j+1)) ;;
            --project|--with|--python|-p|--package|--extra|--group|--env-file|--index|--cache-dir|--config-file|--with-requirements|--only-group|--no-group) j=$((j+2)) ;;
            -*) j=$((j+1)) ;;
            *) break ;;
          esac
        done
        [ "${TK[j]:-}" = run ] || break
        TK=("${TK[@]:$((j + 1))}")
        while [ "${#TK[@]}" -gt 0 ]; do
          case "${TK[0]}" in
            --directory) abspath "${TK[1]:-.}" "$CURDIR"; CURDIR="$ABS"; TK=("${TK[@]:2}") ;;
            --directory=*) abspath "${TK[0]#*=}" "$CURDIR"; CURDIR="$ABS"; TK=("${TK[@]:1}") ;;
            --project|--with|--python|-p|--package|--extra|--group|--env-file|--index|--with-requirements|--only-group|--no-group|-m|--module) TK=("${TK[@]:2}") ;;
            -*) TK=("${TK[@]:1}") ;;
            *) break ;;
          esac
        done ;;
      bash|sh|zsh|dash)               # sh -c 'SCRIPT' ARG…: the script is one word
        case "${TK[1]:-}" in
          -*c*) rest=("${TK[@]:3}"); tokenize "${TK[2]:-}"; TK+=(${rest[@]+"${rest[@]}"}) ;;
          *) break ;;
        esac ;;
      [A-Za-z_]*=*) check_assign "${TK[0]}"; TK=("${TK[@]:1}") ;;
      *) break ;;
    esac
  done
  [ "${#TK[@]}" -gt 0 ] || { CURDIR="$seg_saved"; return 0; }
  cmd="${TK[0]##*/}"

  # Rule 1f: container tools, agent CLIs, privilege changes, nested claude.
  case "$cmd" in
    docker|docker-compose|dockerd|dockerd-rootless*|podman|podman-compose|nerdctl|lxc|lxd|incus|ctr|buildah|runc|crictl|opencode|codex|sudo|su|pkexec|doas|runuser|sg|newgrp)
      block "(rule 1f) — '$cmd' is a container tool, an agent CLI or a privilege change. A study session never runs one directly; container and agent runs go only through scripts/mksandbox-run, scripts/contract_local.sh or the fvh harness, and privileged commands are the human's to run." ;;
    claude)
      claude_ok || block "(rule 1f) — a nested claude with tools enabled is an agent outside this session's guard. The only nested form is the tool-less policy call: claude -p … --tools \"\" --strict-mcp-config (no --mcp-config); agent runs go through the fvh harness or scripts/contract_local.sh." ;;
  esac
  # Rule 2g: verifier poisoning by the command line.
  case "$cmd" in
    dafny|vcheck|vaudit|specfreeze) verifier_flags ;;
  esac
  if [ "$PATHSET" = 1 ]; then
    case "$cmd" in
      dafny|verus|vcheck|vaudit|specfreeze|cargo|cargo-verus|rust_verify|z3|z3-*)
        block "(rule 2g) — a PATH= prefix on '$cmd' can substitute the solver or the toolchain (a fake-green vector). Run the pinned toolchain through scripts/vcheck with a clean environment." ;;
    esac
  fi

  # Rule 1: words that are globs or existing paths, checked where they land —
  # the command word too (`* -exec`, or a scratch symlink run as a program).
  for t in "${TK[@]}"; do
    t="${t#<}"
    case "$t" in ''|-*|*'>'*) continue ;; esac
    case "$t" in
      *'*'*|*'?'*|*'['*)
        while IFS= read -r r; do
          [ -n "$r" ] || continue
          abspath "$r" "$CURDIR"
          in_spoiler "$ABS" && block "(rule 1d) — the glob '$t' expands into a reference tree. $R1D_HINT"
          in_state "$ABS" && block "(rule 1e) — the glob '$t' expands into another Claude Code session's state. $R1E_HINT"
          if [ -L "$ABS" ]; then   # a scratch symlink into Solutions/ is the same read
            realp "$ABS"
            in_spoiler "$REAL" && block "(rule 1d) — the glob '$t' expands onto a symlink into a reference tree. $R1D_HINT"
          fi
        done <<EOF
$(glob_paths "$t")
EOF
        ;;
      *)
        n=$((n + 1)); [ "$n" -le 40 ] || continue
        abspath "$t" "$CURDIR"
        if [ -e "$ABS" ] || [ -L "$ABS" ]; then check_named "$ABS" / scan; fi ;;
    esac
  done

  # Rule 2: redirect targets in this segment.
  case "$1" in
    *'>'*)
      while IFS= read -r r; do
        r="${r#>}"; r="${r#>}"; r="${r#|}"
        r="${r#"${r%%[![:space:]]*}"}"; r="${r//\"/}"; r="${r//\'/}"
        case "$r" in ''|/dev/*) continue ;; esac
        check_write "$r" "$CURDIR" "$CMD"
      done <<EOF
$(printf '%s\n' "$1" | grep -oE '>>?\|?[[:space:]]*[^[:space:]<>|;&()]+')
EOF
      ;;
  esac

  case "$cmd" in
    popd)
      # Back to a directory the hook did not see pushed (or an earlier
      # command line's): the project root, the conservative choice.
      CURDIR="$ROOT"; SHDIR="$ROOT"; return 0 ;;
    cd|pushd)
      # A bare cd goes home. cd -, cd ~-, pushd with no directory or a stack
      # rotation (+N/-N), and an argument the hook cannot resolve (cut off by
      # $(…) or `…`, $OLDPWD or another variable than the xvar spellings,
      # ~user) reset the shell's directory to the project root, the
      # conservative choice: a recursive read of it takes in the reference.
      t="${TK[1]:-}"
      case "$t" in
        -L|-P|-e|-@|--) t="${TK[2]:-}" ;;
        -n) [ "$cmd" = pushd ] && return 0 ;;     # pushd -n: the stack only
      esac
      if [ "$cmd" = cd ] && [ "${#TK[@]}" -eq 1 ]; then
        case "$SEG_NEXT" in
          '$('*|'`'*) ;;                          # cd $(…): not a bare cd
          *) CURDIR="$HOME"; SHDIR="$HOME"; return 0 ;;
        esac
      fi
      case "$t" in
        ''|-|'~-'|'~-/'*|[+-][0-9]*) CURDIR="$ROOT"; SHDIR="$ROOT"; return 0 ;;
      esac
      xvar "$t"
      case "$XV" in *'$'*|*'`'*|'~'*) CURDIR="$ROOT"; SHDIR="$ROOT"; return 0 ;; esac
      abspath "$t" "$CURDIR"; CURDIR="$ABS"; SHDIR="$ABS"
      realp "$CURDIR"
      if in_spoiler "$CURDIR" || in_spoiler "$REAL"; then block "$R1_MSG"; fi
      if in_state "$CURDIR" || in_state "$REAL"; then block "(rule 1e) — '$t' is another Claude Code session's state. $R1E_HINT"; fi
      return 0 ;;
    rg|ag|ack|ack-grep) search_check "$cmd" 1 ;;
    rga) search_check rg 1 ;;                       # ripgrep-all: rg's words
    grep|egrep|fgrep|zgrep|ugrep|ug|pcregrep|pcre2grep)
      g=grep; case "$cmd" in ugrep|ug) g=ugrep ;; esac
      for t in "${TK[@]:1}"; do
        case "$t" in
          --recursive|--dereference-recursive|--directories=recurse) search_check "$g" 1; break ;;
          --*) ;;
          -*[rR]*) search_check "$g" 1; break ;;
        esac
      done
      [[ " ${TK[*]} " =~ [[:space:]](-d|--directories)[[:space:]]+recurse[[:space:]] ]] && search_check "$g" 1 ;;
    diff|colordiff) diff_check ;;
    fd|fdfind) fd_check ;;
    ctags|ctags-universal|ctags-exuberant|uctags|exuberant-ctags|universal-ctags) index_check ctags ;;
    cscope) index_check cscope ;;
    git) git_check ;;
    find) find_check ;;
    pytest|py.test) pytest_check 1 ;;
    vaudit) vaudit_writes 0 ;;
    python|python3|python3.*)
      [ "${TK[1]:-}" = -m ] && [ "${TK[2]:-}" = pytest ] && pytest_check 3
      t="${TK[1]:-}"
      [ "${t##*/}" = vaudit ] && vaudit_writes 1 ;;
    tee)
      for t in "${TK[@]:1}"; do case "$t" in -*) ;; *) write_word "$t" ;; esac; done ;;
    sed|gsed|perl|ruby)
      inplace=0
      for t in "${TK[@]:1}"; do case "$t" in --in-place*) inplace=1 ;; --*) ;; -*i*) inplace=1 ;; esac; done
      if [ "$inplace" = 1 ]; then      # in-place edits need an existing file, which skips the script
        for t in "${TK[@]:1}"; do
          case "$t" in
            -*) continue ;;
            *'*'*|*'?'*|*'['*)         # a glob target: check each file it expands to
              while IFS= read -r r; do
                [ -n "$r" ] && check_write "$r" "$CURDIR" "$CMD"
              done <<EOF
$(glob_paths "$t")
EOF
              ;;
            *) abspath "$t" "$CURDIR"; [ -e "$ABS" ] && check_write "$t" "$CURDIR" "$CMD" ;;
          esac
        done
      fi ;;
    chmod|chown|chgrp|chattr|setfacl|chflags)
      # Mode and owner changes are writes: a hook without its execute bit
      # would not run, and the wiring's `bash <path>` is the other half.
      for t in "${TK[@]:1}"; do
        case "$t" in
          -*) ;;
          *'*'*|*'?'*|*'['*)
            while IFS= read -r r; do [ -n "$r" ] && check_write "$r" "$CURDIR" "$CMD"; done <<EOF
$(glob_paths "$t")
EOF
            ;;
          *) check_write "$t" "$CURDIR" "$CMD" ;;
        esac
      done ;;
    tar|bsdtar|gtar) copy_reach tar ;;
    zip) copy_reach zip ;;
    7z|7za|7zr) copy_reach 7z ;;
    pax) copy_reach pax ;;
    ditto) copy_reach ditto ;;
    cp|install|rsync|ln|scp)
      case "$cmd" in cp|rsync|scp) copy_reach "$cmd" ;; esac
      copy_writes "$cmd" ;;
    mv) copy_writes mv ;;
    rm|rmdir|unlink|shred|truncate)
      for t in "${TK[@]:1}"; do case "$t" in -*) ;; *) write_word "$t" ;; esac; done ;;
    unzip) unzip_check ;;
    patch|gpatch) patch_check ;;
    ex|vi|vim|nvim|ed|red|rvim|gvim|evim|vim.basic|vim.tiny|vim.nox)
      # A non-interactive editor run (ex -sc '…|x' FILE, ed -s FILE) writes
      # its file operands; every non-option word is classified as a target.
      for t in "${TK[@]:1}"; do case "$t" in -*|+*) ;; *) write_word "$t" ;; esac; done ;;
    dd)
      for t in "${TK[@]:1}"; do case "$t" in of=*) check_write "${t#of=}" "$CURDIR" "$CMD" ;; esac; done ;;
  esac
  CURDIR="$seg_saved"
  return 0
}
bash_checks() {
  local body seg p
  # When the checkout itself lies in a refused tree (a clone under an author lane's
  # scratch, /tmp/dvl0-dv…/), "cd back to $ROOT" would name the directory refused.
  if in_spoiler "$CURDIR"; then
    in_spoiler "$ROOT/" && block "(rule 1) — the shell is inside a reference tree or an author lane's scratch ($CURDIR), and so is this checkout ($ROOT), so every path in it is refused. Run the session from a checkout outside those trees (a study clone lives under /tmp/dvl0-study-…/, never under /tmp/dvl0-dv…/)."
    block "(rule 1) — the shell is inside a reference tree ($CURDIR); cd back to $ROOT first."
  fi
  in_state "$CURDIR" && block "(rule 1e) — the shell is inside another Claude Code session's state ($CURDIR); cd back to $ROOT first."
  # Heredoc bodies are data, not commands: drop them before splitting.
  body="$(printf '%s\n' "$CMD" | awk -v q="'" '
    skip { t = $0; sub(/^\t+/, "", t); if (t == delim) skip = 0; next }
    { print
      l = $0; gsub(/["\\]/, "", l); gsub(q, "", l)
      if (match(l, /(^|[^<])<<-?[ \t]*[A-Za-z_][A-Za-z0-9_]*/)) {
        d = substr(l, RSTART, RLENGTH); sub(/^[^<]*<<-?[ \t]*/, "", d)
        delim = d; skip = 1
      } }')"
  # A backslash-newline continues the command: `cp x \⏎ dafny/Q/…` is one
  # cp. Joined after the heredoc bodies are gone (inside a quoted heredoc a
  # backslash is literal; where the shell would join an unquoted one, the
  # hook checks more than the shell runs, the safe side).
  body="${body//\\$'\n'/}"
  # fd duplications (2>&1, >&2) are not file writes; &> is a plain redirect.
  body="$(printf '%s\n' "$body" | sed -E 's/[0-9]*[<>]&[0-9-]+//g; s/&>>?/>/g')"
  # Substitutions that only print the working directory or the checkout
  # root become $PWD / $CLAUDE_PROJECT_DIR before the line is cut at $( and
  # `, so "$(pwd)/x" stays one word that abspath resolves.
  body="$(printf '%s\n' "$body" | sed -E \
    -e 's/\$\([[:space:]]*(pwd([[:space:]]+-[LP])?|realpath[[:space:]]+\.|readlink[[:space:]]+-[fem][[:space:]]+\.)[[:space:]]*\)/$PWD/g' \
    -e 's/`[[:space:]]*(pwd([[:space:]]+-[LP])?|realpath[[:space:]]+\.|readlink[[:space:]]+-[fem][[:space:]]+\.)[[:space:]]*`/$PWD/g' \
    -e 's/\$\([[:space:]]*git[[:space:]]+rev-parse[[:space:]]+--show-toplevel[[:space:]]*\)/$CLAUDE_PROJECT_DIR/g' \
    -e 's/`[[:space:]]*git[[:space:]]+rev-parse[[:space:]]+--show-toplevel[[:space:]]*`/$CLAUDE_PROJECT_DIR/g')"
  # Cut the line at && || $( ; | & ` ( ), keeping each delimiter (marked by
  # \037) so a cut made inside a quoted string can be undone below.
  local us=$'\037' line i j n m pend=0 cutscript
  # The cut, as POSIX sed: each delimiter on a line of its own behind \037
  # (backslash-newline in the replacement; GNU sed's \n there is an extension).
  cutscript="$(printf 's/(&&|\\|\\||\\$\\(|[;|&`()])/\\\n%s\\1\\\n/g' "$us")"
  local -a FR=() DL=()
  body="${body//$us/}"
  while IFS= read -r line; do
    if [ "${line:0:1}" = "$us" ]; then
      [ "${#FR[@]}" -gt 0 ] || FR+=("")
      DL[${#FR[@]}-1]+="${line:1}"; pend=1
    else
      [ "${#FR[@]}" -gt 0 ] && [ "$pend" = 0 ] && DL[${#FR[@]}-1]+=$'\n'
      FR+=("$line"); pend=0
    fi
  done <<EOF
$(printf '%s\n' "$body" | sed -E "$cutscript")
EOF
  # The quote state at each cut, in one pass (a cut does not change it).
  # Every fragment is checked on its own, except one that starts outside
  # quotes and ends inside them (`grep -rn "a|b" dafny` cut at the |): it is
  # checked as the whole command instead, joined up to the fragment where the
  # quote closes, so its pattern and paths are the shell's. The fragments
  # inside the quote are still checked on their own. Linear: no two such
  # joins overlap.
  local -a SS=() ES=()
  n="${#FR[@]}"; m=0
  for ((i = 0; i < n; i++)); do
    SS[i]="$m"; tokenize "${FR[i]}" "$m"; ES[i]="$TOK_ST"; m="$TOK_ST"
  done
  # A subshell, ( … ) or $( … ), keeps its cd to itself: the shell's directory
  # is saved at the opening cut and restored at the closing one, a ) in the
  # quote state its opener was cut in (cuts inside single quotes, and a bare
  # ( or ) inside double quotes, are text). A ) with nothing saved (a case
  # pattern) changes nothing.
  local -a SVC=() SVS=() SVQ=()
  local k
  i=0
  while [ "$i" -lt "$n" ]; do
    seg="${FR[i]}"
    if [ "${SS[i]}" = 0 ] && [ "${ES[i]}" != 0 ]; then
      m="$seg"; j="$i"
      while [ "${ES[j]}" != 0 ] && [ $((j + 1)) -lt "$n" ]; do
        m+="${DL[j]:-}${FR[j+1]}"; j=$((j + 1))
      done
      [ "${ES[j]}" = 0 ] && seg="$m"
    fi
    SEG_NEXT="${DL[i]:-}"
    seg_check "$seg"
    case "${DL[i]:-}:${ES[i]}" in
      '(:0'|'$(:0'|'$(:2') SVC+=("$CURDIR"); SVS+=("$SHDIR"); SVQ+=("${ES[i]}") ;;
      '):0'|'):2')
        k=$(( ${#SVC[@]} - 1 ))
        if [ "$k" -ge 0 ] && [ "${SVQ[k]}" = "${ES[i]}" ]; then
          CURDIR="${SVC[k]}"; SHDIR="${SVS[k]}"
          unset "SVC[$k]" "SVS[$k]" "SVQ[$k]"
        fi ;;
    esac
    i=$((i + 1))
  done
  # Script one-liners that write: protected paths named anywhere in the text.
  if [[ "$CMD" =~ $RX_SCRIPT ]] && [[ "$CMD" =~ $RX_SCRIPT_WRITES ]]; then
    while IFS= read -r p; do
      [ -n "$p" ] && check_write "$p" "$CURDIR" "$CMD"
    done <<EOF
$(printf '%s\n' "$CMD" | grep -oE "$RX_PROT")
EOF
  fi
}

# --- Registry ids (rule 1b for verifier MCP targets). -------------------------
# Without a registry, fall back to the id shape check_course_map.py enforces.
registry_ids() {
  if [ -f "$ROOT/MODULES.toml" ]; then
    grep -oE '^[[:space:]]*id[[:space:]]*=[[:space:]]*"[^"]+"' "$ROOT/MODULES.toml" 2>/dev/null \
      | sed -E 's/.*"([^"]+)"/\1/'
  fi
}
target_ok() {   # T — a registry id, a learner or given package, or a path in this checkout
  local t="$1" up
  up="$(printf '%s' "$t" | tr '[:lower:]' '[:upper:]')"
  if [ -f "$ROOT/MODULES.toml" ]; then
    registry_ids | grep -Fxq -- "$up" && return 0
  else
    [[ "$up" =~ ^[QR][0-9][0-9]$ ]] && return 0
  fi
  [[ "$t" =~ ^[qr][0-9][0-9]_[a-z0-9_]+$ ]] && return 0
  [[ "$t" =~ ^(qg|rg)_[a-z0-9_]+$ ]] && return 0
  case "$t" in
    */*|*.dfy|*.rs|*.toml|*.py)
      abspath "$t" "$ROOT"; realp "$ABS"
      case "$ABS/" in "$ROOT"/*|"$RROOT"/*) return 0 ;; esac ;;
  esac
  return 1
}

# =============================================================================
# Delegation, skill and web tools: only the rules that concern them.
case "$TOOL_NAME" in
  Workflow|ScheduleWakeup)
    block "(rule 1f) — $TOOL_NAME starts a workflow or schedules background work. Course skills run only in their own session (CLAUDE.md §Session hygiene), with no workflows or background jobs. Continue in this session; research agent runs go through the course harness." ;;
  Skill)
    case "$SKILL" in
      local-assistant|*:local-assistant|local-assistant:*|local-assistant\ *)
        block "(rule 1f) — the local-assistant skill runs opencode with file tools, which ignores this guard. Agent runs go only through scripts/mksandbox-run, scripts/contract_local.sh or the fvh harness." ;;
    esac
    exit 0 ;;
  Monitor)
    # A WebSocket source (no command): the web tools' rules.
    if [ -z "$CMD" ]; then
      [ -n "$CONTRACT" ] && block "(rule 2c) — Monitor's WebSocket source: $R2C_MSG"
      if [ -n "$URL" ] && printf '%s\n' "$URL" | grep -Eq "$RX_PATH"; then block "$R1_MSG"; fi
      exit 0
    fi ;;
  WebFetch|WebSearch)
    [ -n "$CONTRACT" ] && block "(rule 2c) — $TOOL_NAME: $R2C_MSG"
    if [ "$TOOL_NAME" = WebFetch ] && [ -n "$URL" ] && printf '%s\n' "$URL" | grep -Eq "$RX_PATH"; then block "$R1_MSG"; fi
    exit 0 ;;
esac

if [ -n "$IS_SHELL" ] && [ -n "$CMD" ]; then
  # Rule 2c's agent list first while a contract runs (DV5d): `fvh unseal`
  # also names held-out material (rule 1c below), and a contractor is told
  # the contract's reason.
  if [ -n "$CONTRACT" ] && printf '%s\n' "$CMDJ" | grep -Eq "$RX_2C_AGENT"; then
    block "(rule 2c) — this starts another agent or a model run (contract_local.sh, fvh run/resume/contract-local), unseals held-out cards (fvh unseal) or makes a network fetch (get_bench.sh), and $R2C_MSG A contractor never starts another agent."
  fi
  # Rule 1c: held-out material.
  if printf '%s\n' "$CMDJ" | grep -Eq "$RX_HIDDEN"; then
    block "(rule 1c) — this names held-out grading material (Hidden/, an unsealed tree, the hidden grader, or an age archive). Claude never unseals, decrypts or names it, not even to exclude it; the learner runs the grader themselves. Scope a search by naming the directories you mean."
  fi
  # Rule 1f: container daemons, sockets, the docker SDK, the local assistant.
  if printf '%s\n' "$CMDJ" | grep -Eq "$RX_1F_ANY"; then
    block "(rule 1f) — this line reaches a container daemon, the docker SDK or the local-assistant agent. Container and agent runs go only through scripts/mksandbox-run, scripts/contract_local.sh or the fvh harness. To write prose that mentions them, use the Write tool."
  fi
  # Rule 2g: environment that changes how the verifier runs.
  if printf '%s\n' "$CMDJ" | grep -Eq "$RX_POISON"; then
    block "(rule 2g) — this line changes how the verifier runs (VERUS_Z3_PATH, VERUS_EXTRA_ARGS, RUSTC_WRAPPER, RUSTFLAGS with --cfg/verus_only, or a Dafny --plugin): a fake-green vector. Run the pinned toolchain through scripts/vcheck with a clean environment."
  fi
  # Rule 1b: author-only steps read the reference or rewrite a pin a study
  # session is checked against.
  if printf '%s\n' "$CMDJ" | grep -Eq "$RX_AUTHOR"; then
    block "(rule 1b) — this runs an author-only step: a reference lint, update_rubric_pins.sh, pins.py --update/--ref, vcheck or vaudit --ref, specfreeze --pin, firsttry --empty-body, test_corpus.py --update, mksandbox-run --author/--attest, get_bench.sh --pin/--pin-pool or the fvh fixture recorder (fvh.tools.record). Each reads the reference, rewrites a pin a study session is checked against, or runs the memory-heavy empty-body gate; the author runs them in the authoring worktree. The learner forms stay open: scripts/ci.sh, vcheck [--gate] <unit>, vaudit <unit>, specfreeze --check <ID>, firsttry.sh <ID> --check/--report/--exit, pins.py <ID> or --ci, test_corpus.py --list/--ci/--only <SEL>. To read a script, use the Read tool."
  fi
  # Rule 2c (DV4): no other agent, container run or network fetch while a
  # contract runs; mksandbox-run's --check-access, --dry-run and --build-verify
  # stay open (--build-verify only as a whole word: its mode group excludes a run).
  # (Its agent list, RX_2C_AGENT, is checked above, before rule 1c.)
  if [ -n "$CONTRACT" ]; then
    while IFS= read -r p; do
      [ -n "$p" ] || continue
      case "$p" in *--check-access*|*--dry-run*) continue ;; esac
      [[ "$p" =~ (^|[[:space:]])--build-verify([[:space:]]|$) ]] && continue
      block "(rule 2c) — scripts/mksandbox-run starts a sandbox container (only --check-access, --dry-run and --build-verify stay open), and $R2C_MSG A contractor never starts another agent."
    done <<EOF
$(printf '%s\n' "$CMDJ" | grep -oE "${B}mksandbox-run${E}[^;&|]*")
EOF
  fi
  # Rule 1b: a script one-liner that puts CI in the environment (shell
  # assignments are check_assign's, in bash_checks).
  if [[ "$CMDJ" =~ $RX_SCRIPT ]] && printf '%s\n' "$CMDJ" | grep -Eq "$RX_CI_SCRIPT"; then
    block "$R1B_CI"
  fi
  if printf '%s\n' "$CMDJ" | grep -Eq "$RX_BUILD_TOOL" && printf '%s\n' "$CMDJ" | grep -Eq "$RX_REFNAME"; then
    block "(rule 1b) — building, verifying or testing the reference prints its diagnostics and output. Study-mode builds: scripts/vcheck on a registry unit or a scratch file, cargo verus verify -p <learner crate>, uv run --directory harness pytest, make -C paper paper."
  fi
fi

# Rule 1b: verifier MCP calls build this checkout's registry units, nothing else.
if [ -n "$IS_MCP" ]; then
  [ -n "$REFFLAG" ] && block "(rule 1b) — this verifier call asks for a reference build (ref/reference: true). The reference is built only by CI and authors."
  if printf '%s\n' "$STRICT" | grep -Eq '(^|[[:space:]])--ref(erence)?([=[:space:]]|$)'; then
    block "(rule 1b) — this verifier call asks for a reference build (--ref). The reference is built only by CI and authors."
  fi
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    abspath "$p" "$ROOT"; realp "$ABS"
    case "$ABS/" in "$ROOT"/*|"$RROOT"/*) continue ;; esac
    case "$REAL/" in "$ROOT"/*|"$RROOT"/*) continue ;; esac
    block "(rule 1b) — a verifier call may only build this checkout ($ROOT); another project could make the reference its default."
  done <<EOF
$PROJ
EOF
  while IFS= read -r t; do
    [ -n "$t" ] || continue
    target_ok "$t" || block "(rule 1b) — verifier target '$t' is not a MODULES.toml module id, a learner or given package, or a path in this checkout."
  done <<EOF
$TARGETS
EOF
fi

# Rule 1: names, in path-like fields.
if [ -n "$STRICT" ]; then
  STRICT_W="$STRICT"                     # bare words: the registry vocabulary passes on a shell line
  [ -n "$IS_SHELL" ] && STRICT_W="$(unvocab "$STRICT")"
  if printf '%s\n' "$STRICT" | grep -Eq "$RX_PATH|$RX_IMP_RS|$RX_IMP_CLI|$RX_IMP_SH" \
     || printf '%s\n' "$STRICT_W" | grep -Eq "$RX_WORD"; then
    block "$R1_MSG"
  fi
fi
# Rule 1c: the held-out tree is never named, not even to exclude it.
if [ -n "$STRICT" ] && printf '%s\n' "$STRICT" | grep -Eq "${B}Hidden${E}"; then
  block "(rule 1c) — this names the held-out tree (Hidden/). Held-out material is never named, not even to exclude it: scope a search by naming the directories you mean (grep -rn PAT dafny verus docs instructor)."
fi
# Rule 1e: other sessions' Claude Code state named in a path-like field.
if [ -n "$STRICT" ]; then
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    abspath "$p" "$CWD"
    in_state "$ABS" && block "(rule 1e) — '$p' is another Claude Code session's state (a transcript, session directory, file history or scratch directory). $R1E_HINT"
  done <<EOF
$(state_words "$STRICT")
EOF
fi
# Rules 2f, 2s, 2g first for the file-editing tools: an edit of guard
# configuration reports 2g even when its new text names the reference trees.
case "$TOOL_NAME" in
  Edit|Write|MultiEdit|NotebookEdit)
    while IFS= read -r p; do [ -n "$p" ] && check_write "$p" "$CWD" "$TEXT" early; done <<EOF
$FPATHS
EOF
    ;;
esac
# Rule 1: written content (path forms and include/import forms only).
if [ -n "$TEXT" ] && printf '%s\n' "$TEXT" | grep -Eq "$RX_TEXT"; then
  block "(rule 1) — this content names the reference material (a Solutions/ path, an include, mod, use, extern crate, Cargo dependency, dfyconfig entry or Python import of the reference, or the course cache). Never write a file that includes, imports or reads it; scratch probes import the given layers and the learner's own files only."
fi

# Rules 1, 1d, 1e, 2c: named files, through symlinks; MCP and LSP files also by
# their include/import forms (the server checks the file it is pointed at).
case "$TOOL_NAME" in
  mcp__firecrawl__firecrawl_parse)
    # This is a file reader, not a verifier: resolve filePath from the caller's
    # cwd, as Read does. In particular, a relative scratch symlink must not be
    # checked against the project root instead of the file the caller names.
    while IFS= read -r p; do [ -n "$p" ] && check_named "$p" "$CWD"; done <<EOF
$FPATHS
EOF
    ;;
  mcp__*)
    while IFS= read -r p; do [ -n "$p" ] && check_named "$p" "$ROOT" scan; done <<EOF
$FPATHS
EOF
    ;;
  LSP)
    while IFS= read -r p; do [ -n "$p" ] && check_named "$p" "$CWD" scan; done <<EOF
$FPATHS
EOF
    ;;
  *)
    while IFS= read -r p; do [ -n "$p" ] && check_named "$p" "$CWD"; done <<EOF
$FPATHS
$SPATHS
EOF
    ;;
esac

# Rule 1d for the Grep tool: with no path it searches from the working
# directory, and a search whose reach takes in a reference tree returns
# reference text. Glob is left alone — it returns names, not contents.
if [ "$TOOL_NAME" = Grep ]; then
  gdirs="$SPATHS"; [ -n "$gdirs" ] || gdirs="$CWD"
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    abspath "$p" "$CWD"
    reach_one "$ABS" "$p" "a Grep rooted at" "rule 1d"
  done <<EOF
$gdirs
EOF
fi

# Rules 1, 1b, 1d, 1e, 1f, 2 for shell commands.
[ -n "$IS_SHELL" ] && [ -n "$CMD" ] && bash_checks

# Rules 2, 2c, 2s, 2f, 2g for the file-editing tools.
case "$TOOL_NAME" in
  Edit|Write|MultiEdit|NotebookEdit)
    while IFS= read -r p; do [ -n "$p" ] && check_write "$p" "$CWD" "$TEXT"; done <<EOF
$FPATHS
EOF
    ;;
esac

exit 0
