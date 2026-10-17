# paper/Makefile — the written track's build. `make -C paper paper` green is the
# written track's definition of done, as `scripts/vcheck --gate` is for code.
#
# Targets:
#   make paper            build every learner-facing pair of both tracks:
#                         [RQ]NN_problems.tex with its [RQ]NN_answers.tex (Q
#                         blueprints, paper cards and lab pre-registrations ship
#                         as such a pair; MODULES.toml `paper`). FAILS if nothing
#                         matches (an empty set means a broken glob, not a green
#                         written track) and if any file lacks its partner.
#                         The templates are never built here.
#   make paper-solutions  build solutions/*.tex: scripts/ci.sh (CI=true) and the
#                         course author's linked authoring worktree only; it
#                         refuses anywhere else (exit 3). Each latexmk run logs
#                         to solutions/<name>.latexmk.log and is never echoed;
#                         the console shows only "built N" or the failing file
#                         names.
#   make clean            remove the LaTeX build products of the learner-facing
#                         files (not of solutions/).
#
# `paper` never touches solutions/, so a learner's (or a study-mode Claude
# session's) build cannot compile or print a reference solution. The
# spoiler-guard hook also refuses any command that runs `paper-solutions`.
#
# The paper-solutions self-check is the spec's author-script test (spec §7.4):
# CI=true, or a linked git worktree whose HEAD is not on a learner branch
# (leobwang-*). It is not a guard ("CI=true is one word away"); the hook is.
#
# Engine: pdflatex through latexmk (see preamble.tex for Unicode notes).

LATEXMK       ?= latexmk
LATEXMK_FLAGS ?= -pdf -interaction=nonstopmode -halt-on-error

PROBLEMS   := $(wildcard [RQ][0-9][0-9]_problems.tex)
ANSWERS    := $(wildcard [RQ][0-9][0-9]_answers.tex)
SOLUTIONS  := $(wildcard solutions/*.tex)

TEXFILES   := $(PROBLEMS) $(ANSWERS)
PDFS       := $(TEXFILES:.tex=.pdf)

PROBLEM_IDS := $(patsubst %_problems.tex,%,$(PROBLEMS))
ANSWER_IDS  := $(patsubst %_answers.tex,%,$(ANSWERS))
UNPAIRED    := $(sort $(filter-out $(ANSWER_IDS),$(PROBLEM_IDS)) $(filter-out $(PROBLEM_IDS),$(ANSWER_IDS)))

# Shell test: true for scripts/ci.sh (CI=true) and for a linked worktree whose
# HEAD is not on a leobwang-* branch.
AUTHOR_OK = { [ "$${CI:-}" = true ] || { \
  gd=$$(git rev-parse --path-format=absolute --git-dir 2>/dev/null) && \
  cdir=$$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null) && \
  [ "$$gd" != "$$cdir" ] && \
  ! git symbolic-ref --short -q HEAD 2>/dev/null | grep -q '^leobwang-'; }; }

.PHONY: paper _paper-pdfs paper-solutions clean

paper:
ifeq ($(strip $(TEXFILES)),)
	@echo "paper: no [RQ]NN_problems.tex / [RQ]NN_answers.tex files matched; nothing built. An empty set means a broken glob, not a green written track." >&2; exit 1
else ifneq ($(strip $(UNPAIRED)),)
	@echo "paper: unpaired written-track files for: $(UNPAIRED). Every <ID>_problems.tex needs its <ID>_answers.tex and the reverse; nothing built." >&2; exit 1
else
	@$(MAKE) --no-print-directory _paper-pdfs
	@echo "paper: built $(words $(PDFS)) document(s); the written track is green"
endif

# Internal: the PDFs of the pairs (run only through `paper`, after its checks).
_paper-pdfs: $(PDFS)
	@:

# Learner-facing documents: latexmk's output on the console, as usual.
%.pdf: %.tex preamble.tex
	$(LATEXMK) $(LATEXMK_FLAGS) -output-directory=$(dir $@) $<

paper-solutions:
	@$(AUTHOR_OK) || { echo "paper-solutions: refused; the reference build runs only under scripts/ci.sh (CI=true) or in the course author's linked authoring worktree" >&2; exit 3; }
ifeq ($(strip $(SOLUTIONS)),)
	@echo "paper-solutions: no solutions/*.tex files matched; nothing built. Check the glob." >&2; exit 1
else
	@n=0; failed=0; \
	for f in $(SOLUTIONS); do \
	  if $(LATEXMK) $(LATEXMK_FLAGS) -output-directory=solutions "$$f" > "$${f%.tex}.latexmk.log" 2>&1; then \
	    n=$$((n + 1)); \
	  else \
	    echo "paper-solutions: FAILED $$f" >&2; failed=$$((failed + 1)); \
	  fi; \
	done; \
	if [ "$$failed" -gt 0 ]; then exit 1; fi; \
	echo "paper-solutions: built $$n document(s)"
endif

clean:
	rm -f [RQ][0-9][0-9]_*.aux [RQ][0-9][0-9]_*.log [RQ][0-9][0-9]_*.fls \
	      [RQ][0-9][0-9]_*.fdb_latexmk [RQ][0-9][0-9]_*.synctex.gz \
	      [RQ][0-9][0-9]_*.out [RQ][0-9][0-9]_*.toc [RQ][0-9][0-9]_*.pdf \
	      template_*.aux template_*.log template_*.fls template_*.fdb_latexmk \
	      template_*.synctex.gz template_*.out template_*.toc template_*.pdf
