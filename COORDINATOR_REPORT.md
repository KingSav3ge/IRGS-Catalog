# Catalog interoperability — all three development repositories pulled

Pulled main from all three development repositories as requested. Catalog was
already at `4bd572843cebc94e7d043c3706d1be85249d6c10`; Engine fast-forwarded to
`0fdfc21f45510e3fd99fd6a8087cd3314d077267` and App to
`67411f8ef5214c8cb51af2b244590751e6ea20df`. App submodules were checked out at
its committed pointers. No Engine/App implementation edit, commit or push was made.

## Exact compatibility matrix

App still pins Engine `2f9476c6090878257d17cab3ad3a83a7ce18a5dc` and Catalog
`27fff8385d1c01fdfe9ad7254b7647e6bc12a01e`. Catalog-side tests therefore qualify
two explicit Engine roles against current App and this Catalog candidate:

| Engine role | Exact source | HTTP checks |
| --- | --- | ---: |
| Development | `0fdfc21f45510e3fd99fd6a8087cd3314d077267` | 11 |
| App-pinned | `2f9476c6090878257d17cab3ad3a83a7ce18a5dc` | 11 |

`evaluation/development_interop_v1/compatibility.json` records the new matrix
under `irgs-development-interop-v1`, with exact source and original compatibility
hashes. The new validator checks role/pin consistency and scope. Historical
manifests, payloads, guards and evidence remain unchanged. Current overrides are
reported as tested candidates, not adopted App dependency updates.

## What passed from Catalog

The new consumer class reuses all nine native HTTP response/recovery checks under
its own exact matrix guard. Each role independently initializes Rise R00 and the
existing optional fictional quay opening in the 1415 campaign. Catalog text,
Engine runtime and App presentation agree on the unchanged depot bytes and public
contracts. Actual success/failure, zero spans, editable non-submitting drafts,
explicit declarations, older saved presentations, failed-save retry, source
fallback, foreign/stale requests and restore remain covered.

Two additional tests use App's now-published received-process controls. Trusted
synthetic setup establishes an observation or shelter-work process through the
real typed Engine API while the host is stopped. Public preparation changes no
campaign bytes and execution requires explicit acceptance. Observation completes
at its actual 20-second rule boundary and delivers knowledge then; Rise work
preserves 100 seconds of progress across zero-second pause/resume, respects
existing material boundaries and completes 3,600 seconds of work. Catalog-backed
phase presentations survive saved-result lookup, restart and exact retry.

These tests create no App process-start flow, capability discovery rule or
campaign adapter. Broker dispatch and direct provider transport are forbidden
throughout the consumer tests. Routine provider calls are zero. Only temporary
synthetic saves and loopback HTTP are used.

## Fresh execution — 25 October 2026

**237 tests passed, zero skips:**

| Scope | Passed |
| --- | ---: |
| Catalog source/archive/content and compatibility contracts | 118 |
| Development Engine/current App/Catalog HTTP consumers | 11 |
| App-pinned Engine/current App/Catalog HTTP consumers | 11 |
| Original integrated-pair consumers with original selectors | 9 |
| Current Engine phase/offline/depot regressions | 55 |
| Current App process/shared/portfolio regressions | 33 |

Catalog integrity passes 175 files, all 44 previews and the complete original
archive: 32 parts, 5,146 files and 5,145 bindings. Current Engine integrity passes.
The App's full component verifier passes against its actual checked-out Engine
and Catalog pins, including all 55 App files. Its verified-byte Catalog intake
regression remains passing. Only Catalog source hashes were refreshed.

Exact commands, roots, hashes and results are in
[DEVELOPMENT_INTEROP_VALIDATION.json](DEVELOPMENT_INTEROP_VALIDATION.json).
The original 185-test integrated-pair record remains unchanged in
`INTEGRATED_RESPONSE_VALIDATION.json`; its report is preserved as
`COORDINATOR_REPORT_INTEGRATED_RESPONSES_01.md`.

## Remaining dependencies

No Catalog-side interoperability blocker was found in the named response and
received observation/work paths. App/coordinator adoption of current dependency
pointers and exact-set joined/browser/package qualification remain separate.
The current Engine now publishes process-start discovery; current App still
pins its earlier Engine and reports `start_available: false`. Public start-flow
adoption belongs to App. Communication/source controls and further contexts
require matching owner interfaces. General dialogue, live/model quality,
production savings and wider DEV/C2 retain their existing scope.

The depot remains exactly 750 system variants, 250 editable drafts and 32 recipes.
No old content, original archives, user saves or private external fixtures were
changed or transferred. This chat pushes only `IRGS-Catalog/main`; the component
chat reports the full new SHA. Repository publication is the coordinator handoff.
