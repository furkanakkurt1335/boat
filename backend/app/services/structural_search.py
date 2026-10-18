"""Structural search engine for UD treebank data.

Delegates to the udsearch library for pattern matching and rewriting.
Provides adapters between BoAT's JSON query format and udsearch's
structural pattern language.
"""

from __future__ import annotations

from typing import Any

from udsearch._compat import apply_operations_to_dicts, match_structural_dicts
from udsearch.structural import (
    NodePattern,
    RelationPattern,
    StructuralPattern,
    parse_structural,
)


def _query_dict_to_structural(query: dict[str, Any]) -> StructuralPattern:
    """Convert a BoAT JSON structural query to a udsearch StructuralPattern.

    This preserves backward compatibility with the existing StructuralQuery
    schema: target, head_constraint, dependent_constraints, negated_dependents.
    """
    pattern = StructuralPattern()

    # Build target node constraints in udsearch format
    target_constraints = _node_constraint_to_pattern(query.get("target", {}))
    pattern.nodes["target"] = NodePattern(name="target", constraints=target_constraints)
    pattern.anchor = "target"

    # Head constraint: target -deprel-> head
    head_c = query.get("head_constraint")
    if head_c:
        head_constraints = _node_constraint_to_pattern(head_c)
        pattern.nodes["head"] = NodePattern(name="head", constraints=head_constraints)

        deprel = None
        deprel_list = head_c.get("deprel")
        if deprel_list:
            deprel = "|".join(deprel_list)

        # In BoAT's model, head_constraint.deprel constrains the TARGET's deprel
        # (the arc label from head to target). So target is the child, head is the head.
        pattern.relations.append(RelationPattern(child="target", head="head", deprel=deprel))

    # Dependent constraints: dep -deprel-> target
    dep_constraints = query.get("dependent_constraints") or []
    for i, dep_c in enumerate(dep_constraints):
        dep_name = f"dep{i}"
        dep_pattern = _node_constraint_to_pattern(dep_c)
        pattern.nodes[dep_name] = NodePattern(name=dep_name, constraints=dep_pattern)

        deprel = None
        deprel_list = dep_c.get("deprel")
        if deprel_list:
            deprel = "|".join(deprel_list)

        pattern.relations.append(RelationPattern(child=dep_name, head="target", deprel=deprel))

    # Negated dependents: !neg -deprel-> target
    neg_constraints = query.get("negated_dependents") or []
    for i, neg_c in enumerate(neg_constraints):
        neg_name = f"neg{i}"
        neg_pattern = _node_constraint_to_pattern(neg_c)
        pattern.nodes[neg_name] = NodePattern(name=neg_name, constraints=neg_pattern, negated=True)

        deprel = None
        deprel_list = neg_c.get("deprel")
        if deprel_list:
            deprel = "|".join(deprel_list)

        pattern.relations.append(RelationPattern(child=neg_name, head="target", deprel=deprel))

    return pattern


def _node_constraint_to_pattern(constraint: dict[str, Any]) -> dict[str, str]:
    """Convert a BoAT NodeConstraint dict to udsearch pattern constraints."""
    result: dict[str, str] = {}

    upos_list = constraint.get("upos")
    if upos_list:
        result["UPOS"] = "|".join(upos_list)

    form = constraint.get("form")
    if form is not None:
        # BoAT does case-insensitive match; udsearch uses regex for that
        result["form"] = f"/{form}/i" if form else form

    lemma = constraint.get("lemma")
    if lemma is not None:
        result["lemma"] = f"/{lemma}/i" if lemma else lemma

    feats = constraint.get("feats")
    if feats:
        for feat_key, allowed_values in feats.items():
            if allowed_values:
                result[feat_key] = "|".join(allowed_values)
            else:
                result[feat_key] = "__EXISTS__"

    return result


def match_structural(
    query: dict[str, Any],
    wordlines: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Find tokens matching a structural query within a single sentence.

    This is the backward-compatible entry point matching the old API.
    Accepts either:
    - A BoAT JSON query dict (with target, head_constraint, etc.)
    - A pattern string in udsearch syntax (via "pattern_string" key)

    Args:
        query: A structural query dict or {"pattern_string": "v: [UPOS=VERB]\\n..."}.
        wordlines: List of wordline dicts (one sentence).

    Returns:
        List of wordline dicts for target tokens that match all constraints.
    """
    # Check if the query uses the new pattern string format
    pattern_string = query.get("pattern_string")
    if pattern_string:
        structural_pattern = parse_structural(pattern_string)
    else:
        structural_pattern = _query_dict_to_structural(query)

    bindings = match_structural_dicts(structural_pattern, wordlines)

    # Return target/anchor token dicts (backward compatible: flat list of matched tokens)
    anchor = structural_pattern.anchor
    seen_ids = set()
    result = []
    for binding in bindings:
        token_dict = binding.get(anchor)
        if token_dict and token_dict["id_f"] not in seen_ids:
            seen_ids.add(token_dict["id_f"])
            result.append(token_dict)
    return result


def match_structural_full(
    query: dict[str, Any] | str,
    wordlines: list[dict[str, Any]],
) -> list[dict[str, dict[str, str]]]:
    """Full structural matching returning all node bindings.

    Unlike match_structural() which returns only target tokens for backward
    compatibility, this returns the complete binding dicts.

    Args:
        query: A pattern string or a query dict with "pattern_string" key.
        wordlines: List of wordline dicts.

    Returns:
        List of binding dicts {node_name: wordline_dict}.
    """
    if isinstance(query, str):
        pattern = parse_structural(query)
    else:
        pattern_string = query.get("pattern_string")
        if pattern_string:
            pattern = parse_structural(pattern_string)
        else:
            pattern = _query_dict_to_structural(query)

    return match_structural_dicts(pattern, wordlines)


def rewrite_wordlines(
    wordlines: list[dict[str, str]],
    pattern: str,
    operations: list[str],
    sent_id: str = "?",
    text: str = "",
) -> tuple[list[dict[str, str]], list[dict]]:
    """Apply batch rewrite operations to matching tokens.

    Args:
        wordlines: List of wordline dicts for a single sentence.
        pattern: Pattern string (single-node or structural).
        operations: List of operation strings (e.g., ["UPOS=ADJ", "s.Case=Nom"]).
        sent_id: Sentence ID.
        text: Sentence text.

    Returns:
        Tuple of (modified_wordlines, changes).
    """
    return apply_operations_to_dicts(
        wordlines,
        pattern=pattern,
        operations=operations,
        sent_id=sent_id,
        text=text,
    )
