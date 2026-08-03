# INPUT-SPEC — gtin-validator (client mode)

What to hand the validator in a client engagement. Written so a client's IT person can
produce the file without a call.

## The file

- **CSV or XLSX.** Read via `lailara_engagement`'s tolerant reader: UTF-8 / UTF-8-BOM /
  latin-1; comma / semicolon / tab; leading blank rows and trailing junk dropped; header
  whitespace trimmed.
- One row per product. Extra columns are ignored.

## Required column

| Canonical | Type | Required | Used for |
|---|---|---|---|
| `gtin` | identifier (text) | yes | The GTIN/UPC/barcode validated against GS1 standards. §1 |

- **Read as text.** GTINs keep leading zeros; `012345678905` is never parsed to `12345678905`.
- Accepted GTIN lengths: 8, 12 (UPC-A), 13 (EAN), 14 (ITF-14 case). The engine checks the
  mod-10 check digit, GTIN-14 indicator rules, duplicates, company-prefix consistency, and
  unit→case hierarchy.

## Column mapping (engagement.yml)

If the client's header isn't literally `gtin`, map it:

```yaml
client:
  name: "Meridian Farms"
engagement:
  id: "MER-2026-08"
as_of_date: "2026-07-31"
columns:
  gtin: "UPC / Barcode"     # client header -> canonical
```

A case/whitespace-insensitive match (e.g. `GTIN`, `UPC`, `barcode`) is auto-detected and
disclosed; anything else must be mapped here. If no GTIN column resolves, the run produces a
**Data Readiness Report** naming the missing column instead of results.

## Run

```bash
# with lailara_engagement installed: pip install -e ../engagement-template/lib
python client_mode.py --config engagement.yml --input client-data/items.csv \
    --out client-output [--final]
```

Outputs to `client-output/` (gitignored):
- `gtin-readiness-summary.html` — branded, provenance-footed (input SHA-256, row counts,
  `as_of_date`, config hash), DRAFT-watermarked until `--final`.
- `gtin-validation.csv` — the full per-GTIN report.
- or `data-readiness-report.html` if the GTIN column is missing.
