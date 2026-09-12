"""Fetch the full Artificial Analysis model catalog."""

import gzip
import hashlib
import json
import re

from src.go_source import fetch_bytes

AA_MODELS_URL = "https://artificialanalysis.ai/models"
AA_STORAGE_KEY = "aa-saved-model-sets"


def extract_manifests(html):
    # Collect every encrypted manifest reference from the page data.
    # Quotes arrive backslash-escaped inside the flight payload.
    found = re.findall(
        r'path\\*":\\*"(/data/[a-f0-9]+\.txt)\\*",\\*"key\\*":\\*"([a-f0-9]+)\\*"',
        html,
    )
    if not found:
        raise RuntimeError("No AA manifests found in models HTML.")
    return found


def decrypt_manifest(data, key_hex):
    # Mirror the site JS: AES-GCM decrypt, then gunzip the JSON payload.
    key = bytes.fromhex(key_hex)
    iv = hashlib.sha256(key).digest()[:12]

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    plain = AESGCM(key).decrypt(iv, data, None)
    return json.loads(gzip.decompress(plain).decode("utf-8"))


def fetch_aa_models():
    # Download the models page and try each manifest until one holds models.
    html = fetch_bytes(AA_MODELS_URL).decode("utf-8", errors="ignore")

    for path, key in extract_manifests(html):
        try:
            payload = decrypt_manifest(fetch_bytes(
                "https://artificialanalysis.ai" + path,
            ), key)
        except Exception:
            continue

        # Keep the manifest that carries the full model catalog.
        models = payload.get("models") if isinstance(payload, dict) else None
        if models and len(models) > 100:
            return models

    raise RuntimeError("Could not decrypt any AA model manifest.")
