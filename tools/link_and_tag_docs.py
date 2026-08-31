#!/usr/bin/env python
"""Retrofits docs/**/*.md (excluding docs/agents/research/transcripts/) with:

  1. YAML frontmatter tags, by folder/file convention (see CLAUDE.md
     "Tags + graph color groups").
  2. Stable block-IDs (`^N`) on every numbered `## N. Title` heading, so
     section links survive future title edits.
  3. Obsidian [[wikilinks]] in place of plain-text filename/section mentions
     (see CLAUDE.md "Cross-reference links").

Idempotent and safe to re-run any time new docs land (e.g. from an
autonomous agent committing to docs/): already-tagged files are left alone,
already-added block-IDs are not duplicated, and text already inside
`[[...]]` (or inside a backtick-wrapped absolute path) is never re-matched,
so re-running never double-wraps or corrupts existing links.

Known limitation: resolving a bare `§N` reference to "which document owns
heading N" is a heuristic (last-file-mentioned-on-this-line > current
document's own numbering > iteration_findings.md), not a certainty -- a
document that discusses another doc's section by number without ever
naming that doc on the same line can still resolve wrong. Spot-check the
diff after running this against a newly-added doc that itself has numbered
`## N.` headings.
"""
import os
import re
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(REPO, "docs")


def all_md_files():
    out = []
    for root, dirs, files in os.walk(DOCS):
        if "transcripts" in root.replace("\\", "/").split("/"):
            continue
        for f in files:
            if f.endswith(".md"):
                out.append(os.path.join(root, f))
    return out


def rel_of(f):
    return os.path.relpath(f, DOCS).replace("\\", "/")[:-3]


# ---------------------------------------------------------------- tagging --

def classify(rel):
    if rel.startswith("concepts/"):
        return "concept"
    if rel == "iteration_findings":
        return "findings"
    if rel.startswith("agents/research/"):
        return "research-digest"
    if rel.startswith("agents/"):
        return "agent-loop"
    if rel in ("thrust_vectoring_drone_buildspec", "thrust_vectoring_results"):
        return "design-study"
    if rel in ("throw_planning", "arm_v1_status"):
        return "historical"
    return None


def add_tags(files):
    changed, skipped_fm, unclassified = [], [], []
    for f in files:
        rel = rel_of(f)
        with open(f, encoding="utf-8") as fh:
            text = fh.read()
        if text.startswith("---\n"):
            skipped_fm.append(rel)
            continue
        tag = classify(rel)
        if not tag:
            unclassified.append(rel)
            continue
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(f"---\ntags:\n  - {tag}\n---\n\n{text}")
        changed.append((rel, tag))
    return changed, skipped_fm, unclassified


# ------------------------------------------------------ heading block-ids --

HEADING_LINE_RE = re.compile(r"^(## )(\d+[a-z]?)(\. .+?)(\s*\^\S+)?$")


def add_block_ids(files):
    """Returns rel -> set(heading numbers) for every file with numbered headings."""
    per_file_headings = {}
    for f in files:
        rel = rel_of(f)
        with open(f, encoding="utf-8") as fh:
            lines = fh.readlines()
        nums, changed = set(), False
        for i, line in enumerate(lines):
            m = HEADING_LINE_RE.match(line.rstrip("\n"))
            if m:
                prefix, num, rest, existing_id = m.groups()
                nums.add(num)
                if not existing_id:
                    lines[i] = f"{prefix}{num}{rest} ^{num}\n"
                    changed = True
        if nums:
            per_file_headings[rel] = nums
        if changed:
            with open(f, "w", encoding="utf-8") as fh:
                fh.writelines(lines)
    return per_file_headings


# --------------------------------------------------------------- linking --

def build_filename_index(rel_to_base):
    base_counts = Counter(rel_to_base.values())
    candidates = []
    for rel, base in rel_to_base.items():
        candidates.append((f"docs/{rel}.md", rel))
        candidates.append((f"{rel}.md", rel))
        if base_counts[base] == 1:
            candidates.append((f"{base}.md", rel))
        m = re.match(r"^concepts/(\d{2})-", rel)
        if m:
            candidates.append((f"concepts/{m.group(1)}", rel))
    candidates.sort(key=lambda t: -len(t[0]))
    return candidates


PROTECT_RE = re.compile(r"\[\[[^\]]*\]\]|`/[^`\n]*`")


