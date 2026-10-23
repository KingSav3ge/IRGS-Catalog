# Catalog delivery — historical-details-01

Archived preceding-cycle report. Historical Details was subsequently integrated;
the old remaining-review notes below describe its delivery date. Current work
and dependencies are in `COORDINATOR_REPORT.md` and `DEVELOPMENT.md`.

Owner: **IRGS Catalog**. Repository: `KingSav3ge/IRGS-Catalog/main`. This report
includes the full-payload delivery from
`58ce55672bdd75076b94882bd8715a1d2a1f383a` and the following Catalog validation
increment; resolve the latest candidate's exact SHA from Git.
The preceding tooling-only increment is
`ab3e127f4a0bc504158fd91617e4f76fef5a2f7d`.
The updated work order at `02db97383a8a0c785250b98585253d24f3365a9b`
is included; its AI content/rights dependencies are recorded as future work in
the development plan after reading all three linked coordinator sources.

## Latest Catalog follow-up — CAT-03

Catalog source verification now rejects malformed editorial records even after
their source hashes are refreshed: duplicate/invalid campaign IDs, inconsistent
type/slate, unknown development status, release/entitlement/readiness claims and
runtime availability fields in preview input. Discovery IDs and held starting
references are also checked. Drafts remain valid editorial source records.

Four failures were reproduced against the previous source verifier using small
temporary fixtures. All 16 new regression tests pass. The complete fresh run
passes **55 source/consumer tests and six App catalogue tests, zero skips**;
Catalog verification still passes all 140 source files, 44 concepts and the
complete archive. Only Catalog source pins changed. Campaign data, designs,
archive bytes and manifest pin are identical to the full-payload delivery.
See `CAMPAIGN_RECORD_VALIDATION.json` for commands and tested dependency commits.
App pins and joined integration remain coordinator-owned work.

## Delivered source

`IRGS_Catalog/historical_details/` now preserves the complete original Historical
Grand Archive 1.1 ZIP in 32 ordered 16 MiB byte parts. The original and exact
reassembly match 533,064,680 bytes and SHA-256
`51246eb6898a228f42f0794ed19ce69af275a2a4661c0fb6a1d3baebe3efc773`.
The last part is 12,970,984 bytes; every file is below the 100 MiB import limit.

Manifest path: `IRGS_Catalog/historical_details/manifest.json`.
Manifest SHA-256:
`1543cd65b5c4b3ed6f160565b4e4bf01d09dd44a392d53c7036efcd5c0dcf21f`.
Its status is `complete`; its exact size is 10,581 bytes, below the Engine's
1 MiB manifest limit. The separate member index is pinned by that manifest.

All 5,146 archive files were read and hashed. All 5,145 declared delivery
bindings match; the delivery manifest is the sole self-excluded unbound file.
The database, books, source assets, rights records and ancillary files are
preserved. All ten reader collections were parsed and counted; these are a
partial browsing view of the complete archive, not a substitute payload.

## Consumer contract and executed checks

The Engine manifest contract and API match committed Engine
`b3e7d760a2cf3712292b09328566cf1ed0d78c97`. Actual consumer checks select its
two reader modules and App reference-service modules from
`e8ef2b0e683a46fab4fe586e86afd26196ab2869` in isolated temporary snapshots.
All four module bytes were checked against their committed Git blob identities.

- **Original archive delivery: 39 source/consumer tests passed, zero skips:** 30 synthetic tests, five
  complete-delivery checks and four actual Engine/App service checks. This
  includes exact real-data reassembly, every member/binding, missing, corrupt,
  duplicate and reordered parts, real collection reads and App repair/retry.
- **Six existing App catalogue tests passed, zero skips:** all 44 previews,
  proposal/launch boundaries and temporary synthetic-world HTTP continuity.
  That regression run used App `aac20055270cc64ba870061085cd8f6bfe43a93c`
  with its pinned Engine `c0777be7e68021bd1bee66437d555390778c0adb` and this
  Catalog selected explicitly. It does not qualify new dependency pointers.
- Catalog verification passed for 140 source files; only Catalog source pins
  were refreshed. Existing campaign data and original design packages are
  unchanged. No user campaign save was read or migrated.

## Remaining coordinator work

There is no missing source input. The initial download blocker is resolved.
Review this exact Catalog commit and the exact Engine/App candidates; App owns
its dependency pointer update and full HTTP/interface qualification of that set.
Only the coordinator selects and tests the isolated joined candidate. No other
repository or dependency pointer is changed by this delivery.

Archive integrity establishes source preservation, not historical truth, new
rights, campaign adoption or release approval. See
`HISTORICAL_DETAILS_VALIDATION.json` for collection counts, commands, module
identities and the remaining unrun integration checks.
