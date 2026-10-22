# Catalog development

Updated 2026-10-22. Owner: IRGS Catalog. Push destination:
`KingSav3ge/IRGS-Catalog/main`. The coordinator in **IRGS Enviroment** owns joined
integration and review of the exact Engine/App/Catalog dependency set.

## Completed

| ID | Increment | Evidence |
| --- | --- | --- |
| CAT-01 | Independent Catalog data and preserved original campaign designs. | `b6c1362`; component instructions and source verifier. |
| CAT-02 | Expanded v0.5 previews for all 44 concepts, preserving prior adoption and runtime boundaries. | `c70dc16`; import reconciliation and pinned original package. |
| HD-01a | Deterministic 16 MiB whole-ZIP packaging and verified reconstruction tools. | `IRGS_Catalog/historical_details_package.py`; synthetic multipart round-trip and rejection tests. |
| HD-01b | Manifest/member-index contract and explicit unavailable state in Catalog verification. | `IRGS_Catalog/historical_details/README.md`; `verify_catalog.py`; missing-source checks. |
| HD-01c | Inspect supplied extracted Drive folder and preserve its unchanged delivery manifest as intake evidence. | `IRGS_Catalog/historical_details/intake/`; no claim of full payload verification. |

## Active

`historical-details-01` remains the assigned increment. Package tooling is ready
for the exact original ZIP. The manifest's shared selection fields have been
checked against the Engine reader's working draft. Coordinator review and App
qualification remain separate from source-tool tests.

The campaign portfolio still marks Century, Kira and Rise **In Development** and
41 other concepts **Planned**. These labels describe concept development; the
Catalog does not implement their Engine mechanics or App viewer.

## Blocked

- **HD-02: preserve the complete original archive.** The uploaded 533 MB ZIP
  exceeds the worker's 32 MiB attachment-transfer limit. The user provided the
  original ZIP's Drive link and its metadata matches the expected name and size.
  The authenticated Drive plugin has a separate 256 MiB download limit; the
  direct link requires sign-in. Required input: an accessible streaming download
  URL or original ZIP workspace path.
- **HD-03: full dataset acceptance.** Exact 533,064,680-byte reconstruction and
  SHA-256, every actual member/delivery binding and actual collection counts
  cannot be verified without the original source. Synthetic tests do not close
  this item.
- **HD-04: candidate dependency selection.** A complete Catalog payload and
  coordinator-reviewed Engine and App commits are required. No qualified
  Historical Details component set is published by this increment.

## Remaining

1. Verify the expected original identity, import all 32 byte parts, and check
   exact reassembly and every member against the full source dataset.
2. Review actual delivery-binding coverage, unbound files and collection counts;
   preserve original rights, sources, uncertainty and any disclosed limitations.
3. Refresh Catalog source pins and deliver the exact commit and executed checks
   for coordinator review. App owns pinning and testing the reviewed dependencies.
4. Continue concept editorial/historical review, artwork and packaging decisions
   from the existing decision register. Full campaign verification and release
   remain independent of public previews and archive preservation.

## Verification record

See `HISTORICAL_DETAILS_VALIDATION.json` for commands, counts, dependency scope,
unrun acceptance checks and source-access findings. All behavioral fixtures are
synthetic and temporary; no user campaign saves are read or migrated.
