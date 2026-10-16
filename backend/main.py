from __future__ import annotations

import json
import urllib.error
import urllib.request
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from rag import retrieve_schemes

APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "data" / "schemes.json"
FRONTEND_DIR = APP_DIR.parent / "frontend"

app = FastAPI(
    title="YojanaMitra API",
    description=(
        "Initial government scheme screening based on the "
        "profile and available scheme data."
    ),
    version="1.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserProfile(BaseModel):
    age: Optional[int] = None
    state: Optional[str] = None
    district: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[float] = None
    bpl_status: Optional[bool] = None
    category: Optional[str] = None
    land_owned: Optional[bool] = None
    land_area_acres: Optional[float] = None
    family_size: Optional[int] = None
    education: Optional[str] = None
    currently_enrolled_student: Optional[bool] = None
    disability_status: Optional[bool] = None
    marital_status: Optional[str] = None
    residence: Optional[str] = None
    income_tax_payer: Optional[bool] = None
    government_employee: Optional[bool] = None
    government_pensioner: Optional[bool] = None
    monthly_pension: Optional[float] = None
    professional_practice: Optional[bool] = None
    institutional_landholder: Optional[bool] = None
    self_employed: Optional[bool] = None
    actively_engaged_in_trade: Optional[bool] = None
    similar_loan_last_5_years: Optional[bool] = None
    previous_loan_fully_repaid: Optional[bool] = None
    previous_loan_scheme: Optional[str] = None
    family_member_registered: Optional[bool] = None
    family_member_in_government_service: Optional[bool] = None
    documents: List[str] = Field(default_factory=list)



class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    answer_language: str = Field(default="Hinglish", max_length=20)



def normalize(value: Any) -> str:
    """Normalize text while preserving Hindi and other Unicode letters."""
    if value is None:
        return ""

    text = str(value).strip().casefold()
    text = text.replace("&", " and ")
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def as_list(value: Any) -> List[Any]:
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]



def as_list(value: Any) -> List[Any]:
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def truthy_flag(value: Any) -> bool:
    return value is True or normalize(value) in {
        "true", "yes", "required", "1"
    }


NATIONWIDE_VALUES = {
    "",
    "all",
    "all india",
    "india",
    "pan india",
    "national",
    "nationwide",
    "central",
    "government of india",
    "government of india central scheme",
}


def is_nationwide(value: Any) -> bool:
    values = as_list(value)

    if not values:
        return True

    return any(
        normalize(item) in NATIONWIDE_VALUES
        for item in values
    )


OCCUPATION_ALIASES = {
    "carpenter suthar badhai": "carpenter",
    "carpenter suthar": "carpenter",
    "blacksmith lohar": "blacksmith",
    "goldsmith sonar sunar": "goldsmith",
    "potter kumhaar": "potter",
    "mason rajmistri": "mason",
    "washerman dhobi": "washerman",
    "tailor darzi": "tailor",
    "barber naai": "barber",
    "cobbler shoesmith footwear artisan": "cobbler",
    "leather based": "cobbler",
    "leather worker": "cobbler",
    "artisan craftsperson": "artisan",
    "self employed": "self employed",
}


def normalized_occupation(value: Any) -> str:
    raw = normalize(value)

    for alias, canonical in OCCUPATION_ALIASES.items():
        if raw == alias or raw.startswith(alias + " "):
            return canonical

    if (
        "cobbler" in raw
        or "shoesmith" in raw
        or "footwear artisan" in raw
    ):
        return "cobbler"

    return raw


