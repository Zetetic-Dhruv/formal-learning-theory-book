#!/usr/bin/env python3
"""
Evaluate reference task outputs against gold answers in flt_task_answers.json.

Usage:
    python3 scripts/run_reference_tasks.py | python3 scripts/evaluate_reference_tasks.py
    python3 scripts/evaluate_reference_tasks.py results.json
    python3 scripts/evaluate_reference_tasks.py < results.json
"""

import json
import os
import sys

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANSWERS_PATH = os.path.join(PROJ_DIR, "flt_task_answers.json")
TASKS_PATH = os.path.join(PROJ_DIR, "flt_tasks.json")

# Task type labels for display
TASK_TYPES = {
    "T01": "prerequisite_retrieval",
    "T02": "characterization_query",
    "T03": "non_implication_query",
    "T04": "generalization_bound_comparison",
    "T05": "cross_paradigm_reasoning",
    "T06": "hierarchy_extraction",
    "T07": "obstruction_analysis",
    "T08": "grammar_expansion_detection",
    "T09": "computational_barrier_query",
    "T10": "curriculum_ordering",
    "T11": "scope_boundary_query",
    "T12": "separation_witness_retrieval",
    "T13": "complexity_measure_comparison",
    "T14": "real_valued_extension",
    "T15": "multiclass_analysis",
}


def jaccard(predicted, expected):
    """Jaccard similarity: |A ∩ B| / |A ∪ B|."""
    p = set(predicted)
    e = set(expected)
    if not p and not e:
        return 1.0
    intersection = p & e
    union = p | e
    return len(intersection) / len(union)


def score_set_match(predicted_answer, gold):
    """Score a set_match task. predicted_answer should be a list of node IDs."""
    expected = gold["expected"]
    if isinstance(predicted_answer, dict):
        # Try to extract the list from the answer dict
        predicted_answer = predicted_answer.get("answer", predicted_answer)
    if isinstance(predicted_answer, list):
        return jaccard(predicted_answer, expected)
    return 0.0


def score_chain_match(predicted_answer, gold):
    """Score a chain_match task. Answer is an ordered sequence; score = 1 if order matches exactly."""
    expected = gold["expected"]
    if isinstance(predicted_answer, dict):
        predicted_answer = predicted_answer.get("answer", predicted_answer)
    if isinstance(predicted_answer, list) and predicted_answer == expected:
        return 1.0
    return 0.0


def score_exact_match(predicted_answer, gold):
    """Score an exact_match task. Score = 1 if match else 0."""
    expected = gold["expected"]
    if isinstance(predicted_answer, dict):
        predicted_answer = predicted_answer.get("answer", predicted_answer)
    if str(predicted_answer) == str(expected):
        return 1.0
    return 0.0


def score_boolean_match(predicted_answer, gold):
    """Score a boolean_match task."""
    expected = gold["expected"]
    if isinstance(predicted_answer, dict):
        predicted_answer = predicted_answer.get("answer", predicted_answer)
    if str(predicted_answer).lower() == str(expected).lower():
        return 1.0
    return 0.0


def score_count_match(predicted_answer, gold):
    """Score a count_match task."""
    expected = gold["expected"]
    if isinstance(predicted_answer, dict):
        predicted_answer = predicted_answer.get("answer", predicted_answer)
    if predicted_answer == expected:
        return 1.0
    return 0.0


