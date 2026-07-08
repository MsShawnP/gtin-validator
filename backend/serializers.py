"""Convert gtin_core dataclass instances to Pydantic response models."""

from __future__ import annotations

from backend.schemas.responses import (
    BatchSummaryOut,
    BeforeAfterOut,
    CostEstimateOut,
    FixRoadmapItemOut,
    GTIN14IndicatorOut,
    GTIN14SuggestionOut,
    GTINResultOut,
    HierarchyOut,
    HierarchyPairOut,
    IssueOut,
    RetailerChecklistOut,
    RetailerCheckOut,
    ScoreResultOut,
)
from gtin_core import BatchResult, GTINResult, Issue


def serialize_issue(issue: Issue) -> IssueOut:
    return IssueOut(
        severity=issue.severity.value,
        code=issue.code,
        message=issue.message,
        recommendation=issue.recommendation,
        retailer_impact=issue.retailer_impact,
    )


def serialize_gtin_result(r: GTINResult) -> GTINResultOut:
    return GTINResultOut(
        raw_input=r.raw_input,
        cleaned=r.cleaned,
        row_number=r.row_number,
        is_valid=r.is_valid,
        gtin_type=r.gtin_type.value,
        issues=[serialize_issue(i) for i in r.issues],
        corrected_value=r.corrected_value,
        company_prefix=r.company_prefix,
        indicator_digit=r.indicator_digit,
        check_digit_expected=r.check_digit_expected,
        has_critical=r.has_critical,
        has_warning=r.has_warning,
    )


def serialize_hierarchy(hierarchy: dict) -> HierarchyOut:
    return HierarchyOut(
        matched_pairs=[
            HierarchyPairOut(**pair) for pair in hierarchy["matched_pairs"]
        ],
        orphan_cases=[
            serialize_gtin_result(r) for r in hierarchy["orphan_cases"]
        ],
        units_without_cases=[
            serialize_gtin_result(r) for r in hierarchy["units_without_cases"]
        ],
        has_hierarchy=hierarchy["has_hierarchy"],
        hierarchy_complete=hierarchy["hierarchy_complete"],
    )


def serialize_retailer_checklists(
    checklists: dict,
) -> dict[str, RetailerChecklistOut]:
    out = {}
    for name, checklist in checklists.items():
        profile = dict(checklist["profile"])
        profile.pop("required_gtin_types", None)
        if "requires_hierarchy" in profile:
            profile.pop("requires_hierarchy", None)
        if "requires_case_gtin" in profile:
            profile.pop("requires_case_gtin", None)

        out[name] = RetailerChecklistOut(
            profile=profile,
            checks=[
                RetailerCheckOut(
                    check=c["check"],
                    passed=c["passed"],
                    detail=c["detail"],
                    failing_gtins=[(row, gtin) for row, gtin in c["failing_gtins"]],
                )
                for c in checklist["checks"]
            ],
            passed=checklist["passed"],
            total=checklist["total"],
            ready=checklist["ready"],
        )
    return out


def serialize_cost_estimate(cost: dict) -> CostEstimateOut | None:
    if not cost:
        return None
    return CostEstimateOut(
        chargeback_range=tuple(cost["chargeback_range"]),
        delayed_launch_range=tuple(cost["delayed_launch_range"]),
        rework_hours=cost["rework_hours"],
        rework_cost=cost["rework_cost"],
        annual_estimate_low=cost["annual_estimate_low"],
        annual_estimate_high=cost["annual_estimate_high"],
        growth_note=cost["growth_note"],
        delayed_skus=cost["delayed_skus"],
        assumptions=cost["assumptions"],
        drivers=cost["drivers"],
    )


def serialize_fix_roadmap(roadmap: list[dict]) -> list[FixRoadmapItemOut]:
    return [FixRoadmapItemOut(**item) for item in roadmap]


def serialize_before_after(items: list[dict]) -> list[BeforeAfterOut]:
    return [BeforeAfterOut(**item) for item in items]


def serialize_gtin14_suggestions(
    suggestions: list[dict],
) -> list[GTIN14SuggestionOut]:
    return [
        GTIN14SuggestionOut(
            row=s["row"],
            unit_gtin=s["unit_gtin"],
            unit_type=s["unit_type"],
            indicators={
                ind: GTIN14IndicatorOut(**info)
                for ind, info in s["indicators"].items()
            },
        )
        for s in suggestions
    ]


def serialize_batch_result(
    data: BatchResult,
    *,
    executive_summary: str,
    fix_roadmap: list[dict],
    before_after: list[dict],
    gtin14_suggestions: list[dict],
    token: str,
) -> dict:
    """Serialize a full BatchResult + analysis into a JSON-safe dict."""
    return {
        "token": token,
        "results": [serialize_gtin_result(r) for r in data["results"]],
        "summary": BatchSummaryOut(**data["summary"]),
        "duplicates": data["duplicates"],
        "hierarchy": serialize_hierarchy(data["hierarchy"]),
        "retailer_checklists": serialize_retailer_checklists(
            data["retailer_checklists"]
        ),
        "score": ScoreResultOut(**data["score"]),
        "cost_estimate": serialize_cost_estimate(data["cost_estimate"]),
        "executive_summary": executive_summary,
        "fix_roadmap": serialize_fix_roadmap(fix_roadmap),
        "before_after": serialize_before_after(before_after),
        "gtin14_suggestions": serialize_gtin14_suggestions(gtin14_suggestions),
    }