def linkify_files(files, rel_to_base, per_file_headings, concept_num_to_rel):
    candidates = build_filename_index(rel_to_base)
    mention_to_rel = dict(candidates)
    fname_alt = "|".join(re.escape(m) for m, _ in candidates)

    master_re = re.compile(
        r"\[`(?P<mdinner>" + fname_alt + r")`\]\((?P=mdinner)\)"
        r"|(?<![\w-])(?P<fname>" + fname_alt + r")"
        r"|§(?P<r1>\d{1,2}[a-z]?)(?P<dash>[–-])(?P<r2>\d{1,2}[a-z]?)"
        r"|§(?P<s1>\d{1,2}[a-z]?)"
    )

    def note_target(rel):
        base = rel_to_base[rel]
        return rel if base == "README" else base

    def resolve_section(num, current_rel, last_ref_rel, sep):
        if re.match(r"^0\d$", num) and num in concept_num_to_rel:
            rel = concept_num_to_rel[num]
            return None if rel == current_rel else f"[[{note_target(rel)}{sep}"
        key = num.lstrip("0") or "0"
        if last_ref_rel and last_ref_rel in per_file_headings and key in per_file_headings[last_ref_rel]:
            if last_ref_rel == current_rel:
                return f"[[#^{key}{sep}"
            return f"[[{note_target(last_ref_rel)}#^{key}{sep}"
        if current_rel in per_file_headings and key in per_file_headings[current_rel]:
            return f"[[#^{key}{sep}"
        if key in per_file_headings.get("iteration_findings", set()):
            if current_rel == "iteration_findings":
                return f"[[#^{key}{sep}"
            return f"[[iteration_findings#^{key}{sep}"
        return None

    def process_line(line, current_rel, sep):
        state = {"last_ref_rel": None}

        def _sub(m):
            if m.group("mdinner") or m.group("fname"):
                mention = m.group("mdinner") or m.group("fname")
                rel = mention_to_rel[mention]
                state["last_ref_rel"] = rel
                return f"[[{note_target(rel)}{sep}{mention}]]"
            if m.group("r1"):
                r1, dash, r2 = m.group("r1"), m.group("dash"), m.group("r2")
                p1 = resolve_section(r1, current_rel, state["last_ref_rel"], sep)
                p2 = resolve_section(r2, current_rel, state["last_ref_rel"], sep)
                part1 = f"{p1}§{r1}]]" if p1 else f"§{r1}"
                part2 = f"{p2}{r2}]]" if p2 else r2
                return part1 + dash + part2
            if m.group("s1"):
                num = m.group("s1")
                p = resolve_section(num, current_rel, state["last_ref_rel"], sep)
                return f"{p}§{num}]]" if p else f"§{num}"
            return m.group(0)

        return master_re.sub(_sub, line)

    heading_re = re.compile(r"^#{1,6} ")
    table_row_re = re.compile(r"^\s*\|")
    backtick_span_re = re.compile(r"`([^`\n]*)`")

    def unwrap_backticks_around_links(line):
        def _sub(m):
            inner = m.group(1)
            return inner if "[[" in inner else m.group(0)
        return backtick_span_re.sub(_sub, line)

    def process_line_protected(line, current_rel, sep):
        # Protect spans that must never be re-matched: existing [[wikilinks]]
        # (idempotency) and backtick-wrapped absolute paths (`/mnt/...` etc,
        # which are machine-specific citations, not portable doc refs).
        protected = []

        def _stash(m):
            protected.append(m.group(0))
            return f"\x00{len(protected) - 1}\x00"

        stashed_line = PROTECT_RE.sub(_stash, line)
        result = process_line(stashed_line, current_rel, sep)
        result = unwrap_backticks_around_links(result)

        def _restore(m):
            return protected[int(m.group(1))]

        return re.sub(r"\x00(\d+)\x00", _restore, result)

    changed_files = []
    for f in files:
        rel = rel_of(f)
        with open(f, encoding="utf-8") as fh:
            original = fh.read()
        out_lines = []
        for line in original.split("\n"):
            if heading_re.match(line):
                out_lines.append(line)
                continue
            sep = "::" if table_row_re.match(line) else "|"
            out_lines.append(process_line_protected(line, rel, sep))
        text = "\n".join(out_lines)
        if text != original:
            changed_files.append(f)
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(text)
    return changed_files


def main():
    files = all_md_files()

    print("--- tags ---")
    tag_changed, skipped_fm, unclassified = add_tags(files)
    for rel, tag in tag_changed:
        print(f"  tagged {tag:16s} {rel}")
    if unclassified:
        print("  UNCLASSIFIED (add a rule to classify(), or tag by hand):", unclassified)

    print("--- block-ids ---")
    per_file_headings = add_block_ids(files)

    rel_to_base = {rel_of(f): rel_of(f).split("/")[-1] for f in files}
    concept_num_to_rel = {}
    for rel in rel_to_base:
        m = re.match(r"^concepts/(\d{2})-", rel)
        if m:
            concept_num_to_rel[m.group(1)] = rel

    print("--- links ---")
    link_changed = linkify_files(files, rel_to_base, per_file_headings, concept_num_to_rel)
    for f in link_changed:
        print(" ", os.path.relpath(f, REPO))

    print(f"\n{len(tag_changed)} newly tagged, {len(link_changed)} files with new/updated links.")
    if unclassified:
        print("Review UNCLASSIFIED files above -- they were left untouched.")


if __name__ == "__main__":
    main()
