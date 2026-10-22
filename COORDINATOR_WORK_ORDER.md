# IRGS Catalog work order — historical-details-01

Assigned by the user through IRGS Enviroment on 2026-10-22. Owner: **IRGS Catalog**. Repository: `KingSav3ge/IRGS-Catalog`.

## Current state and input

Expanded v0.5 provides 44 verified concept records. The user now authorizes storing the **Historical Grand Archive 1.1** in parts under **Historical Details**. The source ZIP is not present in these cloud checkouts. The previous local attachment record identifies 533,064,680 bytes and SHA-256 `51246eb6898a228f42f0794ed19ce69af275a2a4661c0fb6a1d3baebe3efc773`. This is an expected source identity from the prior local check, not a new cloud verification. Obtain an accessible copy or use a local task with the user's file access; never manufacture missing source data.

## Deliverable

Own the payload and its manifest in `IRGS_Catalog/historical_details/`, with display name **Historical Details**. Keep Engine parsing/runtime code in IRGS-Engine and viewer code in IRGS-APP-WEB. Preserve the existing 44 campaign records and original design packages.

First preserve the entire original ZIP through deterministic ordered byte parts, so its central database, source assets, books and ancillary files are not silently omitted. Use 16 MiB parts (the final part may be smaller); record each relative path, ordinal, byte count and SHA-256. The manifest records schema/version, archive name, exact original size and SHA-256, part size/order and completion status. Paths must be relative, portable and contained in this directory. Every part stays below the current 100 MiB source-import limit. A package with only the ten structured reader collections is a partial derivative, not the full archive.

Keep original delivery/rights/source records intact inside the preserved payload. Any separately indexed derivative needs collection/member identity, source and uncertainty metadata, record counts and its relationship to the exact preserved archive. Source-specific attribution remains truthful. A declaration of storage does not establish historical truth, a new license or campaign adoption.

## Acceptance

- Exact reassembly yields the expected original archive bytes and SHA-256; validate the actual full dataset, not only a small fixture.
- Every part is present once in its recorded order, and corruption/missing/reordered parts fail verification.
- Validate archive member/collection bindings and report complete versus partial coverage explicitly.
- Coordinate the manifest with Engine and App before publishing a candidate pin.
- Add/update a Catalog development plan with completed, active, blocked and remaining work.
- Refresh Catalog source pins after source edits; run Catalog verification and meaningful split/reassembly tests. Never commit installation caches or user saves.

**Current blocker:** the original ZIP needs to be available to the worker. This work order contains no archive payload and is not a completed import.

## Delivery and review

Work only in your component repository and push its `main`. Do not publish component source to joined IRGS, change another component, or reset existing work. Read repository instructions and current plans first. Keep completed, active and remaining work explicit. Preserve accurate source attribution and distinguish implemented behavior, design requirements and reference data.

Return the full pushed commit SHA, changed behavior, dependency commits, checks actually executed, skipped/unrun checks, open findings and any missing input to the coordinator chat **IRGS Enviroment**. Update the development plan with that increment. A planning-only commit is not the requested viable component update.

The coordinator reviews exact commits. When Engine, App and Catalog each have an approved viable update for this cycle, and the App pins exactly those Engine and Catalog commits, the coordinator tests an isolated joined candidate and imports it into `KingSav3ge/IRGS/main`. Until then the existing integrated component set remains selected. Changes requested by the user take precedence.

## Additional backlog — AI evaluation content and rights

The user supplied an AI provider strategy. Read the coordinator's [master-spec addendum](https://github.com/KingSav3ge/IRGS/blob/main/AI_PROVIDER_STRATEGY.md), [checked research](https://github.com/KingSav3ge/IRGS/blob/main/AI_PROVIDER_REVIEW.md) and [16 synthetic evaluation cases](https://github.com/KingSav3ge/IRGS/blob/main/provenance/qa/ai_provider_strategy/EVALUATION_CASES.json). Record the relevant content/rights dependencies in the Catalog plan while continuing the Historical Details deliverable. No provider configuration belongs in catalogue records.

For future evaluation inputs, preserve source identity, rights, uncertainty, version and permitted processing classification. Public availability alone does not establish permission to send content to an external provider. Private campaign saves are excluded. Synthetic evaluation characters and situations are labelled fixtures; they do not become campaign canon, playable starts or released products. Keep evaluator-only hidden facts out of material sent to an actor model.

Catalog owns independently reviewed content and provenance; Engine owns provider/access/validation code and App owns administration/presentation. Do not copy the historical archive into model prompts, select models through campaign metadata, store keys/prices as campaign facts or adopt generated prose as historical truth. The first live provider step does not require a gratuitous catalogue data change. Existing three-component review gates and complete-archive acceptance still apply; these additional requirements are not a completed import or viable component delivery.
