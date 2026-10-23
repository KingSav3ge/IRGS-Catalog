# Catalog development

Target iteration: **IRGS 3.4.0 — in development**. See the active Solo runtime work order and completion plan. Previously qualified versions and evidence retain their recorded identities.

Updated 2026-10-23. Owner: IRGS Catalog. Push destination:
`KingSav3ge/IRGS-Catalog/main`. The coordinator in **IRGS Enviroment** owns joined
integration and review of the exact Engine/App/Catalog dependency set.

## Completed

| ID | Increment | Evidence |
| --- | --- | --- |
| CAT-01 | Independent Catalog data and preserved original campaign designs. | `b6c1362`; component instructions and source verifier. |
| CAT-02 | Expanded v0.5 previews for all 44 concepts, preserving prior adoption and runtime boundaries. | `c70dc16`; import reconciliation and pinned original package. |
| CAT-03 | Validate editorial campaign records before App handoff, independently of refreshed source hashes. | `verify_catalog.py`; `tools/tests/test_campaign_records.py`; `CAMPAIGN_RECORD_VALIDATION.json`. |
| HD-01a | Deterministic 16 MiB whole-ZIP packaging and verified reconstruction tools. | `IRGS_Catalog/historical_details_package.py`; synthetic multipart round-trip and rejection tests. |
| HD-01b | Manifest/member-index contract and explicit unavailable state in Catalog verification. | `IRGS_Catalog/historical_details/README.md`; `verify_catalog.py`; missing-source checks. |
| HD-01c | Inspect supplied extracted Drive folder and preserve its unchanged delivery manifest as intake evidence. | `IRGS_Catalog/historical_details/intake/`; no claim of full payload verification. |
| HD-02 | Retrieve the exact original ZIP and preserve every byte in 32 parts. | Original and reassembled size/SHA-256 verified; original database, books and ancillary files retained. |
| HD-03 | Verify the actual full dataset, source bindings and reader collection counts. | All 5,146 files hashed, all 5,145 delivery bindings verified; one self-excluded delivery manifest; ten collections counted. |

## Active priority — 23 October 2026

`solo-runtime-01` assigns a small versioned synthetic R00-derived evaluation scenario, with separate actor-visible inputs and evaluator-only oracles, explicit rights/processing labels and actual Engine consumer tests. Follow [the new work order](COORDINATOR_WORK_ORDER.md). This priority update delivers no new fixture or runtime. Historical Details and its compatible App pins are integrated; its source-access and review blockers are resolved.

## Previous-cycle execution record

`historical-details-01` was the preceding increment. Full source preservation
and byte-level acceptance are complete. The manifest matches committed Engine
`b3e7d760a2cf3712292b09328566cf1ed0d78c97`. Consumer checks use that reader and
the App reference service from `e8ef2b0e683a46fab4fe586e86afd26196ab2869`
as explicit isolated source snapshots. See the validation record for executed
results; these checks do not change or approve App dependency pointers.

Executed acceptance: 39 source/consumer tests passed (30 synthetic, five actual
complete-delivery checks, four actual Engine/App service checks), plus six
existing App catalogue tests. Full Catalog integrity verification passed for 140
source files and all 44 existing campaign concepts. No checks in these runs were
skipped. The complete multipart set subsequently passed coordinator review, App pinning
and joined qualification; these older test identities remain historical evidence.

The campaign portfolio still marks Century, Kira and Rise **In Development** and
41 other concepts **Planned**. These labels describe concept development; the
Catalog does not implement their Engine mechanics or App viewer.

The Catalog follow-up, `CAT-03`, closes a reproduced authoring gap:
refreshed source hashes alone previously allowed duplicate catalogue IDs,
unknown development statuses and release/entitlement claims to pass verification.
Source verification now checks identity/type/slate consistency, explicit preview
and readiness flags, discovery IDs and held starting references. It preserves
Planned, Concept Draft and In Development as separate states; App remains the
owner of draft filtering and runtime projection. Current campaign descriptions,
source archives, Historical Details bytes and its manifest pin are unchanged.
See `CAMPAIGN_RECORD_VALIDATION.json` for this follow-up's executed checks.

Fresh follow-up checks passed: 55 source/consumer tests (including the 16 new
record-validation tests), six App catalogue tests and complete Catalog integrity
verification. All tests executed with zero skips.

## Blocked

- **HD-04 resolved:** coordinator review, exact App dependency selection and
  joined qualification are complete for historical-details-01. The new synthetic
  runtime fixture and its consumer qualification remain undelivered.
- The original source-access blocker is resolved. There is no missing source
  input for the Catalog deliverable.

## Remaining

1. Deliver the versioned synthetic runtime scenario, separated actor/evaluator
   files, rights/processing labels and fixture validator for solo-runtime-01.
2. Qualify that fixture against the actual selected Engine handlers, then hand
   exact source and checks to App and the coordinator for connected acceptance.
3. Preserve original rights, sources, uncertainty and archive bytes in future
   indexing; the ten reader collections remain a view of the full archive.
4. Resume optional catalogue/artwork expansion after the runtime delivery.
   Campaign release remains independent of previews and archive preservation.

## Verification record

See `HISTORICAL_DETAILS_VALIDATION.json` for commands, counts, dependency scope,
unrun acceptance checks and source-access findings. All behavioral fixtures are
synthetic and temporary; no user campaign saves are read or migrated.

## AI evaluation content and rights backlog

The coordinator added this sequenced backlog in work-order commit
`02db97383a8a0c785250b98585253d24f3365a9b`. The
[master addendum](https://github.com/KingSav3ge/IRGS/blob/main/AI_PROVIDER_STRATEGY.md),
[research review](https://github.com/KingSav3ge/IRGS/blob/main/AI_PROVIDER_REVIEW.md)
and [16 proposed evaluation cases](https://github.com/KingSav3ge/IRGS/blob/main/provenance/qa/ai_provider_strategy/EVALUATION_CASES.json)
were read; model evaluations remain unrun.

Future Catalog evaluation inputs must preserve source identity, version, rights,
uncertainty and permitted processing classification. Public access is not
permission for external processing. Exclude private saves; label synthetic
characters/situations as evaluation fixtures rather than campaign canon or
playable content. Keep evaluator-only hidden facts out of actor/model inputs.
Review any derivative or creator processing rights independently before use.

Engine owns provider access, routing and validation; App owns administration and
presentation. Catalog records do not select models, store credentials/prices or
authorize transfer. This increment sends no archive content to providers and
does not adopt generated prose. The active work order now requests a small reusable synthetic fixture for
proving the runnable Solo loop. Historical Details review and App dependency
selection are complete. Fixture validation, actual Engine compatibility and
new-cycle component review remain required.
