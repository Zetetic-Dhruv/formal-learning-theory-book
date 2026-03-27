#!/usr/bin/env python3
"""Validate that all BibTeX keys referenced in flt_concept_graph.json
resolve against flt_bibliography.bib, and report orphan/malformed keys.

Exit code 0: no missing or malformed keys.
Exit code 1: at least one missing or malformed key found.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Trailing-comma tolerance: the graph JSON uses trailing commas in places,
# which is invalid per the JSON spec.  We strip them before parsing.
_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


def load_json_tolerant(path: Path) -> dict:
    """Load a JSON file, tolerating trailing commas."""
    text = path.read_text(encoding="utf-8")
    cleaned = _TRAILING_COMMA_RE.sub(r"\1", text)
    return json.loads(cleaned)


# BibTeX key pattern: AuthorName(s)YYYY with optional trailing letter
BIBTEX_KEY_RE = re.compile(r"^[A-Za-z]+[0-9]{4}[a-z]?$")

# Pattern to extract @type{KEY, from .bib files
BIB_ENTRY_RE = re.compile(r"@\w+\{([^,\s]+)", re.MULTILINE)


def parse_bib_keys(bib_path: Path) -> set:
    """Extract all entry keys from a BibTeX file."""
    text = bib_path.read_text(encoding="utf-8")
    return set(BIB_ENTRY_RE.findall(text))


def looks_like_bibtex_key(value: str) -> bool:
    """Return True if the string matches BibTeX key format (not prose)."""
    return bool(BIBTEX_KEY_RE.match(value))


def collect_graph_keys(graph: dict) -> dict:
    """Walk the concept graph and collect all citation-bearing field values.

    Returns a dict mapping each key string to a list of locations where
    it was referenced (for diagnostic output).
    """
    refs = {}  # key -> [location_description, ...]

    def record(key: str, location: str):
        refs.setdefault(key, []).append(location)

    # --- Nodes ---
    for node in graph.get("nodes", []):
        node_id = node.get("id", "<unknown>")

        # bib_keys array
        for k in node.get("bib_keys", []):
            if isinstance(k, str) and looks_like_bibtex_key(k):
                record(k, f"node '{node_id}' bib_keys")

        # provenance.introduced_by / provenance.proved_by
        prov = node.get("provenance", {})
        if isinstance(prov, dict):
            for field in ("introduced_by", "proved_by"):
                val = prov.get(field)
                if isinstance(val, str) and looks_like_bibtex_key(val):
                    record(val, f"node '{node_id}' provenance.{field}")
                elif isinstance(val, list):
                    for v in val:
                        if isinstance(v, str) and looks_like_bibtex_key(v):
                            record(v, f"node '{node_id}' provenance.{field}")

    # --- Edges ---
    for i, edge in enumerate(graph.get("edges", [])):
        src = edge.get("source", "?")
        tgt = edge.get("target", "?")
        rel = edge.get("relation", "?")
        label = f"edge {src}-[{rel}]->{tgt}"

        val = edge.get("citation")
        if isinstance(val, str) and looks_like_bibtex_key(val):
            record(val, label)
        elif isinstance(val, list):
            for v in val:
                if isinstance(v, str) and looks_like_bibtex_key(v):
                    record(v, label)

    return refs


def check_malformed(keys: set) -> list:
    """Return keys that don't match the canonical BibTeX key pattern."""
    # This checks bib-file keys themselves
    malformed = []
    for k in sorted(keys):
        if not BIBTEX_KEY_RE.match(k):
            malformed.append(k)
    return malformed


def main():
    parser = argparse.ArgumentParser(
        description="Validate bibliography cross-references between graph and bib."
    )
    default_root = Path(__file__).resolve().parent.parent
    parser.add_argument(
        "--graph",
        type=Path,
        default=default_root / "flt_concept_graph.json",
        help="Path to concept graph JSON",
    )
    parser.add_argument(
        "--bib",
        type=Path,
        default=default_root / "flt_bibliography.bib",
        help="Path to BibTeX bibliography",
    )
    args = parser.parse_args()

    # --- Load data ---
    if not args.graph.exists():
        print(f"ERROR: Graph file not found: {args.graph}", file=sys.stderr)
        sys.exit(1)
    if not args.bib.exists():
        print(f"ERROR: Bib file not found: {args.bib}", file=sys.stderr)
        sys.exit(1)

    graph = load_json_tolerant(args.graph)
    bib_keys = parse_bib_keys(args.bib)
    graph_refs = collect_graph_keys(graph)

    # --- Analysis ---
    referenced_keys = set(graph_refs.keys())
    missing = sorted(referenced_keys - bib_keys)
    orphans = sorted(bib_keys - referenced_keys)
    malformed_bib = check_malformed(bib_keys)

    has_errors = False

    # --- Report ---
    print("=" * 65)
    print("  Bibliography Link Validation")
    print("=" * 65)
    print()
    print(f"  BibTeX entries in .bib file:       {len(bib_keys)}")
    print(f"  Unique keys referenced in graph:    {len(referenced_keys)}")
    print()

    # Missing keys
    if missing:
        has_errors = True
        print(
            f"FAIL  Missing keys ({len(missing)}): referenced in graph but not in .bib"
        )
        print("-" * 65)
        for k in missing:
            locs = graph_refs[k]
            print(f"  {k}")
            for loc in locs:
                print(f"      -> {loc}")
        print()
    else:
        print("PASS  No missing keys.")
        print()

    # Malformed keys in bib
    if malformed_bib:
        has_errors = True
        print(
            f"FAIL  Malformed bib keys ({len(malformed_bib)}): do not match pattern [A-Za-z]+[0-9]{{4}}[a-z]?"
        )
        print("-" * 65)
        for k in malformed_bib:
            print(f"  {k}")
        print()
    else:
        print("PASS  All bib keys are well-formed.")
        print()

    # Orphan keys (warning only)
    if orphans:
        print(
            f"WARN  Orphan keys ({len(orphans)}): in .bib but never referenced in graph"
        )
        print("-" * 65)
        for k in orphans:
            print(f"  {k}")
        print()
    else:
        print("PASS  No orphan keys. Every bib entry is referenced.")
        print()

    # --- Summary ---
    print("=" * 65)
    if has_errors:
        print("  RESULT: FAIL")
    else:
        print("  RESULT: PASS")
    print("=" * 65)

    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
