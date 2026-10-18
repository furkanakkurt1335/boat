"""Inter-annotator agreement computation."""

import time
from collections import defaultdict

# Simple in-memory cache: treebank_id -> (score_dict, timestamp)
_agreement_cache: dict[int, tuple[dict, float]] = {}
_CACHE_TTL = 60.0  # seconds


def get_cached_agreement(treebank_id: int) -> dict | None:
    """Return cached agreement result if still valid, else None."""
    entry = _agreement_cache.get(treebank_id)
    if entry is None:
        return None
    result, ts = entry
    if time.monotonic() - ts > _CACHE_TTL:
        del _agreement_cache[treebank_id]
        return None
    return result


def set_cached_agreement(treebank_id: int, result: dict) -> None:
    """Store agreement result in cache."""
    _agreement_cache[treebank_id] = (result, time.monotonic())


def invalidate_agreement_cache(treebank_id: int) -> None:
    """Remove a treebank's cached agreement, e.g. after wordline updates."""
    _agreement_cache.pop(treebank_id, None)


def compute_annotation_agreement(
    annotation_wordlines: list[list[dict]],
) -> float:
    """Compute pairwise inter-annotator agreement for a single sentence.

    *annotation_wordlines* is a list of wordline lists — one list per annotator.
    Each wordline dict must have keys: id_f, form, lemma, upos, feats, head, deprel.

    Returns a score between 0 and 1, or -1 if multiword tokens are present.
    """
    # Group wordlines by id_f across annotators
    by_id: dict[str, list[dict]] = defaultdict(list)
    for wl_list in annotation_wordlines:
        for wl in wl_list:
            if "-" in wl["id_f"]:
                return -1  # multiword tokens not supported
            by_id[wl["id_f"]].append(wl)

    score_sum = 0
    pair_count = 0

    for wls in by_id.values():
        n = len(wls)
        if n <= 1:
            continue
        for i in range(n):
            for j in range(i + 1, n):
                score = 0
                if wls[i]["form"] == wls[j]["form"] and wls[i]["lemma"] == wls[j]["lemma"]:
                    if wls[i]["upos"] == wls[j]["upos"]:
                        score += 1
                    if wls[i]["feats"] == wls[j]["feats"]:
                        score += 1
                    if wls[i]["head"] == wls[j]["head"]:
                        score += 1
                    if wls[i]["deprel"] == wls[j]["deprel"]:
                        score += 1
                score_sum += score
                pair_count += 1

    if pair_count == 0:
        return 0.0
    return score_sum / (pair_count * 4)
