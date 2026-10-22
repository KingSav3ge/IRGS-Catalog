# IRGS Catalog

Independent campaign catalogue data and design source for [IRGS](https://github.com/KingSav3ge/IRGS). The App viewer remains in [IRGS-APP-WEB](https://github.com/KingSav3ge/IRGS-APP-WEB); technical content libraries, profiles, campaign canon and initializers remain in [IRGS-Engine](https://github.com/KingSav3ge/IRGS-Engine).

`IRGS_Catalog/data/` contains campaign discovery listings and 44 concept previews: 31 launch targets, 12 future campaigns and one independent simulation system. These are not 44 released games. `IRGS_Catalog/design/campaign_catalogue/` preserves the original v0.4 specification and implementation scope.

```bash
git clone https://github.com/KingSav3ge/IRGS-Catalog.git
cd IRGS-Catalog
python -B IRGS_Catalog/verify_catalog.py
```

Python 3.12+ is sufficient; no packages, App, Engine, API keys or user saves are required. After intentional content edits, run `python -B tools/refresh_component_releases.py --component catalog`, verify, review and commit. Refreshing hashes establishes source identity, not campaign approval or passing App tests. Preserve supplied source documents byte for byte and add new versions separately.

The App pins this repository in its `Catalog/` submodule. Qualify a specific Catalog commit with the App and its pinned Engine before committing a dependency update. The joined `IRGS/main` keeps complete sources in `IRGS_Catalog/` and records the exact Catalog commit in `COMPONENTS.json`. See [integration instructions](https://github.com/KingSav3ge/IRGS/blob/main/COMPONENT_REPOSITORIES.md).

Preview data cannot grant playable starts, entitlements, live effects or full release approval. Existing campaigns retain their actual committed world and history. Kira v0.5 working canon belongs to the Engine; catalogue descriptions cannot supersede it.
