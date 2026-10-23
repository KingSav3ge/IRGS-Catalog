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
| SOLO-CAT-01 | Versioned synthetic R00 evaluation content, actor/oracle separation, explicit rights and schema validation. | Ten cases and five legitimate actions; `IRGS_Catalog/evaluation/solo_r00_v1/`; `solo_evaluation.py`. |
| SOLO-CAT-02 | Actual selected Engine/App consumer qualification using temporary synthetic state. | 18 new schema/consumer tests; finite materials, hidden boundary, denial, unsupported action, stale/replayed requests, restart, concurrent duplicate and failed-save recovery. See `SOLO_FIXTURE_VALIDATION.json`. |

## Active priority — 23 October 2026

`solo-runtime-01` Catalog test content is delivered for component review. The
versioned R00 fixture has separate actor-visible inputs and evaluator-only
setup/oracles, explicit processing rights, strict schema/hash validation and
actual Engine/App consumer checks. Engine owns all initialization and execution;
Catalog adds no simulator or public campaign entry. Five legitimate operations
move, found, reserve materials and complete shelter work, consuming four existing
timber bundles across the two households. Rejection and replay preserve state.

Qualification selects Engine `723627e629231b5e90f38b9d52b65c9a3967b92a` and App
`d8dc35ed653e516ccd0cacf91ee9693258491032` in isolated, unedited snapshots. Its
Catalog dependency is explicitly overridden to this candidate for tests; the
App's committed Catalog pin remains `3e898acb2179f18a41d7967817bedf429df29d3f`.
New runtime/provider contracts and production App fixture loading need separate
component work and qualification. The coordinator owns exact App pin updates,
joined acceptance and live prerequisites. Historical Details remains integrated.

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
  joined qualification are complete for historical-details-01.
- The original source-access blocker is resolved. There is no missing source
  input for the Catalog deliverable.
- No Catalog source blocker remains for solo-runtime-01. New-cycle review and
  exact App/joined selection are pending; baseline consumer qualification does
  not approve a new provider runtime or claim live execution.

## Remaining

1. Coordinator review of the exact new Catalog commit and App dependency pinning.
2. Requalify this synthetic content against the next selected Engine/App Solo
   proposal/provider contract and joined candidate. Production App fixture
   integration and configured live-provider smoke tests remain unrun.
3. Preserve original rights, sources, uncertainty and archive bytes in future
   indexing; the ten reader collections remain a view of the full archive.
4. Resume optional catalogue/artwork expansion after the runtime delivery.
   Campaign release remains independent of previews and archive preservation.

## Verification record

See `SOLO_FIXTURE_VALIDATION.json` for current commands, results and exact
dependencies. `HISTORICAL_DETAILS_VALIDATION.json`,
`CAMPAIGN_RECORD_VALIDATION.json` and `COORDINATOR_REPORT_HISTORICAL_DETAILS_01.md`
retain labelled previous-cycle evidence. All behavioral fixtures are synthetic
and temporary; no user campaign saves are read or migrated.

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
does not adopt generated prose. The current R00 fixture supplies validated
synthetic inputs and actual baseline consumer compatibility for the active work
order. It does not run the earlier 16 proposed provider evaluation cases or
complete new provider runtime contracts. New-cycle component review and exact
App/joined dependency selection remain required.
