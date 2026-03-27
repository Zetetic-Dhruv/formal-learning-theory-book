#!/usr/bin/env python3
"""
Compute answers for all 15 FLT reference tasks by traversing flt_concept_graph.json.
Outputs JSON to stdout.
"""

import json
import re
import sys
import os
from collections import deque

GRAPH_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "flt_concept_graph.json",
)


def load_graph(path):
    """Load the concept graph, fixing trailing commas in JSON."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r",\s*}", "}", content)
    content = re.sub(r",\s*]", "]", content)
    return json.loads(content)


def build_graph(data):
    """Build adjacency structures from nodes and edges."""
    nodes = {n["id"]: n for n in data["nodes"]}
    edges = data["edges"]

    # Forward adjacency: source -> [(target, edge_dict), ...]
    fwd = {}
    # Reverse adjacency: target -> [(source, edge_dict), ...]
    rev = {}
    for e in edges:
        fwd.setdefault(e["source"], []).append((e["target"], e))
        rev.setdefault(e["target"], []).append((e["source"], e))

    return nodes, edges, fwd, rev


def bfs_reachable(start, fwd, relation):
    """BFS from start node following edges of given relation type. Returns reachable set excluding start."""
    visited = set()
    queue = deque([start])
    while queue:
        n = queue.popleft()
        if n in visited:
            continue
        visited.add(n)
        for target, e in fwd.get(n, []):
            if e["relation"] == relation and target not in visited:
                queue.append(target)
    visited.discard(start)
    return visited


def task_T01(nodes, edges, fwd, rev):
    """Prerequisite retrieval: all nodes reachable via defined_using from vc_dimension."""
    reachable = bfs_reachable("vc_dimension", fwd, "defined_using")
    return sorted(reachable)


def task_T02(nodes, edges, fwd, rev):
    """Characterization query: all nodes X where X characterizes pac_learning, plus fundamental_theorem."""
    result = set()
    for source, e in rev.get("pac_learning", []):
        if e["relation"] == "characterizes":
            result.add(source)
    # The task says "plus the fundamental_theorem node"
    if "fundamental_theorem" in nodes:
        result.add("fundamental_theorem")
    return sorted(result)


def task_T03(nodes, edges, fwd, rev):
    """Non-implication query: check for does_not_imply edge from pac_learning to mistake_bounded."""
    for target, e in fwd.get("pac_learning", []):
        if target == "mistake_bounded" and e["relation"] == "does_not_imply":
            return {"answer": "NO", "witness": e.get("witness", ""), "edge_found": True}
    return {"answer": "YES", "edge_found": False}


def task_T04(nodes, edges, fwd, rev):
    """Generalization bound comparison: find all nodes X with upper_bounds -> generalization_error,
    then their defined_using dependencies."""
    bound_nodes = set()
    for source, e in rev.get("generalization_error", []):
        if e["relation"] == "upper_bounds":
            bound_nodes.add(source)

    # For each bound node, find its defined_using dependencies
    deps = {}
    for bn in bound_nodes:
        bn_deps = bfs_reachable(bn, fwd, "defined_using")
        deps[bn] = sorted(bn_deps)

    return {"bound_nodes": sorted(bound_nodes), "dependencies": deps}


def task_T05(nodes, edges, fwd, rev):
    """Cross-paradigm reasoning: traverse specified edge paths and collect facts."""
    facts = {}

    # bayesian_learner -[instance_of]-> learner
    for target, e in fwd.get("bayesian_learner", []):
        if target == "learner" and e["relation"] == "instance_of":
            facts["bayesian_learner_instance_of_learner"] = True

    # pac_bayes_bound -[upper_bounds]-> generalization_error
    for target, e in fwd.get("pac_bayes_bound", []):
        if target == "generalization_error" and e["relation"] == "upper_bounds":
            facts["pac_bayes_upper_bounds_gen_error"] = True

    # natarajan_dimension -[does_not_imply]-> pac_learning
    for target, e in fwd.get("natarajan_dimension", []):
        if target == "pac_learning" and e["relation"] == "does_not_imply":
            facts["natarajan_does_not_imply_pac"] = True
            facts["natarajan_witness"] = e.get("witness", "")

    # ds_dimension -[characterizes]-> pac_learning
    for target, e in fwd.get("ds_dimension", []):
        if target == "pac_learning" and e["relation"] == "characterizes":
            facts["ds_characterizes_pac"] = True

    return facts


def task_T06(nodes, edges, fwd, rev):
    """Hierarchy extraction: traverse strictly_stronger edges among Ex, BC, FIN nodes."""
    gold_ids = {"ex_learning", "bc_learning", "finite_learning"}
    chain_edges = []

    for e in edges:
        if (
            e["relation"] == "strictly_stronger"
            and e["source"] in gold_ids
            and e["target"] in gold_ids
        ):
            chain_edges.append((e["source"], e["target"]))

    # Also check restricts edges that establish hierarchy
    for e in edges:
        if (
            e["relation"] == "restricts"
            and e["source"] in gold_ids
            and e["target"] in gold_ids
        ):
            chain_edges.append((e["source"], e["target"]))

    # Build the chain: the strictly_stronger is ex_learning -> finite_learning
    # bc_learning restricts ex_learning (BC is more general)
    # We need to construct the hierarchy: BC > Ex > FIN
    # strictly_stronger: X strictly_stronger Y means X > Y (X includes more)
    # restricts: X restricts Y means X generalizes Y (X > Y in power)

    # Build adjacency for hierarchy
    stronger = {}  # node -> set of nodes it's strictly stronger than
    for src, tgt in chain_edges:
        stronger.setdefault(src, set()).add(tgt)

    # Topological sort to get chain
    # BC restricts Ex (BC > Ex), Ex strictly_stronger FIN (Ex > FIN)
    all_nodes = set()
    for s, t in chain_edges:
        all_nodes.add(s)
        all_nodes.add(t)

    # Build chain by finding ordering
    chain = []
    remaining = set(all_nodes)
    in_degree = {n: 0 for n in all_nodes}
    for s, t in chain_edges:
        in_degree[t] = in_degree.get(t, 0) + 1

    queue = deque([n for n in all_nodes if in_degree.get(n, 0) == 0])
    while queue:
        n = queue.popleft()
        chain.append(n)
        remaining.discard(n)
        for t in stronger.get(n, set()):
            in_degree[t] -= 1
            if in_degree[t] == 0:
                queue.append(t)

    return chain


def task_T07(nodes, edges, fwd, rev):
    """Obstruction analysis: read obstruction field on analogy edge concept_drift -> online_learning."""
    for target, e in fwd.get("concept_drift", []):
        if target == "online_learning" and e["relation"] == "analogy":
            return {
                "obstruction": e.get("obstruction", ""),
                "obstruction_type": e.get("obstruction_type", ""),
            }
    return {"obstruction": "", "obstruction_type": ""}


def task_T08(nodes, edges, fwd, rev):
    """Grammar expansion detection: find all nodes X with extends_grammar -> vc_dimension."""
    result = set()
    for source, e in rev.get("vc_dimension", []):
        if e["relation"] == "extends_grammar":
            result.add(source)
    return sorted(result)


def task_T09(nodes, edges, fwd, rev):
    """Computational barrier query: find computational_hardness node, traverse its edges."""
    result = {
        "requires_assumption": [],
        "used_in_proof": [],
        "lower_bounds": [],
        "does_not_imply_from": [],
        "does_not_imply_to": [],
    }

    for target, e in fwd.get("computational_hardness", []):
        if e["relation"] == "requires_assumption":
            result["requires_assumption"].append(
                {
                    "target": target,
                    "note": e.get("note", ""),
                    "citation": e.get("citation", ""),
                }
            )
        elif e["relation"] == "used_in_proof":
            result["used_in_proof"].append(target)
        elif e["relation"] == "lower_bounds":
            result["lower_bounds"].append(target)

    # Also check does_not_imply edges involving computational_hardness
    for source, e in rev.get("computational_hardness", []):
        if e["relation"] == "does_not_imply":
            result["does_not_imply_to"].append(
                {"source": source, "witness": e.get("witness", "")}
            )

    return result


def task_T10(nodes, edges, fwd, rev):
    """Curriculum ordering: topological sort of defined_using subgraph for PAC-related nodes."""
    pac_nodes = {
        "domain",
        "label",
        "concept",
        "concept_class",
        "hypothesis_space",
        "shatters",
        "vc_dimension",
        "iid_sample",
        "generalization_error",
        "sample_complexity",
        "pac_learning",
        "vc_characterization",
        "fundamental_theorem",
    }

    # Build defined_using subgraph restricted to PAC nodes
    # Edge: source defined_using target means source depends on target
    # For curriculum: target should come before source
    adj = {}  # node -> nodes it depends on (defined_using targets)
    for e in edges:
        if (
            e["relation"] == "defined_using"
            and e["source"] in pac_nodes
            and e["target"] in pac_nodes
        ):
            adj.setdefault(e["source"], set()).add(e["target"])

    # Also include characterizes and restricts edges that create ordering for theorems
    # vc_characterization characterizes vc_dimension and pac_learning -> needs both first
    # fundamental_theorem restricts vc_characterization -> needs vc_characterization first
    for e in edges:
        if e["source"] in pac_nodes and e["target"] in pac_nodes:
            if e["relation"] in ("characterizes", "used_in_proof", "restricts"):
                # These theorem nodes need their referenced concepts defined first
                adj.setdefault(e["source"], set()).add(e["target"])

    # Kahn's algorithm for topological sort
    in_degree = {n: 0 for n in pac_nodes}
    for src, deps in adj.items():
        for d in deps:
            if d in pac_nodes:
                pass  # we count reverse
    # Recompute: for ordering, if src depends on tgt, then tgt comes first
    # Build reverse: tgt -> [src] means src depends on tgt
    dependents = {}  # tgt -> set of nodes that depend on tgt
    in_degree = {n: 0 for n in pac_nodes}
    for src in pac_nodes:
        for dep in adj.get(src, set()):
            if dep in pac_nodes:
                dependents.setdefault(dep, set()).add(src)
                in_degree[src] = in_degree.get(src, 0) + 1

    queue = deque(sorted([n for n in pac_nodes if in_degree.get(n, 0) == 0]))
    order = []
    while queue:
        n = queue.popleft()
        order.append(n)
        for dependent in sorted(dependents.get(n, set())):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    return order


def task_T11(nodes, edges, fwd, rev):
    """Scope boundary query: check for scope_boundary node with id containing 'rl'."""
    result = {}
    for nid, node in nodes.items():
        if node.get("category") == "scope_boundary" and "rl" in nid:
            result["found"] = True
            result["node_id"] = nid
            result["description"] = node.get("description", "")
            result["scope_note"] = node.get("scope_note", "")
            return result
    return {"found": False}


def task_T12(nodes, edges, fwd, rev):
    """Separation witness retrieval: collect all does_not_imply and strictly_stronger edges with witnesses."""
    separations = []

    for e in edges:
        if e["relation"] in ("does_not_imply", "strictly_stronger"):
            separations.append(
                {
                    "source": e["source"],
                    "target": e["target"],
                    "relation": e["relation"],
                    "witness": e.get("witness", ""),
                }
            )

    return {
        "separations": separations,
        "does_not_imply_count": sum(
            1 for s in separations if s["relation"] == "does_not_imply"
        ),
        "strictly_stronger_count": sum(
            1 for s in separations if s["relation"] == "strictly_stronger"
        ),
        "total_count": len(separations),
    }


def task_T13(nodes, edges, fwd, rev):
    """Complexity measure comparison: find all edges among vc_dimension, littlestone_dimension,
    sq_dimension, and star_number."""
    dims = {"vc_dimension", "littlestone_dimension", "sq_dimension", "star_number"}
    result = []

    for e in edges:
        if e["source"] in dims and e["target"] in dims:
            entry = {
                "source": e["source"],
                "target": e["target"],
                "relation": e["relation"],
            }
            if "note" in e:
                entry["note"] = e["note"]
            if "obstruction" in e:
                entry["obstruction"] = e["obstruction"]
            if "witness" in e:
                entry["witness"] = e["witness"]
            result.append(entry)

    return result


def task_T14(nodes, edges, fwd, rev):
    """Real-valued extension: traverse extends_grammar and restricts edges from vc_dimension
    to pseudodimension and fat_shattering_dimension."""
    result = {
        "extends_grammar_to_vc": [],
        "restricts_edges": [],
        "characterizes_edges": [],
    }

    # extends_grammar -> vc_dimension (what extends VC?)
    for source, e in rev.get("vc_dimension", []):
        if e["relation"] == "extends_grammar":
            entry = {"source": source, "note": e.get("note", "")}
            result["extends_grammar_to_vc"].append(entry)

    # pseudodimension restricts fat_shattering_dimension
    for target, e in fwd.get("pseudodimension", []):
        if e["relation"] == "restricts":
            entry = {
                "source": "pseudodimension",
                "target": target,
                "note": e.get("note", ""),
            }
            result["restricts_edges"].append(entry)

    # fat_shattering characterizes anything?
    for target, e in fwd.get("fat_shattering_dimension", []):
        if e["relation"] == "characterizes":
            entry = {
                "source": "fat_shattering_dimension",
                "target": target,
                "note": e.get("note", ""),
            }
            result["characterizes_edges"].append(entry)

    return result


def task_T15(nodes, edges, fwd, rev):
    """Multiclass analysis: check fundamental_theorem edges to multiclass nodes,
    check natarajan_dimension and ds_dimension characterization status."""
    result = {
        "fundamental_theorem_to_multiclass": [],
        "natarajan_characterizes_pac": False,
        "natarajan_does_not_imply_pac": False,
        "natarajan_does_not_imply_witness": "",
        "ds_characterizes_pac": False,
        "natarajan_extends_vc": False,
        "ds_stronger_natarajan": False,
    }

    multiclass_nodes = {"natarajan_dimension", "ds_dimension"}

    # Check fundamental_theorem edges to multiclass nodes
    for target, e in fwd.get("fundamental_theorem", []):
        if target in multiclass_nodes:
            result["fundamental_theorem_to_multiclass"].append(
                {"target": target, "relation": e["relation"]}
            )

    # Check natarajan_dimension characterizes pac_learning
    for target, e in fwd.get("natarajan_dimension", []):
        if target == "pac_learning":
            if e["relation"] == "characterizes":
                result["natarajan_characterizes_pac"] = True
            elif e["relation"] == "does_not_imply":
                result["natarajan_does_not_imply_pac"] = True
                result["natarajan_does_not_imply_witness"] = e.get("witness", "")

    # Check ds_dimension characterizes pac_learning
    for target, e in fwd.get("ds_dimension", []):
        if target == "pac_learning" and e["relation"] == "characterizes":
            result["ds_characterizes_pac"] = True

    # Check natarajan extends_grammar vc_dimension
    for target, e in fwd.get("natarajan_dimension", []):
        if target == "vc_dimension" and e["relation"] == "extends_grammar":
            result["natarajan_extends_vc"] = True

    # Check ds_dimension strictly_stronger natarajan_dimension
    for target, e in fwd.get("ds_dimension", []):
        if target == "natarajan_dimension" and e["relation"] == "strictly_stronger":
            result["ds_stronger_natarajan"] = True

    return result


def main():
    graph_data = load_graph(GRAPH_PATH)
    nodes, edges, fwd, rev = build_graph(graph_data)

    results = {}

    results["T01"] = {"answer": task_T01(nodes, edges, fwd, rev)}
    results["T02"] = {"answer": task_T02(nodes, edges, fwd, rev)}
    results["T03"] = {"answer": task_T03(nodes, edges, fwd, rev)}
    results["T04"] = {"answer": task_T04(nodes, edges, fwd, rev)}
    results["T05"] = {"answer": task_T05(nodes, edges, fwd, rev)}
    results["T06"] = {"answer": task_T06(nodes, edges, fwd, rev)}
    results["T07"] = {"answer": task_T07(nodes, edges, fwd, rev)}
    results["T08"] = {"answer": task_T08(nodes, edges, fwd, rev)}
    results["T09"] = {"answer": task_T09(nodes, edges, fwd, rev)}
    results["T10"] = {"answer": task_T10(nodes, edges, fwd, rev)}
    results["T11"] = {"answer": task_T11(nodes, edges, fwd, rev)}
    results["T12"] = {"answer": task_T12(nodes, edges, fwd, rev)}
    results["T13"] = {"answer": task_T13(nodes, edges, fwd, rev)}
    results["T14"] = {"answer": task_T14(nodes, edges, fwd, rev)}
    results["T15"] = {"answer": task_T15(nodes, edges, fwd, rev)}

    json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
