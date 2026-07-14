# raw/inbox — Drop Zone

Unprocessed source files land here (via the OneDrive → Power Automate bridge, or a direct commit). The ingestion pipeline picks up every new file, extracts durable knowledge into the vault zones, then moves the file to `raw/processed/`.

- Use descriptive, dated filenames: `OTC design review 2026-07-15.pdf`, not `notes.pdf`.
- Never treat files here as vault knowledge — they are raw material only.
- Do not edit or reorganize files in this folder; the pipeline owns it.
