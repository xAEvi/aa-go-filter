"""Persist last sync snapshot and diff it against the current run."""

import json
from datetime import datetime, timezone


def load_state(path):
    # Return empty snapshot when no previous run exists.
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"go_models": [], "aa_slugs": [], "updated": None}


def save_state(path, go_names, slugs, slugs_highest=None):
    # Overwrite the snapshot with the current run.
    payload = {
        "go_models": list(go_names),
        "aa_slugs": list(slugs),
        "updated": datetime.now(timezone.utc).isoformat(),
    }
    if slugs_highest is not None:
        payload["aa_slugs_highest"] = list(slugs_highest)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def diff_runs(old, go_names, slugs, slugs_highest=None):
    # Set-diff old snapshot vs current run, sorted for stable output.
    old_go, old_slugs = set(old.get("go_models", [])), set(old.get("aa_slugs", []))
    new_go, new_slugs = set(go_names), set(slugs)
    diff = {
        "added_go": sorted(new_go - old_go),
        "removed_go": sorted(old_go - new_go),
        "added_slugs": sorted(new_slugs - old_slugs),
        "removed_slugs": sorted(old_slugs - new_slugs),
    }
    if slugs_highest is not None:
        old_highest, new_highest = set(old.get("aa_slugs_highest", [])), set(slugs_highest)
        diff["added_highest"] = sorted(new_highest - old_highest)
        diff["removed_highest"] = sorted(old_highest - new_highest)
    return diff
