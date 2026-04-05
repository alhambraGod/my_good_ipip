"""Local deterministic personalization logic for selecting 40 questions from 100-item bank."""

from __future__ import annotations

import random
from collections import defaultdict

from questions.question_bank import DIMENSIONS


def _scene_score(question: dict, user_scenes: set[str]) -> int:
    scenes = set(question.get("scenes") or [])
    if "all" in scenes:
        return 1
    return len(scenes.intersection(user_scenes))


def _pick_unique_facets(candidates: list[dict], rng: random.Random, target: int) -> list[dict]:
    if target <= 0:
        return []
    groups: dict[str, list[dict]] = defaultdict(list)
    for q in candidates:
        groups[q.get("facet") or q["id"]].append(q)

    chosen: list[dict] = []
    facet_keys = list(groups.keys())
    rng.shuffle(facet_keys)

    for facet in facet_keys:
        if len(chosen) >= target:
            break
        pool = groups[facet]
        rng.shuffle(pool)
        chosen.append(pool[0])

    if len(chosen) < target:
        leftovers = [q for q in candidates if q not in chosen]
        rng.shuffle(leftovers)
        chosen.extend(leftovers[: target - len(chosen)])

    return chosen[:target]


def _sort_candidates(candidates: list[dict], user_scenes: set[str], rng: random.Random) -> list[dict]:
    shuffled = list(candidates)
    rng.shuffle(shuffled)
    return sorted(shuffled, key=lambda q: (_scene_score(q, user_scenes), q.get("difficulty") == "easy"), reverse=True)


def select_personalized_questions(
    profile_vector: dict,
    pool: list[dict],
    seed: str,
    previous_question_ids: set[str] | None = None,
) -> list[dict]:
    """Select 40 questions with constraints: per dimension 8 = 4 core + 2 scene + 2 reverse."""
    rng = random.Random(seed)
    previous_question_ids = previous_question_ids or set()
    user_scenes = set(profile_vector.get("scenes", []))

    selected: list[dict] = []

    for dim in DIMENSIONS:
        dim_items = [q for q in pool if q["dimension"] == dim]

        core = [q for q in dim_items if q.get("role") == "core" and not q.get("reverse")]
        scene = [q for q in dim_items if q.get("role") == "scene" and not q.get("reverse")]
        reverse = [q for q in dim_items if q.get("reverse")]

        # Penalty for repeated questions (if provided)
        core = [q for q in core if q["id"] not in previous_question_ids] or core
        scene = [q for q in scene if q["id"] not in previous_question_ids] or scene
        reverse = [q for q in reverse if q["id"] not in previous_question_ids] or reverse

        ranked_core = _sort_candidates(core, user_scenes, rng)
        ranked_scene = _sort_candidates(scene, user_scenes, rng)
        ranked_reverse = _sort_candidates(reverse, user_scenes, rng)

        dim_selected: list[dict] = []
        dim_selected.extend(_pick_unique_facets(ranked_core, rng, 4))
        dim_selected.extend(_pick_unique_facets(ranked_scene, rng, 2))
        dim_selected.extend(_pick_unique_facets(ranked_reverse, rng, 2))

        # Fallback relaxation to guarantee 8 questions per dimension
        if len(dim_selected) < 8:
            rest = [q for q in dim_items if q not in dim_selected]
            rest = _sort_candidates(rest, user_scenes, rng)
            dim_selected.extend(rest[: 8 - len(dim_selected)])

        # Final guard
        if len(dim_selected) < 8:
            raise ValueError(f"Insufficient questions for dimension {dim}")

        rng.shuffle(dim_selected)
        selected.extend(dim_selected[:8])

    rng.shuffle(selected)
    return selected
