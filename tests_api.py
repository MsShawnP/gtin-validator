"""API endpoint tests for the FastAPI backend."""

import csv
from io import StringIO

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app

VALID_GTINS = ["614141000012", "614141000029", "614141000036"]
INVALID_GTIN = "614141000019"  # bad check digit


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class TestHealth:
    @pytest.mark.anyio
    async def test_health(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Sample data + retailers
# ---------------------------------------------------------------------------


class TestSampleAndRetailers:
    @pytest.mark.anyio
    async def test_sample_data(self, client):
        resp = await client.get("/api/sample")
        assert resp.status_code == 200
        data = resp.json()
        assert "csv" in data
        assert "description" in data
        assert "GTIN" in data["csv"]

    @pytest.mark.anyio
    async def test_retailers(self, client):
        resp = await client.get("/api/retailers")
        assert resp.status_code == 200
        data = resp.json()
        assert "Walmart" in data
        assert "description" in data["Walmart"]


# ---------------------------------------------------------------------------
# Validation — text input
# ---------------------------------------------------------------------------


class TestValidateText:
    @pytest.mark.anyio
    async def test_valid_gtins(self, client):
        resp = await client.post("/api/validate", json={"gtins": VALID_GTINS})
        assert resp.status_code == 200
        data = resp.json()
        assert data["token"]
        assert data["summary"]["total_gtins"] == 3
        assert data["score"]["score"] >= 0
        assert data["score"]["grade"] in ("A", "B", "C", "D", "F", "N/A")
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 3
        assert isinstance(data["executive_summary"], str)
        assert isinstance(data["fix_roadmap"], list)
        assert isinstance(data["before_after"], list)
        assert isinstance(data["gtin14_suggestions"], list)

    @pytest.mark.anyio
    async def test_invalid_gtin_flagged(self, client):
        resp = await client.post("/api/validate", json={"gtins": [INVALID_GTIN]})
        assert resp.status_code == 200
        data = resp.json()
        result = data["results"][0]
        assert result["has_critical"] or any(
            i["code"] == "BAD_CHECK_DIGIT" for i in result["issues"]
        )

    @pytest.mark.anyio
    async def test_empty_list_rejected(self, client):
        resp = await client.post("/api/validate", json={"gtins": []})
        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_retailer_checklists_present(self, client):
        resp = await client.post("/api/validate", json={"gtins": VALID_GTINS})
        data = resp.json()
        assert "Walmart" in data["retailer_checklists"]
        checklist = data["retailer_checklists"]["Walmart"]
        assert "checks" in checklist
        assert "ready" in checklist

    @pytest.mark.anyio
    async def test_hierarchy_structure(self, client):
        resp = await client.post("/api/validate", json={"gtins": VALID_GTINS})
        data = resp.json()
        h = data["hierarchy"]
        assert "matched_pairs" in h
        assert "orphan_cases" in h
        assert "units_without_cases" in h
        assert isinstance(h["has_hierarchy"], bool)

    @pytest.mark.anyio
    async def test_cost_estimate_structure(self, client):
        resp = await client.post(
            "/api/validate", json={"gtins": [INVALID_GTIN]}
        )
        data = resp.json()
        cost = data["cost_estimate"]
        assert cost is not None
        assert "chargeback_range" in cost
        assert "annual_estimate_low" in cost


# ---------------------------------------------------------------------------
# Validation — file upload
# ---------------------------------------------------------------------------


class TestValidateUpload:
    @pytest.mark.anyio
    async def test_csv_upload(self, client):
        csv_content = "GTIN,Product\n614141000012,Test Product\n614141000029,Another Product\n"
        files = {"file": ("test.csv", csv_content.encode(), "text/csv")}
        resp = await client.post("/api/validate/upload", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["total_gtins"] == 2

    @pytest.mark.anyio
    async def test_csv_upload_auto_detect_column(self, client):
        csv_content = "SKU,UPC Code,Name\n1,614141000012,Widget\n2,614141000029,Gadget\n"
        files = {"file": ("items.csv", csv_content.encode(), "text/csv")}
        resp = await client.post("/api/validate/upload", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["total_gtins"] == 2

    @pytest.mark.anyio
    async def test_unsupported_file_type(self, client):
        files = {"file": ("data.json", b'{"gtins":[]}', "application/json")}
        resp = await client.post("/api/validate/upload", files=files)
        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_column_override(self, client):
        csv_content = "ID,Barcode,Name\n1,614141000012,Widget\n2,614141000029,Gadget\n"
        files = {"file": ("items.csv", csv_content.encode(), "text/csv")}
        resp = await client.post(
            "/api/validate/upload", files=files, params={"gtin_column": "Barcode"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["total_gtins"] == 2


# ---------------------------------------------------------------------------
# Report downloads
# ---------------------------------------------------------------------------


class TestReports:
    @pytest.fixture
    async def token(self, client):
        resp = await client.post("/api/validate", json={"gtins": VALID_GTINS})
        return resp.json()["token"]

    @pytest.mark.anyio
    async def test_csv_report(self, client, token):
        resp = await client.get(f"/api/reports/csv/{token}")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/csv; charset=utf-8"
        reader = csv.reader(StringIO(resp.text))
        header = next(reader)
        assert "GTIN (Original)" in header

    @pytest.mark.anyio
    async def test_corrected_csv(self, client, token):
        resp = await client.get(f"/api/reports/corrected/{token}")
        assert resp.status_code == 200
        reader = csv.reader(StringIO(resp.text))
        header = next(reader)
        assert "Corrected GTIN" in header

    @pytest.mark.anyio
    async def test_pdf_report(self, client, token):
        resp = await client.get(f"/api/reports/pdf/{token}")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    @pytest.mark.anyio
    async def test_pdf_with_company_name(self, client, token):
        resp = await client.get(
            f"/api/reports/pdf/{token}", params={"company_name": "Acme Foods"}
        )
        assert resp.status_code == 200
        assert "Acme_Foods" in resp.headers.get("content-disposition", "")

    @pytest.mark.anyio
    async def test_expired_token(self, client):
        resp = await client.get("/api/reports/csv/nonexistent_token")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Data completeness
# ---------------------------------------------------------------------------


class TestCompleteness:
    @pytest.fixture
    async def token_with_data(self, client):
        csv_content = (
            "GTIN,Product Name,Brand,Weight\n"
            "614141000012,Marinara Sauce,Cedar Hollow,24oz\n"
            "614141000029,Pesto,Cedar Hollow,8oz\n"
        )
        files = {"file": ("products.csv", csv_content.encode(), "text/csv")}
        resp = await client.post("/api/validate/upload", files=files)
        return resp.json()["token"]

    @pytest.mark.anyio
    async def test_completeness(self, client, token_with_data):
        resp = await client.get(f"/api/completeness/{token_with_data}")
        assert resp.status_code == 200
        data = resp.json()
        assert "field_analysis" in data
        assert "missing_important_fields" in data
        assert "overall_completeness" in data

    @pytest.mark.anyio
    async def test_completeness_expired_token(self, client):
        resp = await client.get("/api/completeness/nonexistent")
        assert resp.status_code == 404
