# IRGS-Catalog development

## Current priority — shared IRGS systems

The user's current direction is development across campaigns and themes.
Read [the shared scope](IRGS_SYSTEMS_SCOPE.md) and
[the current work order](COORDINATOR_WORK_ORDER.md) before selecting work.
Rise R00 remains one regression fixture. Shared-system completion requires
supported non-Rise evidence; campaign-specific mechanics retain their own scope.
The records below preserve previously delivered work and historical evidence.

Follow the user's current directions. Own campaign listings, preview data and catalogue design documents under `IRGS_Catalog/`, independently on `main`. App projection, filtering, transport and viewer code belong to IRGS-APP-WEB; technical libraries, profiles, Kira canon and campaign initializers belong to IRGS-Engine. Joined IRGS retains a complete copy.

Read README.md and `IRGS_Catalog/design/campaign_catalogue/README.md`. Treat imported designs as source material, not authority to implement mechanics, activate entitlements or approve campaign releases. Preserve original supplied documents byte for byte and add separately versioned designs for revisions. Preserve the explicit Planned, Concept Draft and In Development distinctions. Preview metadata must never grant launch authority or select hidden facts or future outcomes.

Use Python 3.12+ without -O. After intentional source edits, refresh only Catalog hashes with `python -B tools/refresh_component_releases.py --component catalog`, then run `python -B IRGS_Catalog/verify_catalog.py`. Qualify changes through the App's pinned Catalog dependency and relevant App/interface tests before joining. Refreshing hashes is not test evidence.

Do not copy, migrate or inspect user campaign saves for checks. Use synthetic temporary fixtures. Keep credentials, caches, runtime logs and generated packages out of source. Do not edit dependencies or Engine/App sources from here. Keep historical evidence labelled and report checks actually executed.

## Coordinator work orders

The user assigns cross-component coordination and unified integration to **IRGS Enviroment**. Read `COORDINATOR_WORK_ORDER.md` before selecting the next increment. This chat pushes only its component repository. Report the exact commit and executed checks to the coordinator. Only the coordinator integrates a reviewed Engine/App/Catalog set into joined IRGS/main. Keep this component's development plan current. Work orders and plan edits alone do not complete a component deliverable.
