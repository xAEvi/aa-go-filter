"""Match Go display names to Artificial Analysis slugs."""

import re
import unicodedata

# Suffixes stripped from Go names before matching (not model identity).
GO_STRIP_SUFFIXES = ("contributor", "preview", "exp")

# Tokens allowed after the base slug (effort levels, revisions, variants).
ALLOWED_SUFFIX_TOKENS = {
    "max", "xhigh", "high", "medium", "low",
    "reasoning", "non", "preview", "next",
    "0424", "0420", "0731", "0813",
}


def slugify(name):
    # Normalize a display name to AA slug style.
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")

    # Drop trailing non-identity tokens (Contributor, preview, Exp).
    parts = text.split("-")
    while len(parts) > 1 and parts[-1] in GO_STRIP_SUFFIXES:
        parts.pop()
    return "-".join(parts)


# Ranking of reasoning effort levels (higher wins). The base slug with no
# effort suffix counts as the default effort.
EFFORT_RANK = {
    "max": 5,
    "xhigh": 4,
    "high": 3,
    "medium": 1,
    "low": 0,
    "non-reasoning": -1,
}
DEFAULT_EFFORT_RANK = 2


def effort_rank(tail_tokens):
    # Map tail tokens to an effort rank. Version/date tokens (0424...),
    # preview and next are not efforts and keep the default rank.
    if "non" in tail_tokens and "reasoning" in tail_tokens:
        return EFFORT_RANK["non-reasoning"]
    for token in tail_tokens:
        if token in EFFORT_RANK:
            return EFFORT_RANK[token]
    return DEFAULT_EFFORT_RANK


def pick_highest_effort(go_name, slugs):
    # Keep a single slug per Go model: the one with the highest effort.
    # Ties resolve to fewer tail tokens, then alphabetical for stability.
    base = slugify(go_name)

    def sort_key(slug):
        tail = slug[len(base):].lstrip("-") if slug.startswith(base) else slug
        tokens = tail.split("-") if tail else []
        return (-effort_rank(tokens), len(tokens), slug)

    return sorted(slugs, key=sort_key)[0]


def filter_highest_effort(report):
    # Reduce a match report to one slug per Go model (highest effort only).
    # Returns (slugs, highest_report) preserving Go order, deduplicated.
    highest_report = []
    for go_name, hits in report:
        if not hits:
            highest_report.append((go_name, []))
            continue
        highest_report.append((go_name, [pick_highest_effort(go_name, hits)]))

    seen, slugs = set(), []
    for _, hits in highest_report:
        for slug in hits:
            if slug not in seen:
                seen.add(slug)
                slugs.append(slug)
    return slugs, highest_report


def match_models(go_names, aa_models):
    # Index AA slugs for exact lookups.
    by_slug = {m["slug"]: m for m in aa_models if m.get("slug")}

    matched, missing, report = [], [], []
    for go_name in go_names:
        base = slugify(go_name)

        # Accept the base slug plus known effort/revision suffixes only.
        hits = []
        for slug, model in by_slug.items():
            if slug != base and not slug.startswith(base + "-"):
                continue
            tail = slug[len(base):].lstrip("-")
            tokens = tail.split("-") if tail else []
            if all(t in ALLOWED_SUFFIX_TOKENS for t in tokens):
                hits.append(model)

        hits.sort(key=lambda m: m["slug"])
        if hits:
            matched.extend(h["slug"] for h in hits)
            report.append((go_name, [h["slug"] for h in hits]))
        else:
            missing.append(go_name)
            report.append((go_name, []))

    # Preserve order while removing duplicates.
    seen, slugs = set(), []
    for slug in matched:
        if slug not in seen:
            seen.add(slug)
            slugs.append(slug)
    return slugs, report, missing
