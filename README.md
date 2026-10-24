# IRGS Catalog — 3.4.0 development

Independent campaign catalogue data and design source for [IRGS](https://github.com/KingSav3ge/IRGS). The App viewer remains in [IRGS-APP-WEB](https://github.com/KingSav3ge/IRGS-APP-WEB); technical content libraries, profiles, campaign canon and initializers remain in [IRGS-Engine](https://github.com/KingSav3ge/IRGS-Engine).

`IRGS_Catalog/data/` contains campaign discovery listings and 44 concept previews: 31 launch targets, 12 future campaigns and one independent simulation system. These are not 44 released games. `IRGS_Catalog/design/campaign_catalogue/` preserves the original v0.4 specification and implementation scope.

```bash
git clone https://github.com/KingSav3ge/IRGS-Catalog.git
cd IRGS-Catalog
python -B IRGS_Catalog/verify_catalog.py
```

Python 3.12+ is sufficient; no packages, App, Engine, API keys or user saves are required. After intentional content edits, run `python -B tools/refresh_component_releases.py --component catalog`, verify, review and commit. Refreshing hashes establishes source identity, not campaign approval or passing App tests. Preserve supplied source documents byte for byte and add new versions separately.

Catalog verification also checks campaign record IDs, types, slate and development
statuses, explicit preview/release/readiness flags, discovery IDs and starting
references. Duplicate IDs and release, entitlement or runtime availability claims
in preview inputs fail even after source hashes are refreshed. Internal drafts
remain valid source records; App owns their exclusion from public projection.

The App pins this repository in its `Catalog/` submodule. Qualify a specific Catalog commit with the App and its pinned Engine before committing a dependency update. The joined `IRGS/main` keeps complete sources in `IRGS_Catalog/` and records the exact Catalog commit in `COMPONENTS.json`. See [integration instructions](https://github.com/KingSav3ge/IRGS/blob/main/COMPONENT_REPOSITORIES.md).

Preview data cannot grant playable starts, entitlements, live effects or full release approval. Existing campaigns retain their actual committed world and history. Kira v0.5 working canon belongs to the Engine; catalogue descriptions cannot supersede it.

## Expanded v0.5 source

Active preview data now uses the user-selected v0.5 update for the same 44 concepts, including expanded synopses, perspectives, experiences, systems and design checks. Exact supplied records and readable briefs live in `IRGS_Catalog/design/catalogue_v0_5/`; the original ZIP is preserved under `IRGS_Catalog/design/source_packages/`. `IRGS_Catalog/design/CATALOGUE_V0_5_IMPORT.json` records source verification and reconciliation with existing adoption decisions. Edit the active `data/` view for curated App updates; preserve supplied source files and add new versions separately.

The supplied package's older defaults and Kira notes do not revoke current approved previews, adopted Kira v0.5 canon or the reviewed Century/Rise slices. Existing runtime availability remains authoritative.

## Historical Details and development status

[DEVELOPMENT.md](DEVELOPMENT.md) tracks completed, active, blocked and remaining
Catalog work. [Historical Details](IRGS_Catalog/historical_details/README.md)
defines whole-archive preservation and verified 16 MiB parts. The complete
Historical Grand Archive 1.1 ZIP is preserved in 32 ordered parts, with exact
reassembly, all 5,146 files, all 5,145 delivery bindings and ten reader collection
counts verified. The manifest reports `complete`. Engine/App compatibility
evidence and remaining coordinator integration work are recorded separately;
archive preservation grants no campaign release or new rights.

The [synthetic Solo R00 evaluation fixture](IRGS_Catalog/evaluation/solo_r00_v1/README.md)
supplies separate actor inputs and evaluator-only expectations for the actual
Rise operations, finite shelter work, rejection and durable request recovery.
It is test content outside public campaign discovery. Catalog verification checks
its schema and source separation; exact Engine/App consumer tests qualify behavior.

The original fixture is integrated in the 3.4.0 development build. Separate
[proposal compatibility checks](IRGS_Catalog/evaluation/solo_r00_proposals_v1/README.md)
run its ten cases through the current Engine/App proposal HTTP flow while
preserving the original fixture and dependency evidence. General narration and
dialogue evaluation awaits a supported Engine/App contract.

The [routine response library](IRGS_Catalog/responses/routine_v1/README.md) contains
325 authored variants across 82 families and 12 composition recipes. Its local
formatter joins typed actor-scoped facts without a provider request, preserves
exact committed receipts and supplies editable player drafts. It is intended
for Engine/App routine-first presentation so AI can be reserved for demanding
supported responses. Production selection and dependency integration remain with
those consumers; no measured live API saving is claimed before they adopt it.
