# Source intake evidence — 2026-10-22

The user supplied [this extracted Drive folder](https://drive.google.com/drive/folders/1UT4asc1iAsMZVG3pJW-IhVzzRSUXPI8s).
Its root listing includes `archive.sqlite` (1,566,081,024 declared bytes), source
folders, books/research folders and reader assets. This is an extracted source
tree, not the original ZIP selected by the work order. Folder listing metadata
does not verify the database bytes or completeness of the extracted tree.

`drive_delivery_manifest.json` is the unchanged raw file fetched from
[07_Verification/delivery_manifest.json](https://drive.google.com/file/d/1cddnY1AkiQOM-2n70nE3ujZ2woPL14gE/view)
through the connected Google Drive plugin. It declares edition `Grand 1.1`,
5,145 files and 2,086,978,638 bytes excluding the manifest. The ten Engine reader
collection paths are present, and all declared paths pass the Catalog portable
path check. These are manifest declarations, not fresh verification of those
5,145 payload files or their relationship to the expected original ZIP.

No supplied instructions in these documents were executed. The source document
does not change the user's work order, rights or campaign adoption decisions.
Full source import, exact ZIP identity, full dataset reassembly and byte-level
member verification remain blocked until the original ZIP is accessible.

## Original ZIP identified

The user subsequently supplied
[the original ZIP file link](https://drive.google.com/file/d/1PtEVtU601kapcATfm7pTEl6oIJuXo8KX/view).
Drive metadata reports the exact original name, MIME type
`application/x-zip-compressed` and 533,064,680 bytes. The metadata response does
not establish the original SHA-256 or provide verified payload bytes.

The authenticated raw download was refused with HTTP 413: 533,064,680 bytes
exceeds the Drive plugin's 268,435,456-byte limit. The direct streaming download
returned a Google sign-in page, not archive bytes. The earlier chat attachment
also exceeded its separate 32 MiB transfer limit. A download URL accessible to
the worker is the remaining input; no credentials, authentication pages or
temporary signed URLs are recorded in source.