def merge_ai_extractions(schemes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Use AI-extracted occupation candidates without overwriting existing rules.

    Extracted criteria are unverified and must not be treated as official rules.
    """
    ai_dir = DATA_FILE.parent / "ai_extracted"
    if not ai_dir.is_dir():
        return schemes

    for ai_file in sorted(ai_dir.glob("*_eligibility.json")):
        try:
            with ai_file.open("r", encoding="utf-8-sig") as file:
                extracted = json.load(file)
        except (OSError, json.JSONDecodeError):
            continue

        if not isinstance(extracted, dict):
            continue

        ai_name = normalize(str(extracted.get("scheme_name") or ""))
        if not ai_name:
            continue

        candidates = [
            scheme for scheme in schemes
            if normalize(str(scheme.get("name") or
                             scheme.get("scheme_name") or "")) == ai_name
        ]

        if not candidates and "vishwakarma" in ai_name:
            candidates = [
                scheme for scheme in schemes
                if "vishwakarma" in normalize(
                    str(scheme.get("name") or
                        scheme.get("scheme_name") or "")
                )
            ]

        if len(candidates) != 1:
            continue

        scheme = candidates[0]
        incoming = extracted.get("eligibility", {})
        if not isinstance(incoming, dict):
            continue

        eligibility = scheme.get("eligibility")
        if not isinstance(eligibility, dict):
            eligibility = {}

        existing = eligibility.get("occupation", [])
        if not isinstance(existing, list):
            existing = [existing] if existing else []

        additions = incoming.get("occupation", [])
        if not isinstance(additions, list):
            additions = [additions] if additions else []

        added_any = False
        for occupation in additions:
            if not isinstance(occupation, str) or not occupation.strip():
                continue
            if not any(
                normalize(occupation) == normalize(str(old))
                for old in existing
            ):
                existing.append(occupation.strip())
                added_any = True

        if added_any:
            eligibility["occupation"] = existing
            eligibility["verification_required"] = True
            eligibility["verification_note"] = (
                str(eligibility.get("verification_note") or "").strip()
                + " AI-extracted occupation candidates were added for "
                "preliminary matching and require official verification."
            ).strip()

            scheme["eligibility"] = eligibility
            scheme["verification_required"] = True
            scheme["verification_status"] = "needs_official_verification"
            scheme["ai_extraction_used"] = True

    return schemes


def load_schemes() -> List[Dict[str, Any]]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Scheme data file not found: {DATA_FILE}"
        )

    with DATA_FILE.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "schemes.json must contain a JSON array "
            "(a list of scheme objects)."
        )

    schemes = [
        item for item in data
        if isinstance(item, dict)
    ]
    return merge_ai_extractions(schemes)


def scheme_name(scheme: Dict[str, Any]) -> str:
    return str(
        scheme.get("scheme_name")
        or scheme.get("name")
        or scheme.get("title")
        or "Government Scheme"
    )


def scheme_url(scheme: Dict[str, Any]) -> str:
    return str(
        scheme.get("application_url")
        or scheme.get("official_source_url")
        or scheme.get("source_url")
        or scheme.get("url")
        or ""
    ).strip()


def valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return (
            parsed.scheme in {"https", "http"}
            and bool(parsed.netloc)
        )
    except Exception:
        return False


def criterion_values(
    eligibility: Dict[str, Any],
    *keys: str,
) -> List[Any]:
    for key in keys:
        if key in eligibility and eligibility[key] not in (
            None, "", []
        ):
            return as_list(eligibility[key])

    return []


def add_unknown_note(notes: List[str], text: str) -> None:
    if text not in notes:
        notes.append(text)


def evaluate_scheme(
    scheme: Dict[str, Any],
    user: UserProfile,
) -> Tuple[List[str], List[str]]:
    """
    Return (definite_mismatches, verification_notes).

    Missing user data is not treated as a contradiction.
    Explicit mismatches are.
    """
    reasons: List[str] = []
    notes: List[str] = []

    eligibility = scheme.get("eligibility")

    if not isinstance(eligibility, dict):
        eligibility = {}
        add_unknown_note(
            notes,
            "Structured eligibility criteria are not fully "
            "available in this record.",
        )

    # Geographic coverage: All India schemes must not be
    # rejected just because the applicant selected a state.
    scheme_state = scheme.get(
        "state",
        scheme.get("states", ""),
    )
    level = normalize(scheme.get("level", ""))

    if not is_nationwide(scheme_state):
        target_states = {
            normalize(item)
            for item in as_list(scheme_state)
            if normalize(item)
        }

        target_states.update(
            normalize(item)
            for item in as_list(
                scheme.get("eligible_states")
            )
            if normalize(item)
        )

        user_state = normalize(user.state)

        if (
            user_state
            and target_states
            and user_state not in target_states
        ):
            reasons.append(
                "This scheme is limited to a different "
                "state or region."
            )
        elif not user_state:
            add_unknown_note(
                notes,
                "Confirm the applicant's state against "
                "the scheme's state coverage.",
            )

    elif (
        level in {"state", "state scheme"}
        and normalize(scheme_state) in NATIONWIDE_VALUES
    ):
        add_unknown_note(
            notes,
            "Confirm the scheme's geographic coverage "
            "in its official guidelines.",
        )

    # Age
    minimum_age = eligibility.get(
        "min_age",
        eligibility.get("minimum_age"),
    )
    maximum_age = eligibility.get(
        "max_age",
        eligibility.get("maximum_age"),
    )

    if minimum_age is not None:
        if user.age is None:
            add_unknown_note(
                notes,
                "Confirm the applicant's age against "
                "the minimum age rule.",
            )
        elif user.age < float(minimum_age):
            reasons.append(
                f"Minimum age for this scheme is "
                f"{minimum_age} years."
            )

    if maximum_age is not None:
        if user.age is None:
            add_unknown_note(
                notes,
                "Confirm the applicant's age against "
                "the maximum age rule.",
            )
        elif user.age > float(maximum_age):
            reasons.append(
                f"Maximum age for this scheme is "
                f"{maximum_age} years."
            )

    # Gender
    expected_gender = criterion_values(
        eligibility,
        "gender",
        "eligible_gender",
    )

    if expected_gender:
        if not normalize(user.gender):
            add_unknown_note(
                notes,
                "Confirm the applicant's gender against "
                "the scheme criteria.",
            )
        elif normalize(user.gender) not in {
            normalize(value) for value in expected_gender
        }:
            reasons.append(
                "Gender does not match the listed criterion."
            )

    # Annual family income (rupees)
    max_income = eligibility.get(
        "max_annual_income",
        eligibility.get(
            "max_income",
            eligibility.get("income_limit"),
        ),
    )
    min_income = eligibility.get(
        "min_annual_income",
        eligibility.get("min_income"),
    )

    if max_income is not None:
        if user.annual_income is None:
            add_unknown_note(
                notes,
                "Confirm annual family income against "
                "the scheme's income ceiling.",
            )
        elif user.annual_income > float(max_income):
            reasons.append(
                f"Annual family income exceeds the listed "
                f"limit of \u20B9{float(max_income):,.0f}."

            )

    if min_income is not None:
        if user.annual_income is None:
            add_unknown_note(
                notes,
                "Confirm annual family income against "
                "the scheme's minimum income rule.",
            )
        elif user.annual_income < float(min_income):
            reasons.append(
                "Annual family income is below the listed "
                f"minimum of ₹{float(min_income):,.0f}."
            )

    # Shravan Bal: BPL status OR annual income below Rs. 21,000.
    if scheme.get("id") == "shravan-bal":
        if user.bpl_status is True:
            # BPL-listed applicants satisfy this alternative.
            pass

        elif (
            user.annual_income is not None
            and user.annual_income < 21000
        ):
            # Income alternative is satisfied.
            pass

        elif (
            user.bpl_status is False
            and user.annual_income is not None
            and user.annual_income >= 21000
        ):
            reasons.append(
                "Applicant must be on the BPL list or have "
                "annual income below \u20B921,000."
            )

        elif (
            user.bpl_status is False
            and user.annual_income is None
        ):
            add_unknown_note(
                notes,
                "Confirm annual income; applicant is not marked as BPL."
            )

        else:
            add_unknown_note(
                notes,
                "Confirm BPL-list status or annual income below Rs. 21,000."
            )


    # Social category
    expected_categories = criterion_values(
        eligibility,
        "categories",
        "category",
        "eligible_categories",
    )

    if expected_categories:
        user_category = normalize(user.category)
        normalized_expected = {
            normalize(value)
            for value in expected_categories
        }

        if not user_category:
            add_unknown_note(
                notes,
                "Confirm the applicant's social category "
                "against the scheme criteria.",
            )
        elif user_category not in normalized_expected:
            reasons.append(
                "Social category does not match the "
                "listed criterion."
            )

    # Occupation/trade
    expected_occupations = criterion_values(
        eligibility,
        "occupations",
        "occupation",
        "eligible_occupations",
        "trade",
        "trades",
    )

    if expected_occupations:
        user_occ = normalized_occupation(user.occupation)
        allowed = {
            normalized_occupation(value)
            for value in expected_occupations
        }

        if not user_occ:
            add_unknown_note(
                notes,
                "Confirm the applicant's occupation or trade "
                "against the official list.",
            )
        elif user_occ not in allowed:
            reasons.append(
                "Occupation or trade does not match the "
                "listed criterion."
            )

    # Residence
    expected_residences = criterion_values(
        eligibility,
        "residence",
        "residence_type",
        "eligible_residence",
    )

    if expected_residences:
        user_residence = normalize(user.residence)
        expected = {
            normalize(value)
            for value in expected_residences
        }

        aliases = {
            "rural": {"rural", "village", "rural area"},
            "urban": {"urban", "city", "urban area"},
        }

        expanded_expected = set(expected)

        for item in expected:
            expanded_expected.update(
                aliases.get(item, set())
            )

        expanded_user = aliases.get(
            user_residence,
            {user_residence},
        )

        if not user_residence:
            add_unknown_note(
                notes,
                "Confirm whether the applicant's residence "
                "is rural or urban.",
            )
        elif not (expanded_user & expanded_expected):
            reasons.append(
                "Residence type does not match the "
                "listed criterion."
            )

    # Land ownership and area
    expected_land_owned = eligibility.get("land_owned")

    if expected_land_owned is not None:
        if user.land_owned is None:
            add_unknown_note(
                notes,
                "Confirm land ownership against the "
                "scheme criteria.",
            )
        elif bool(user.land_owned) != truthy_flag(
            expected_land_owned
        ):
            reasons.append(
                "Land ownership does not match the "
                "listed criterion."
            )

    max_land = eligibility.get(
        "max_land_area_acres",
        eligibility.get(
            "max_land_acres",
            eligibility.get("land_area_max_acres"),
        ),
    )
    min_land = eligibility.get(
        "min_land_area_acres",
        eligibility.get(
            "min_land_acres",
            eligibility.get("land_area_min_acres"),
        ),
    )

    if max_land is not None:
        if user.land_area_acres is None:
            add_unknown_note(
                notes,
                "Confirm the applicant's land area against "
                "the scheme limit.",
            )
        elif user.land_area_acres > float(max_land):
            reasons.append(
                f"Land area exceeds the listed limit of "
                f"{max_land} acres."
            )

    if min_land is not None:
        if user.land_area_acres is None:
            add_unknown_note(
                notes,
                "Confirm the applicant's land area against "
                "the scheme minimum.",
            )
        elif user.land_area_acres < float(min_land):
            reasons.append(
                f"Land area is below the listed minimum of "
                f"{min_land} acres."
            )

    # Other explicitly encoded criteria
    simple_profile_fields = {
        "disability_status": user.disability_status,
        "marital_status": user.marital_status,
        "education": user.education,
        "currently_enrolled_student": user.currently_enrolled_student,
        "income_tax_payer": user.income_tax_payer,
        "government_employee": user.government_employee,
        "government_pensioner": user.government_pensioner,
        "professional_practice": user.professional_practice,
        "institutional_landholder": user.institutional_landholder,
        "self_employed": user.self_employed,
        "actively_engaged_in_trade": user.actively_engaged_in_trade,
        "similar_loan_last_5_years": user.similar_loan_last_5_years,
        "previous_loan_fully_repaid": user.previous_loan_fully_repaid,
        "family_member_registered": user.family_member_registered,
        "family_member_in_government_service": (
            user.family_member_in_government_service
        ),
    }

    for field_name, user_value in simple_profile_fields.items():
        if field_name not in eligibility:
            continue

        expected_value = eligibility[field_name]

        if user_value is None or user_value == "":
            add_unknown_note(
                notes,
                f"Confirm {field_name.replace('_', ' ')} "
                "against the scheme rules.",
            )
            continue

        if isinstance(expected_value, list):
            allowed_values = {
                normalize(value) for value in expected_value
            }

            if normalize(user_value) not in allowed_values:
                reasons.append(
                    f"{field_name.replace('_', ' ').capitalize()} "
                    "does not match the listed criterion."
                )

        elif isinstance(expected_value, bool):
            if bool(user_value) != expected_value:
                reasons.append(
                    f"{field_name.replace('_', ' ').capitalize()} "
                    "does not match the listed criterion."
                )

        elif normalize(user_value) != normalize(expected_value):
            reasons.append(
                f"{field_name.replace('_', ' ').capitalize()} "
                "does not match the listed criterion."
            )

    # Exclusions only apply when the JSON explicitly encodes them.
    exclusions = scheme.get(
        "exclusions",
        eligibility.get("exclusions", []),
    )

    for exclusion in as_list(exclusions):
        if not isinstance(exclusion, dict):
            continue

        field_name = exclusion.get("field")
        expected_value = exclusion.get("value", True)

        if field_name in simple_profile_fields:
            actual_value = simple_profile_fields[field_name]

            if (
                actual_value is not None
                and actual_value == expected_value
            ):
                reasons.append(
                    str(
                        exclusion.get("reason")
                        or (
                            "Applicant meets an exclusion condition: "
                            f"{field_name.replace('_', ' ')}."
                        )
                    )
                )

    # Verification flags affect the result status, not eligibility.
    verification_required = (
        truthy_flag(scheme.get("verification_required"))
        or truthy_flag(
            eligibility.get("verification_required")
        )
    )

    verification_status = normalize(
        scheme.get("verification_status")
    )

    officially_verified = verification_status in {
        "verified",
        "officially verified",
        "verified official rules",
    }

    if verification_required or not officially_verified:
        note = (
            eligibility.get("verification_note")
            or scheme.get("verification_note")
        )

        if note:
            add_unknown_note(notes, str(note))

        add_unknown_note(
            notes,
            "Eligibility has not been verified against current "
            "official rules. Treat this as a potential match, "
            "not a final eligibility decision.",
        )

    return (
        list(dict.fromkeys(reasons)),
        list(dict.fromkeys(notes)),
    )


def make_result(
    scheme: Dict[str, Any],
    notes: List[str],
    reasons: Optional[List[str]] = None,
) -> Dict[str, Any]:
    result = dict(scheme)

    result["scheme_name"] = scheme_name(scheme)

    result["description"] = (
        scheme.get("description")
        or "Scheme description is not available in this data record."
    )

    result["benefits"] = (
        scheme.get("benefits")
        or "Check the official scheme guidelines for applicable benefits."
    )

    result["level"] = scheme.get("level") or (
        "State"
        if not is_nationwide(scheme.get("state"))
        else "Central"
    )

    result["application_url"] = scheme_url(scheme)

    result["official_source_url"] = (
        scheme.get("official_source_url")
        or scheme_url(scheme)
    )

    result["verification_notes"] = notes
    result["missing_documents"] = []
    result["reasons"] = reasons or []

    status = normalize(scheme.get("verification_status"))

    explicitly_verified = status in {
        "verified",
        "officially verified",
        "verified official rules",
    }

    eligibility = scheme.get("eligibility")
    if not isinstance(eligibility, dict):
        eligibility = {}

    needs_verification = (
        truthy_flag(scheme.get("verification_required"))
        or truthy_flag(
            eligibility.get("verification_required")
        )
        or not explicitly_verified
    )

    result["eligibility_status"] = (
        "Needs verification"
        if needs_verification
        else "Potential match"
    )

    return result


@app.get("/")
def root():
    index_file = FRONTEND_DIR / "index.html"

    if index_file.exists():
        return FileResponse(index_file)

    return {
        "service": "YojanaMitra API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    try:
        schemes = load_schemes()

        return {
            "status": "healthy",
            "scheme_data_ready": True,
            "scheme_count": len(schemes),
        }

    except Exception as exc:
        return {
            "status": "degraded",
            "scheme_data_ready": False,
            "scheme_count": 0,
            "error": str(exc),
        }


@app.get("/schemes")
def get_schemes():
    try:
        schemes = load_schemes()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load schemes.json: {exc}",
        )

    return {
        "total": len(schemes),
        "schemes": schemes,
    }


@app.get("/audit")
def audit():
    try:
        schemes = load_schemes()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load schemes.json: {exc}",
        )

    ids = [
        str(scheme.get("id", "")).strip()
        for scheme in schemes
        if str(scheme.get("id", "")).strip()
    ]

    names_missing = [
        scheme_name(scheme)
        for scheme in schemes
        if not (
            scheme.get("name")
            or scheme.get("scheme_name")
            or scheme.get("title")
        )
    ]

    links_missing_or_invalid = [
        scheme_name(scheme)
        for scheme in schemes
        if not valid_http_url(scheme_url(scheme))
    ]

    duplicates = sorted({
        value for value in ids
        if ids.count(value) > 1
    })

    pending = [
        scheme_name(scheme)
        for scheme in schemes
        if (
            truthy_flag(scheme.get("verification_required"))
            or normalize(scheme.get("verification_status"))
            not in {
                "verified",
                "officially verified",
                "verified official rules",
            }
        )
    ]

    return {
        "total_schemes": len(schemes),
        "duplicate_ids": duplicates,
        "missing_names": names_missing,
        "missing_or_invalid_http_links": links_missing_or_invalid,
        "schemes_needing_official_rule_verification": pending,
        "note": (
            "A syntactically valid URL is not proof that a URL "
            "is official or that eligibility rules are verified."
        ),
    }


@app.post("/match")
def match_schemes(profile: UserProfile):
    try:
        schemes = load_schemes()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load scheme data: {exc}",
        )

    matched: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []


    for scheme in schemes:
        # Some programmes are not individual eligibility matches.
        if scheme.get("individual_matching_supported") is False:
            reason = str(
                scheme.get("matching_note")
                or "This programme needs a separate eligibility workflow."
            )

            result = make_result(scheme, [], [reason])
            result["eligibility_status"] = (
                "Not an individual eligibility match"
            )
            rejected.append(result)
            continue

        reasons, notes = evaluate_scheme(scheme, profile)

        if reasons:
            rejected.append(
                make_result(scheme, notes, reasons)
            )
        else:
            matched.append(
                make_result(scheme, notes)
            )


    return {
        "total_schemes_checked": len(schemes),
        "total_matches": len(matched),
        "total_rejected": len(rejected),
        "matched_schemes": matched,
        "rejected_schemes": rejected,
        "disclaimer": (
            "Potential matches are based only on the criteria "
            "encoded in this dataset. Records marked Needs "
            "verification have not been confirmed against current "
            "official rules. The relevant government department "
            "makes the final eligibility decision."
        ),
    }


if FRONTEND_DIR.exists():
    app.mount(
        "/frontend",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )
    ASSETS_DIR = FRONTEND_DIR / "assets"

if ASSETS_DIR.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(ASSETS_DIR)),
        name="assets",
    )

@app.post("/chat")
def chat_with_ai(payload: ChatRequest):
    message = payload.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    try:
        schemes = load_schemes()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load scheme data: {exc}"
        )

    # Prepare concise scheme records for AI grounding.
    records = []

    for scheme in schemes:
        record = {
            "name": scheme_name(scheme),
            "id": scheme.get("id", ""),
            "state": scheme.get("state", ""),
            "level": scheme.get("level", ""),
            "description": scheme.get("description", ""),
            "benefits": scheme.get("benefits", ""),
            "eligibility": scheme.get("eligibility", {}),
            "required_documents": scheme.get(
                "required_documents", []
            ),
            "verification_status": scheme.get(
                "verification_status", "needs_official_verification"
            ),
            "verification_required": scheme.get(
                "verification_required", True
            ),
            "official_source_url": scheme.get(
                "official_source_url", ""
            ) or scheme_url(scheme),
        }

        searchable = normalize(
            json.dumps(record, ensure_ascii=False)
        )
        records.append((record, searchable))

   
    # Retrieve relevant scheme records using SQLite FTS5.
    question_normalized = normalize(message)

    # Preserve the direct-name shortcut for explicitly named schemes.
    direct_name_matches = [
        record
        for record, searchable in records
        if (
            (
                normalize(record["name"])
                and normalize(record["name"]) in question_normalized
            )
            or (
                normalize(record["id"])
                and normalize(record["id"]) in question_normalized
            )
        )
    ]

    if direct_name_matches:
        selected = direct_name_matches[:3]
    else:
        retrieved = retrieve_schemes(message, schemes, limit=5)

        # Keep the ranking order returned by the retrieval function.
        records_by_id = {
            str(record.get("id") or ""): record
            for record, _searchable in records
        }

        selected = [
            records_by_id[str(item.get("id") or "")]
            for item in retrieved
            if str(item.get("id") or "") in records_by_id
        ][:5]


    # Deterministic direct-scheme responses in the selected language.
    if direct_name_matches:
        scheme = direct_name_matches[0]
        name = scheme_name(scheme)
        description = str(scheme.get("description") or "").strip()
        benefits = str(scheme.get("benefits") or "").strip()
        documents = scheme.get("required_documents") or []

        if not isinstance(documents, list):
            documents = [str(documents)]

        eligibility_data = scheme.get("eligibility") or {}
        verification_note = str(
            eligibility_data.get("verification_note") or ""
        ).strip()
        verification_status = str(
            scheme.get(
                "verification_status",
                "needs_official_verification"
            )
        )
        official_url = str(
            scheme.get("official_source_url") or scheme_url(scheme) or ""
        ).strip()

        if answer_language == "hindi":
            parts = [
                f"**{name}**",
                "\u092f\u0939 \u091c\u093e\u0928\u0915\u093e\u0930\u0940 SchemeSathi \u0915\u0947 \u092e\u094c\u091c\u0942\u0926\u093e \u0921\u0947\u091f\u093e \u0930\u093f\u0915\u0949\u0930\u094d\u0921 \u092a\u0930 \u0906\u0927\u093e\u0930\u093f\u0924 \u0939\u0948\u0964"
            ]
            if description:
                parts.append(
                    f"**\u092f\u094b\u091c\u0928\u093e \u0915\u093e \u0935\u093f\u0935\u0930\u0923 (record \u092e\u0947\u0902 \u0926\u0930\u094d\u091c):** {description}"
                )
            if benefits:
                parts.append(
                    f"**\u0932\u093e\u092d (record \u092e\u0947\u0902 \u0926\u0930\u094d\u091c):** {benefits}"
                )
            if documents:
                parts.append(
                    "**\u0921\u0947\u091f\u093e\u0938\u0947\u091f \u092e\u0947\u0902 \u0938\u0942\u091a\u0940\u092c\u0926\u094d\u0927 \u0926\u0938\u094d\u0924\u093e\u0935\u0947\u091c\u093c:**\n"
                    + "\n".join(f"- {document}" for document in documents)
                )
            if verification_note:
                parts.append(
                    f"**\u0905\u0924\u093f\u0930\u093f\u0915\u094d\u0924 \u091c\u093e\u0901\u091a:** {verification_note}"
                )
            parts.append(
                "\u0906\u0935\u0947\u0926\u0928 \u0915\u0930\u0928\u0947 \u0938\u0947 \u092a\u0939\u0932\u0947 \u0906\u0927\u093f\u0915\u093e\u0930\u093f\u0915 \u0938\u0930\u0915\u093e\u0930\u0940 \u0928\u093f\u092f\u092e\u094b\u0902 \u0915\u0940 \u092a\u0941\u0937\u094d\u091f\u093f \u0915\u0930\u0947\u0902\u0964"
            )
        elif answer_language == "hinglish":
            parts = [
                f"**{name}**",
                "Yeh information SchemeSathi ke current dataset record se li gayi hai."
            ]
            if description:
                parts.append(f"**Description (record mein listed):** {description}")
            if benefits:
                parts.append(f"**Benefits (record mein listed):** {benefits}")
            if documents:
                parts.append(
                    "**Documents (dataset mein listed):**\n"
                    + "\n".join(f"- {document}" for document in documents)
                )
            if verification_note:
                parts.append(f"**Extra verification:** {verification_note}")
            parts.append(
                "Apply karne se pehle current official government rules verify karein."
            )
        else:
            parts = [f"**{name}**"]
            if description:
                parts.append(f"**Description:** {description}")
            if benefits:
                parts.append(f"**Listed benefits:** {benefits}")
            if documents:
                parts.append(
                    "**Documents listed in the dataset:**\n"
                    + "\n".join(f"- {document}" for document in documents)
                )
            if verification_note:
                parts.append(f"**Additional verification:** {verification_note}")
            parts.append("Verify current official rules before applying.")

        answer = "\n\n".join(parts)
        scheme_references = []

        if valid_http_url(official_url):
            scheme_references.append({
                "name": name,
                "url": official_url,
                "verification_status": verification_status,
            })

        return {
            "answer": answer,
            "scheme_references": scheme_references,
            "disclaimer": (
                "Stored scheme information may be incomplete or outdated. "
                "The relevant government authority decides final eligibility."
            ),
        }

    context = json.dumps(selected, ensure_ascii=False)

    answer_language = payload.answer_language.strip().casefold()

    if answer_language not in {"english", "hindi", "hinglish"}:
       answer_language = "hinglish"

    prompt = f"""
You are YojanaMitra, a helpful Indian government scheme assistant.

Selected response language: {answer_language}

Follow the selected language regardless of the language of the user's question.
- English: Reply in clear, simple English.
- Hindi: Reply in natural, grammatically correct Hindi written in Devanagari.
- Hinglish: Reply in natural Hindi-English mix written in Roman script.

Keep official scheme names such as PM-KISAN unchanged.

Selected language instructions:
- English: Answer in clear, natural English.
- Hindi: Answer in natural, grammatically correct Hindi using Devanagari.
- Hinglish: Answer in natural Hindi-English mix using Roman script.
- Follow the selected response language, not the language of the question.
- Keep official scheme names, acronyms and URLs unchanged.

Do not invent facts, eligibility rules, or documents. Only describe
information supported by the supplied scheme records. Clearly state
when official verification is still pending. Never present a potential
match as confirmed eligibility.


Use only the scheme records provided below for scheme-specific facts.
Do not invent eligibility conditions, income limits, benefits,
deadlines, documents, application status, or website links.

Important rules:
- A potential match is not confirmed eligibility.
- Respect each record's verification_status and
  verification_required fields.
- If official verification is pending, clearly say so.
- If the records do not answer the question, admit that the
  available data is insufficient.
- Do not claim that you checked live government websites.
- Use an official URL only when it is present in the records.
- The relevant government authority makes the final decision.

SCHEME RECORDS:
{context}

USER QUESTION:
{message}

Follow the selected language strictly: {answer_language}.
English means English; Hindi means Devanagari Hindi; Hinglish means
Roman-script Hindi-English mix. Answer clearly in 2-5 sentences.
Use only supported scheme facts and disclose when verification is pending.
"""

    language_system = {
        "english": (
            "OUTPUT LANGUAGE: ENGLISH. Write the complete answer "
            "in clear, natural English. Do not switch to Hindi. "
            "Example: A scholarship helps students pay for education."
        ),
        "hindi": (
            "OUTPUT LANGUAGE: HINDI. Write natural, grammatically "
            "correct Hindi using Devanagari script. Avoid awkward "
            "literal translations. Do not write the answer in English "
            "or Roman-script Hindi. Example: ??????????? ??????? ?? "
            "????? ?? ???? ??? ?????? ???? ???"
        ),
        "hinglish": (
            "OUTPUT LANGUAGE: HINGLISH IN ROMAN SCRIPT. Use natural "
            "Hindi sentence structure with common English words. "
            "Do not answer entirely in English. Never use Devanagari. "
            "Example: Scholarship students ko padhai ke kharch mein "
            "help karti hai."
        ),
    }[answer_language]

    request_body = json.dumps({
        "model": "qwen3:1.7b",
        "system": language_system,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 300
        }
    }).encode("utf-8")

    request_obj = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request_obj, timeout=90
        ) as response:
            ai_result = json.loads(
                response.read().decode("utf-8")
            )

    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="AI took too long to respond. Please try again."
        )

    except urllib.error.URLError:
        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable. Please start Ollama and retry."
        )

    except (json.JSONDecodeError, KeyError):
        raise HTTPException(
            status_code=502,
            detail="Could not read the AI response."
        )

    answer = str(ai_result.get("response", "")).strip()

    if not answer:
        raise HTTPException(
            status_code=502,
            detail="The AI returned an empty response."
        )

    source_links = [
        {
            "name": record["name"],
            "url": record["official_source_url"],
            "verification_status": record["verification_status"],
        }
        for record in selected
        if valid_http_url(record["official_source_url"])
    ]

    return {
        "answer": answer,
        "scheme_references": source_links,
        "disclaimer": (
            "AI-generated guidance only. Scheme information may "
            "require official verification. Final eligibility is "
            "decided by the relevant government department."
        ),
    }