def score_structured_explanation(predicted_answer, gold):
    """Score a structured_explanation task. Check required_elements are present."""
    required = gold["expected"]["required_elements"]
    if isinstance(predicted_answer, (dict, list)):
        # Use the full structure as the answer; don't unwrap nested "answer" keys
        # since the answer dict itself may contain an "answer" field as data
        answer = predicted_answer
    else:
        return 0.0

    matched = 0
    total = len(required)

    for key, expected_value in required.items():
        if key.endswith("_contains"):
            # Check that a field contains a substring
            base_key = key.replace("_contains", "")
            actual = answer.get(base_key, "")
            if isinstance(actual, str) and expected_value.lower() in actual.lower():
                matched += 1
        elif key == "bound_nodes":
            # Set match for nested list
            actual = answer.get("bound_nodes", [])
            if set(actual) == set(expected_value):
                matched += 1
        elif key == "edge_count":
            if isinstance(answer, list) and len(answer) == expected_value:
                matched += 1
        elif key.startswith("has_"):
            # Check that at least one edge of this relation exists
            relation_name = key[4:]  # strip "has_"
            if isinstance(answer, list):
                if any(e.get("relation") == relation_name for e in answer):
                    matched += 1
        elif key == "lower_bounds_pac":
            # Check that lower_bounds contains pac_learning
            lb = answer.get("lower_bounds", [])
            if "pac_learning" in lb:
                matched += 1
        elif key == "used_in_proof_vc":
            uip = answer.get("used_in_proof", [])
            if "vc_dimension" in uip:
                matched += 1
        elif key == "used_in_proof_sq":
            uip = answer.get("used_in_proof", [])
            if "sq_dimension" in uip:
                matched += 1
        elif key == "requires_assumption_crypto":
            ra = answer.get("requires_assumption", [])
            if ra and any(
                "DCRA" in r.get("note", "")
                or "cryptographic" in r.get("note", "").lower()
                for r in ra
            ):
                matched += 1
        elif key == "does_not_imply_from_vc":
            dni = answer.get("does_not_imply_to", [])
            if any(d.get("source") == "vc_dimension" for d in dni):
                matched += 1
        elif key == "pseudodimension_extends_vc":
            eg = answer.get("extends_grammar_to_vc", [])
            if any(e.get("source") == "pseudodimension" for e in eg):
                matched += 1
        elif key == "pseudodimension_restricts_fat_shattering":
            re_edges = answer.get("restricts_edges", [])
            if any(
                e.get("source") == "pseudodimension"
                and e.get("target") == "fat_shattering_dimension"
                for e in re_edges
            ):
                matched += 1
        elif key == "extends_grammar_count":
            eg = answer.get("extends_grammar_to_vc", [])
            if len(eg) == expected_value:
                matched += 1
        elif key == "fundamental_theorem_to_multiclass_empty":
            ft = answer.get("fundamental_theorem_to_multiclass", [])
            if len(ft) == 0:
                matched += 1
        elif key == "witness_contains":
            # Check witness field contains value
            witness = answer.get("witness", "")
            if isinstance(witness, str) and expected_value.lower() in witness.lower():
                matched += 1
        else:
            # Direct value match
            if isinstance(answer, dict):
                actual = answer.get(key)
                if actual == expected_value:
                    matched += 1
            # For list answers, skip direct key lookups

    return matched / total if total > 0 else 1.0


def score_relation_map_match(predicted_answer, gold):
    """Score a relation_map_match task."""
    expected = gold["expected"]
    if isinstance(predicted_answer, dict) and "answer" in predicted_answer:
        answer = predicted_answer["answer"]
    else:
        answer = predicted_answer

    if not isinstance(answer, dict) or not isinstance(expected, dict):
        return 0.0

    matched = 0
    total = len(expected)
    for key, val in expected.items():
        if key in answer and answer[key] == val:
            matched += 1
    return matched / total if total > 0 else 1.0


SCORERS = {
    "set_match": score_set_match,
    "chain_match": score_chain_match,
    "exact_match": score_exact_match,
    "boolean_match": score_boolean_match,
    "count_match": score_count_match,
    "structured_explanation": score_structured_explanation,
    "relation_map_match": score_relation_map_match,
}


def main():
    # Load gold answers
    with open(ANSWERS_PATH, "r", encoding="utf-8") as f:
        gold_data = json.load(f)
    gold_answers = gold_data["answers"]

    # Load predicted results from file argument or stdin
    if len(sys.argv) > 1 and sys.argv[1] != "-":
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            predicted = json.load(f)
    else:
        predicted = json.load(sys.stdin)

    task_ids = sorted(gold_answers.keys())
    passed = 0
    total = len(task_ids)
    results = []

    for tid in task_ids:
        gold = gold_answers[tid]
        scoring_type = gold["scoring"]
        task_type = TASK_TYPES.get(tid, "unknown")

        pred = predicted.get(tid, {})
        pred_answer = pred.get("answer", pred)

        scorer = SCORERS.get(scoring_type)
        if scorer is None:
            score = 0.0
            status = "FAIL"
            note = f"unknown scoring type: {scoring_type}"
        else:
            score = scorer(pred_answer, gold)

            # Determine pass/fail threshold
            if scoring_type in (
                "exact_match",
                "chain_match",
                "boolean_match",
                "count_match",
            ):
                threshold = 1.0
            else:
                threshold = 0.8

            if score >= threshold:
                status = "PASS"
                passed += 1
            else:
                status = "FAIL"
            note = ""

        results.append((tid, task_type, status, score, note))

    # Print report
    for tid, task_type, status, score, note in results:
        line = f"Task {tid} ({task_type}): {status} (score={score:.2f})"
        if note:
            line += f" [{note}]"
        print(line)

    print()
    print("=== SUMMARY ===")
    print(f"{passed}/{total} tasks passed")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
