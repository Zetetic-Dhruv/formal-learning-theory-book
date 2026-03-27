#!/usr/bin/env python3
"""Validate the FLT concept graph against its embedded schema.

Checks performed:
  1.  JSON parses correctly
  2.  Node IDs are unique
  3.  Edge endpoints exist as node IDs
  4.  Relation values are in the schema enum
  5.  Required node fields present
  6.  Required edge fields present
  7.  Edge constraints satisfied (witness/citation per relation type)
  8.  No duplicate edges (source, relation, target)
  9.  All bib_keys and citation fields resolve against bibliography
  10. Node count matches meta declaration
  11. Edge count matches meta declaration
  12. Status values are in enum
  13. No generalizes_unclassified edges remain (release readiness)

Exit code 0: all checks pass.
Exit code 1: at least one check fails.
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


# BibTeX key pattern (same as bibliography validator)
BIBTEX_KEY_RE = re.compile(r"^[A-Za-z]+[0-9]{4}[a-z]?$")
BIB_ENTRY_RE = re.compile(r"@\w+\{([^,\s]+)", re.MULTILINE)


def parse_bib_keys(bib_path: Path) -> set:
    """Extract all entry keys from a BibTeX file."""
    text = bib_path.read_text(encoding="utf-8")
    return set(BIB_ENTRY_RE.findall(text))


def looks_like_bibtex_key(value: str) -> bool:
    """Return True if the string matches BibTeX key format."""
    return bool(BIBTEX_KEY_RE.match(value))


class Validator:
    """Accumulates check results and produces a summary report."""

    def __init__(self, graph: dict, bib_keys: set):
        self.graph = graph
        self.meta = graph.get("meta", {})
        self.schema = self.meta.get("json_schema", {})
        self.nodes = graph.get("nodes", [])
        self.edges = graph.get("edges", [])
        self.bib_keys = bib_keys

        # Collected node IDs for cross-referencing
        self.node_ids = set()

        # Results: list of (check_name, passed: bool, details: list[str])
        self.results = []

    def _record(self, name: str, passed: bool, details: list = None):
        self.results.append((name, passed, details or []))

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def check_unique_node_ids(self):
        """Check 2: Node IDs are unique."""
        seen = {}
        dupes = []
        for node in self.nodes:
            nid = node.get("id", "<missing>")
            if nid in seen:
                dupes.append(nid)
            seen[nid] = True
        self.node_ids = set(seen.keys())
        self._record(
            "Unique node IDs",
            len(dupes) == 0,
            [f"Duplicate ID: {d}" for d in dupes],
        )

    def check_edge_endpoints(self):
        """Check 3: All edge source/target reference existing node IDs."""
        errors = []
        for i, edge in enumerate(self.edges):
            src = edge.get("source", "<missing>")
            tgt = edge.get("target", "<missing>")
            if src not in self.node_ids:
                errors.append(f"Edge {i}: source '{src}' is not a node ID")
            if tgt not in self.node_ids:
                errors.append(f"Edge {i}: target '{tgt}' is not a node ID")
        self._record("Edge endpoints exist", len(errors) == 0, errors)

    def check_relation_enum(self):
        """Check 4: All edge relations are in the schema enum."""
        allowed = set(self.schema.get("relation_enum", []))
        errors = []
        for i, edge in enumerate(self.edges):
            rel = edge.get("relation", "<missing>")
            if rel not in allowed:
                src = edge.get("source", "?")
                tgt = edge.get("target", "?")
                errors.append(f"Edge {src}->{tgt}: relation '{rel}' not in enum")
        self._record("Relation values in enum", len(errors) == 0, errors)

    def check_required_node_fields(self):
        """Check 5: Every node has all required fields."""
        required = self.schema.get("node_required_fields", [])
        errors = []
        for node in self.nodes:
            nid = node.get("id", "<unknown>")
            for field in required:
                if field not in node:
                    errors.append(f"Node '{nid}': missing required field '{field}'")
        self._record("Required node fields", len(errors) == 0, errors)

    def check_required_edge_fields(self):
        """Check 6: Every edge has all required fields."""
        required = self.schema.get("edge_required_fields", [])
        errors = []
        for i, edge in enumerate(self.edges):
            src = edge.get("source", "?")
            tgt = edge.get("target", "?")
            for field in required:
                if field not in edge:
                    errors.append(
                        f"Edge {i} ({src}->{tgt}): missing required field '{field}'"
                    )
        self._record("Required edge fields", len(errors) == 0, errors)

    def check_edge_constraints(self):
        """Check 7: Relation-specific required fields (witness, citation)."""
        constraints = self.schema.get("edge_constraints", {})
        errors = []
        for i, edge in enumerate(self.edges):
            rel = edge.get("relation", "")
            if rel in constraints:
                req = constraints[rel].get("required_fields", [])
                src = edge.get("source", "?")
                tgt = edge.get("target", "?")
                for field in req:
                    if field not in edge or not edge[field]:
                        errors.append(
                            f"Edge {src}-[{rel}]->{tgt}: "
                            f"constraint requires '{field}' but it is missing or empty"
                        )
        self._record("Edge constraints", len(errors) == 0, errors)

    def check_duplicate_edges(self):
        """Check 8: No duplicate (source, relation, target) triples."""
        seen = {}
        dupes = []
        for edge in self.edges:
            triple = (edge.get("source"), edge.get("relation"), edge.get("target"))
            if triple in seen:
                dupes.append(f"{triple[0]}-[{triple[1]}]->{triple[2]}")
            seen[triple] = True
        self._record(
            "No duplicate edges", len(dupes) == 0, [f"Duplicate: {d}" for d in dupes]
        )

    def check_bib_resolution(self):
        """Check 9: All bib_keys and citation fields resolve against the bib."""
        errors = []

        # Node bib_keys
        for node in self.nodes:
            nid = node.get("id", "?")
            for k in node.get("bib_keys", []):
                if isinstance(k, str) and looks_like_bibtex_key(k):
                    if k not in self.bib_keys:
                        errors.append(
                            f"Node '{nid}' bib_keys: '{k}' not in bibliography"
                        )

            # Provenance introduced_by / proved_by
            prov = node.get("provenance", {})
            if isinstance(prov, dict):
                for field in ("introduced_by", "proved_by"):
                    val = prov.get(field)
                    if isinstance(val, str) and looks_like_bibtex_key(val):
                        if val not in self.bib_keys:
                            errors.append(
                                f"Node '{nid}' provenance.{field}: '{val}' not in bibliography"
                            )
                    elif isinstance(val, list):
                        for v in val:
                            if isinstance(v, str) and looks_like_bibtex_key(v):
                                if v not in self.bib_keys:
                                    errors.append(
                                        f"Node '{nid}' provenance.{field}: '{v}' not in bibliography"
                                    )

        # Edge citations
        for edge in self.edges:
            src = edge.get("source", "?")
            tgt = edge.get("target", "?")
            rel = edge.get("relation", "?")
            label = f"Edge {src}-[{rel}]->{tgt}"

            val = edge.get("citation")
            if isinstance(val, str) and looks_like_bibtex_key(val):
                if val not in self.bib_keys:
                    errors.append(f"{label} citation: '{val}' not in bibliography")
            elif isinstance(val, list):
                for v in val:
                    if isinstance(v, str) and looks_like_bibtex_key(v):
                        if v not in self.bib_keys:
                            errors.append(
                                f"{label} citation: '{v}' not in bibliography"
                            )

        self._record("Bib keys resolve", len(errors) == 0, errors)

    def check_node_count(self):
        """Check 10: Actual node count matches meta declaration."""
        declared = self.meta.get("node_count", None)
        actual = len(self.nodes)
        ok = declared is not None and actual == declared
        details = []
        if not ok:
            details.append(f"Declared: {declared}, actual: {actual}")
        self._record("Node count matches meta", ok, details)

    def check_edge_count(self):
        """Check 11: Actual edge count matches meta declaration."""
        declared = self.meta.get("edge_count", None)
        actual = len(self.edges)
        ok = declared is not None and actual == declared
        details = []
        if not ok:
            details.append(f"Declared: {declared}, actual: {actual}")
        self._record("Edge count matches meta", ok, details)

    def check_status_enum(self):
        """Check 12: All node status values are in the schema enum."""
        allowed = set(self.schema.get("status_enum", []))
        errors = []
        for node in self.nodes:
            nid = node.get("id", "?")
            status = node.get("status", "<missing>")
            if status not in allowed:
                errors.append(
                    f"Node '{nid}': status '{status}' not in enum {sorted(allowed)}"
                )
        self._record("Status values in enum", len(errors) == 0, errors)

    def check_no_generalizes_unclassified(self):
        """Check 13: No generalizes_unclassified edges remain (release check)."""
        found = []
        for edge in self.edges:
            if edge.get("relation") == "generalizes_unclassified":
                src = edge.get("source", "?")
                tgt = edge.get("target", "?")
                found.append(f"{src}-[generalizes_unclassified]->{tgt}")
        self._record(
            "No generalizes_unclassified edges",
            len(found) == 0,
            [f"Remaining: {e}" for e in found],
        )

    # ------------------------------------------------------------------
    # Run all and report
    # ------------------------------------------------------------------

    def run_all(self):
        """Execute every check in order."""
        self.check_unique_node_ids()  # 2
        self.check_edge_endpoints()  # 3
        self.check_relation_enum()  # 4
        self.check_required_node_fields()  # 5
        self.check_required_edge_fields()  # 6
        self.check_edge_constraints()  # 7
        self.check_duplicate_edges()  # 8
        self.check_bib_resolution()  # 9
        self.check_node_count()  # 10
        self.check_edge_count()  # 11
        self.check_status_enum()  # 12
        self.check_no_generalizes_unclassified()  # 13

    def report(self) -> bool:
        """Print human-readable report. Returns True if all checks pass."""
        all_pass = True
        print("=" * 65)
        print("  FLT Concept Graph Validation")
        print("=" * 65)
        print()

        for name, passed, details in self.results:
            status = "PASS" if passed else "FAIL"
            print(f"  [{status}]  {name}")
            if not passed:
                all_pass = False
                for d in details[:20]:  # cap detail lines
                    print(f"           {d}")
                if len(details) > 20:
                    print(f"           ... and {len(details) - 20} more")
            print()

        print("=" * 65)
        total = len(self.results)
        passed_count = sum(1 for _, p, _ in self.results if p)
        failed_count = total - passed_count
        print(f"  {passed_count}/{total} checks passed, {failed_count} failed.")
        if all_pass:
            print("  RESULT: PASS")
        else:
            print("  RESULT: FAIL")
        print("=" * 65)
        return all_pass


def main():
    parser = argparse.ArgumentParser(
        description="Validate the FLT concept graph against its embedded schema."
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

    # --- Check 1: JSON parses ---
    if not args.graph.exists():
        print(f"ERROR: Graph file not found: {args.graph}", file=sys.stderr)
        sys.exit(1)

    try:
        graph = load_json_tolerant(args.graph)
        print()
        print("  [PASS]  JSON parses correctly")
        print()
    except json.JSONDecodeError as exc:
        print()
        print(f"  [FAIL]  JSON parse error: {exc}")
        print()
        sys.exit(1)

    # --- Load bibliography ---
    if not args.bib.exists():
        print(f"ERROR: Bib file not found: {args.bib}", file=sys.stderr)
        sys.exit(1)

    bib_keys = parse_bib_keys(args.bib)

    # --- Run all checks ---
    v = Validator(graph, bib_keys)
    v.run_all()
    all_pass = v.report()

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
