# AA Go Sync

Builds the **Artificial Analysis** filter for the **Opencode Go** model list, to open manually.

## Requirements

- Python 3.12
- `pip install cryptography pytest`

## Manual usage

```bat
python opencode_go_to_aa.py --out-dir .
```

Generates:

- `opencode_go_models.txt` - the current Go models.
- `aa_opencode_go_url.txt` - AA URL with the filter already applied (`?models=...`). Open it in the browser.
- `aa_opencode_go_set.json` - Model Set payload for Save/Load.
- `state.json` - snapshot of the last run to detect changes.

The second run prints `Sin cambios.` If Go adds or removes models, you will see `Nuevos en Go: [...]` and `Salieron de Go: [...]`.

## Save the filter in AA (once)

1. Open the URL from `aa_opencode_go_url.txt`.
2. Open the models dropdown, hit **Save** with the name `Opencode Go`.

## Troubleshooting

| Symptom | Cause | What to do |
|---|---|---|
| `WARNING: 'X' has no match in AA yet.` | AA does not index that model yet (happened with `Hy4 preview`) | Normal. It gets reported, a slug is never made up. Re-run in a few days. |
| `Go model list not found in any Go page bundle.` | Opencode changed the `/go` page | Check the `goModels` array in the `/_build/assets/*.js` bundles of `opencode.ai/go` and `src/go_source.py`. |
| `Matched 0` or `No AA manifests found` | AA changed its frontend | Save the HTML of `artificialanalysis.ai/models` and check `src/aa_catalog.py`. |

## Tests

```bat
python -m pytest tests/ -v
python -m pytest tests/ -v --live   :: includes network test (slow)
```
