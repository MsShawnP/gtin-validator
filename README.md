# GTIN Product Data Validator

[![CI](https://github.com/MsShawnP/gtin-validator/actions/workflows/ci.yml/badge.svg)](https://github.com/MsShawnP/gtin-validator/actions/workflows/ci.yml)

A diagnostic tool for specialty food brands preparing product data for retailer submission. Validates GTINs against GS1 standards with retailer-specific context — built for operations teams, not developers.

**[Try the live tool →](https://msshawnp-gtin-validator-app-yz0mxn.streamlit.app/)**

---

## What this does

Most GTIN validators tell you "valid" or "invalid." This one tells you **why it matters** — which retailers will reject your submission, what it'll cost you, and what to fix first.

### Features

- **Batch validation** — paste GTINs or upload a CSV, validate your entire product list at once
- **GS1 check digit validation** — mod-10 algorithm per GS1 General Specifications
- **Format checking** — valid lengths (GTIN-8, 12, 13, 14), numeric-only, indicator digit rules
- **Duplicate detection** — flags reused GTINs across different items
- **GS1 Company Prefix consistency** — detects mixed prefixes that may indicate data entry errors or acquisitions
- **Packaging hierarchy analysis** — matches unit GTINs to case-level GTIN-14s, flags orphans
- **Retailer-specific checklists** — pass/fail checks for Walmart Item 360, Costco, UNFI, KeHE, Whole Foods, and 1WorldSync
- **Submission readiness score** — 0–100 score with letter grade, weighted by issue severity
- **Cost-of-inaction estimates** — chargebacks, delayed launches, manual rework hours at your SKU count
- **Before/after view** — shows what corrected GTINs would look like
- **Issue prioritization** — Critical (blocks submission), Warning (will cause problems), Info (best practice)
- **Branded PDF report** — professional report with your company name, formatted for handoff to your COO or broker
- **CSV export** — full detail for your own analysis
- **Sample data** — try it instantly with a realistic messy dataset from a fictional specialty food brand

### Who this is for

Operations managers, supply chain coordinators, and brokers at specialty food brands ($10M–$100M revenue) selling into national retail. If you've ever:

- Had a Walmart Item 360 submission rejected
- Received chargebacks for dimension/weight discrepancies
- Spent hours manually fixing product data for different retailer portals
- Wondered how bad your GTIN data actually is

This tool gives you a clear picture in 60 seconds.

---

## Run locally

Requires Python 3.10+ and Streamlit 1.53+.

```bash
# Clone the repo
git clone https://github.com/MsShawnP/gtin-validator.git
cd gtin-validator

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py

# Run tests
python -m pytest tests.py -v
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set the main file path to `app.py`
5. Deploy

---

## Project structure

```
gtin-validator/
├── app.py              # Streamlit UI
├── gtin_core.py        # Validation engine, scoring, retailer rules
├── csv_report.py       # CSV export
├── pdf_report.py       # Branded PDF report (reportlab)
├── sample_data.py      # Realistic sample data
├── tests.py            # pytest test suite
├── requirements.txt
├── pyproject.toml      # Project metadata
├── styles/
│   └── app.css         # Custom component CSS
├── .streamlit/
│   └── config.toml     # Theme configuration
└── README.md
```

## Technical notes

- **Check digit algorithm**: GS1 standard mod-10 per [GS1 General Specifications §7.9](https://www.gs1.org/standards/barcodes-epcrfid-id-keys/gs1-general-specifications)
- **GTIN-14 hierarchy detection**: Matches indicator digits 1–8 with corresponding unit GTINs by comparing the inner 12-digit item reference
- **Company prefix detection**: Approximate — uses first 7 digits as a grouping heuristic (actual GS1 prefix lengths vary 7–10 digits)
- **Cost estimates**: Based on published industry averages for specialty food/CPG. Directional, not predictive.
- **No data retention**: All validation happens in-session. No data is stored, logged, or transmitted beyond Streamlit's standard hosting.

## Standards referenced

- [GS1 General Specifications](https://www.gs1.org/standards/barcodes-epcrfid-id-keys/gs1-general-specifications)
- [GS1 US GTIN Allocation Rules](https://www.gs1us.org)
- [Walmart Item 360 Product Identifiers](https://itemmanager.helpdocs.io/article/6umpoiszgr-product-identifiers-new-catalog)
- [1WorldSync GDSN](https://1worldsync.com)

---

## License

MIT — see [LICENSE](LICENSE).

---

*Built as a portfolio piece demonstrating product data consulting for specialty food brands. For a comprehensive Product Data Health Audit for your brand, [get in touch](mailto:msshawnp@gmail.com).*
