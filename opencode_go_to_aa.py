"""Build an Artificial Analysis filter from the current Opencode Go model list.

Fetches the Go lineup from the opencode.ai/go page bundle, matches every entry against
the full Artificial Analysis model manifest (AES-GCM encrypted on their
site) and prints a shareable ``?models=`` URL plus a Model Set JSON file
that can be saved through the Save/Load buttons in the AA model dropdown.

Requires: pip install cryptography
Usage: python opencode_go_to_aa.py [--set-name "Opencode Go"] [--out-dir .]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from src.aa_catalog import AA_MODELS_URL, AA_STORAGE_KEY, fetch_aa_models
from src.go_source import fetch_go_models
from src.matcher import filter_highest_effort, match_models
from src.state import diff_runs, load_state, save_state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set-name", default="Opencode Go")
    parser.add_argument("--out-dir", default=".")
    parser.add_argument("--state", default="state.json")
    args = parser.parse_args()

    # Read the current Go lineup from the opencode.ai/go page.
    go_names = fetch_go_models()
    print(f"Go models found: {len(go_names)}")

    # Read the full Artificial Analysis catalog.
    aa_models = fetch_aa_models()
    print(f"AA models found: {len(aa_models)}")

    # Match every Go entry to one or more AA slugs.
    slugs, report, missing = match_models(go_names, aa_models)

    # Keep only the highest effort variant of each Go model.
    highest_name = f"{args.set_name} Highest"
    slugs_highest, report_highest = filter_highest_effort(report)

    # Diff against the previous run snapshot.
    state_path = os.path.join(args.out_dir, args.state)
    old = load_state(state_path)
    diff = diff_runs(old, go_names, slugs, slugs_highest)
    if old.get("updated") is None:
        print("Primera ejecución: todo se registra como agregado.")
    elif all(not v for v in diff.values()):
        print("Sin cambios.")
    else:
        if diff["added_go"]:
            print(f"Nuevos en Go: {diff['added_go']}")
        if diff["removed_go"]:
            print(f"Salieron de Go: {diff['removed_go']}")
        if diff["added_slugs"]:
            print(f"Slugs agregados: {diff['added_slugs']}")
        if diff["removed_slugs"]:
            print(f"Slugs quitados: {diff['removed_slugs']}")
        if diff.get("added_highest"):
            print(f"Slugs Highest agregados: {diff['added_highest']}")
        if diff.get("removed_highest"):
            print(f"Slugs Highest quitados: {diff['removed_highest']}")
    save_state(state_path, go_names, slugs, slugs_highest)

    for go_name, hits in report:
        detail = ", ".join(hits) if hits else "SIN MATCH en AA"
        print(f"  - {go_name} -> {detail}")
    print("Highest effort por modelo:")
    for go_name, hits in report_highest:
        detail = ", ".join(hits) if hits else "SIN MATCH en AA"
        print(f"  - {go_name} -> {detail}")
    for name in missing:
        print(f"WARNING: '{name}' has no match in AA yet.", file=sys.stderr)

    # Build the shareable filter URL (selection lives in ?models=).
    url = f"{AA_MODELS_URL}?models=" + ",".join(slugs)
    url_highest = f"{AA_MODELS_URL}?models=" + ",".join(slugs_highest)

    # Build the Model Set payload for the Save/Load feature.
    model_set = {
        "name": args.set_name,
        "storageKey": AA_STORAGE_KEY,
        "modelSlugs": slugs,
        "date": datetime.now(timezone.utc).isoformat(),
    }
    model_set_highest = {
        "name": highest_name,
        "storageKey": AA_STORAGE_KEY,
        "modelSlugs": slugs_highest,
        "date": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "opencode_go_models.txt"), "w") as f:
        f.write("\n".join(go_names) + "\n")
    with open(os.path.join(args.out_dir, "aa_opencode_go_url.txt"), "w") as f:
        f.write(url + "\n")
    with open(os.path.join(args.out_dir, "aa_opencode_go_set.json"), "w") as f:
        json.dump(model_set, f, indent=2)
    with open(os.path.join(args.out_dir, "aa_opencode_go_url_highest.txt"), "w") as f:
        f.write(url_highest + "\n")
    with open(os.path.join(args.out_dir, "aa_opencode_go_set_highest.json"), "w") as f:
        json.dump(model_set_highest, f, indent=2)

    print(f"\nMatched {len(slugs)} AA slugs, missing {len(missing)}.")
    print(f"URL: {url}")
    print(f"To persist: open the URL, open the models dropdown, Save as '{args.set_name}'.")
    print(f"\nHighest effort: {len(slugs_highest)} AA slugs.")
    print(f"URL Highest: {url_highest}")
    print(f"To persist: open the URL, open the models dropdown, Save as '{highest_name}'.")


if __name__ == "__main__":
    main()
