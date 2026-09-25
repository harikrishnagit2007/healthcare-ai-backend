"""
medicine_knowledge_service.py

Medicine information layer for the Healthcare AI project.

Flow:
    Medicine name
        ↓
    RxNorm search
        ↓
    Product-level RxCUI
        ↓
    RxTerms
        ↓
    DailyMed
        ↓
    Structured medicine knowledge

Safety:
    - Information only
    - No diagnosis
    - No prescription
    - No automatic dose changes
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any


RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"

DAILYMED_BASE_URL = (
    "https://dailymed.nlm.nih.gov/dailymed/services/v2"
)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get_json(
    url: str,
    timeout: int = 15,
) -> dict[str, Any]:

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "HealthcareAI/1.0",
        },
        method="GET",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:

            body = (
                response
                .read()
                .decode("utf-8")
            )

    except urllib.error.HTTPError as exc:

        try:
            detail = (
                exc.read()
                .decode("utf-8")
            )
        except Exception:
            detail = ""

        raise RuntimeError(
            f"HTTP {exc.code}: {detail}"
        ) from exc

    except urllib.error.URLError as exc:

        raise RuntimeError(
            f"Connection failed: {exc.reason}"
        ) from exc

    except TimeoutError as exc:

        raise RuntimeError(
            "Request timed out."
        ) from exc

    try:
        data = json.loads(body)

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            "External API returned invalid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError(
            "Unexpected JSON structure."
        )

    return data


def _get_text(
    url: str,
    timeout: int = 15,
) -> str:

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/xml,text/xml,*/*",
            "User-Agent": "HealthcareAI/1.0",
        },
        method="GET",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:

            return (
                response
                .read()
                .decode("utf-8")
            )

    except urllib.error.HTTPError as exc:

        raise RuntimeError(
            f"HTTP {exc.code}: DailyMed request failed."
        ) from exc

    except urllib.error.URLError as exc:

        raise RuntimeError(
            f"DailyMed connection failed: {exc.reason}"
        ) from exc

    except TimeoutError as exc:

        raise RuntimeError(
            "DailyMed request timed out."
        ) from exc


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def _clean_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    text = str(value)

    text = text.replace(
        "\r",
        " ",
    )

    text = text.replace(
        "\n",
        " ",
    )

    return " ".join(
        text.split()
    ).strip()


def _now_utc() -> str:
    """
    Timezone-aware UTC timestamp.
    """

    return (
        datetime
        .now(timezone.utc)
        .isoformat()
    )


# ---------------------------------------------------------------------------
# RxNorm name search
# ---------------------------------------------------------------------------

def search_rxnorm(
    medicine_name: str,
) -> dict[str, Any]:

    medicine_name = _clean_text(
        medicine_name
    )

    if not medicine_name:

        raise ValueError(
            "Medicine name cannot be empty."
        )

    encoded = urllib.parse.quote(
        medicine_name,
        safe="",
    )

    # Exact or normalized search.
    url = (
        f"{RXNORM_BASE_URL}/rxcui.json"
        f"?name={encoded}"
        f"&search=2"
    )

    data = _get_json(
        url
    )

    id_group = (
        data.get("idGroup")
        or {}
    )

    rxcuis = (
        id_group.get("rxnormId")
        or []
    )

    if isinstance(
        rxcuis,
        str,
    ):
        rxcuis = [rxcuis]

    if rxcuis:

        return {
            "match_type": "exact_or_normalized",
            "input": medicine_name,
            "rxcuis": [
                str(value)
                for value in rxcuis
            ],
        }

    # Approximate fallback.
    approximate_url = (
        f"{RXNORM_BASE_URL}/approximateTerm.json"
        f"?term={encoded}"
        f"&maxEntries=10"
        f"&option=1"
    )

    approximate_data = _get_json(
        approximate_url
    )

    group = (
        approximate_data.get(
            "approximateGroup"
        )
        or {}
    )

    candidates = (
        group.get(
            "candidate"
        )
        or []
    )

    if not isinstance(
        candidates,
        list,
    ):
        candidates = []

    results = []

    for candidate in candidates:

        if not isinstance(
            candidate,
            dict,
        ):
            continue

        results.append(
            {
                "rxcui": candidate.get(
                    "rxcui"
                ),
                "name": candidate.get(
                    "name"
                ),
                "score": candidate.get(
                    "score"
                ),
                "rank": candidate.get(
                    "rank"
                ),
                "source": candidate.get(
                    "source"
                ),
            }
        )

    return {
        "match_type": "approximate",
        "input": medicine_name,
        "rxcuis": [
            str(item["rxcui"])
            for item in results
            if item.get("rxcui")
        ],
        "candidates": results,
    }


# ---------------------------------------------------------------------------
# RxNorm properties
# ---------------------------------------------------------------------------

def get_rxnorm_properties(
    rxcui: str,
) -> dict[str, Any]:

    rxcui = str(
        rxcui
    ).strip()

    url = (
        f"{RXNORM_BASE_URL}/rxcui/"
        f"{urllib.parse.quote(rxcui)}"
        f"/properties.json"
    )

    data = _get_json(
        url
    )

    properties = (
        data.get(
            "properties"
        )
        or {}
    )

    return {
        "rxcui": properties.get(
            "rxcui",
            rxcui,
        ),
        "name": properties.get(
            "name"
        ),
        "synonym": properties.get(
            "synonym"
        ),
        "tty": properties.get(
            "tty"
        ),
        "language": properties.get(
            "language"
        ),
        "suppress": properties.get(
            "suppress"
        ),
    }


# ---------------------------------------------------------------------------
# Find product-level RxCUI
# ---------------------------------------------------------------------------

def get_product_candidates(
    medicine_name: str,
) -> list[dict[str, Any]]:
    """
    Get product-level concepts for an ingredient/brand/name.

    RxNorm getDrugs can return SCD/SBD/GPCK/BPCK products.
    """

    medicine_name = _clean_text(
        medicine_name
    )

    encoded = urllib.parse.quote(
        medicine_name,
        safe="",
    )

    url = (
        f"{RXNORM_BASE_URL}/drugs.json"
        f"?name={encoded}"
        f"&expand=psn"
    )

    data = _get_json(
        url
    )

    group = (
        data.get(
            "drugGroup"
        )
        or {}
    )

    concept_groups = (
        group.get(
            "conceptGroup"
        )
        or []
    )

    if not isinstance(
        concept_groups,
        list,
    ):
        return []

    candidates = []

    for concept_group in concept_groups:

        if not isinstance(
            concept_group,
            dict,
        ):
            continue

        tty = concept_group.get(
            "tty"
        )

        properties = (
            concept_group.get(
                "conceptProperties"
            )
            or []
        )

        if not isinstance(
            properties,
            list,
        ):
            continue

        for item in properties:

            if not isinstance(
                item,
                dict,
            ):
                continue

            candidates.append(
                {
                    "rxcui": item.get(
                        "rxcui"
                    ),
                    "name": item.get(
                        "name"
                    ),
                    "synonym": item.get(
                        "synonym"
                    ),
                    "tty": item.get(
                        "tty"
                    ) or tty,
                    "psn": item.get(
                        "psn"
                    ),
                }
            )

    return [
        item
        for item in candidates
        if item.get("rxcui")
    ]


def choose_product_candidate(
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Prefer a clinical drug (SCD), then branded drug (SBD),
    then packs.
    """

    priority = {
        "SCD": 0,
        "SBD": 1,
        "GPCK": 2,
        "BPCK": 3,
    }

    usable = [
        item
        for item in candidates
        if item.get("rxcui")
    ]

    if not usable:
        return None

    usable.sort(
        key=lambda item: (
            priority.get(
                str(
                    item.get("tty")
                    or ""
                ),
                99,
            ),
            str(
                item.get("name")
                or ""
            ),
        )
    )

    return usable[0]


# ---------------------------------------------------------------------------
# RxTerms
# ---------------------------------------------------------------------------

def get_rxterms_info(
    rxcui: str,
) -> dict[str, Any]:

    rxcui = str(
        rxcui
    ).strip()

    url = (
        f"{RXNORM_BASE_URL}"
        f"/RxTerms/rxcui/"
        f"{urllib.parse.quote(rxcui)}"
        "/allinfo.json"
    )

    data = _get_json(
        url
    )

    properties = (
        data.get(
            "rxtermsProperties"
        )
        or {}
    )

    return {
        "brand_name": properties.get(
            "brandName"
        ),
        "display_name": properties.get(
            "displayName"
        ),
        "synonym": properties.get(
            "synonym"
        ),
        "full_name": properties.get(
            "fullName"
        ),
        "full_generic_name": properties.get(
            "fullGenericName"
        ),
        "strength": properties.get(
            "strength"
        ),
        "dose_form": properties.get(
            "rxtermsDoseForm"
        ),
        "route": properties.get(
            "route"
        ),
        "term_type": properties.get(
            "termType"
        ),
        "rxcui": properties.get(
            "rxcui",
            rxcui,
        ),
        "generic_rxcui": properties.get(
            "genericRxcui"
        ),
        "rxnorm_dose_form": properties.get(
            "rxnormDoseForm"
        ),
    }


# ---------------------------------------------------------------------------
# DailyMed
# ---------------------------------------------------------------------------

def find_dailymed_labels(
    rxcui: str,
    page_size: int = 10,
) -> list[dict[str, Any]]:

    encoded = urllib.parse.quote(
        str(rxcui).strip(),
        safe="",
    )

    url = (
        f"{DAILYMED_BASE_URL}/spls.json"
        f"?rxcui={encoded}"
        f"&pagesize={page_size}"
        f"&page=1"
    )

    data = _get_json(
        url
    )

    items = (
        data.get("data")
        or []
    )

    if not isinstance(
        items,
        list,
    ):
        return []

    labels = []

    for item in items:

        if not isinstance(
            item,
            dict,
        ):
            continue

        labels.append(
            {
                "setid": (
                    item.get("setid")
                    or item.get("SETID")
                ),
                "title": (
                    item.get("title")
                    or item.get("TITLE")
                ),
                "published_date": (
                    item.get(
                        "published_date"
                    )
                    or item.get(
                        "PUBLISHED_DATE"
                    )
                ),
                "spl_version": (
                    item.get(
                        "spl_version"
                    )
                    or item.get(
                        "SPL_VERSION"
                    )
                ),
            }
        )

    return [
        item
        for item in labels
        if item.get("setid")
    ]


def _local_name(
    tag: str,
) -> str:

    if "}" in tag:
        return tag.rsplit(
            "}",
            1,
        )[-1]

    return tag


def _all_element_text(
    element: ET.Element,
) -> str:

    values = []

    for item in element.itertext():

        text = _clean_text(
            item
        )

        if text:
            values.append(
                text
            )

    return " ".join(
        values
    )


def get_dailymed_label(
    setid: str,
) -> dict[str, Any]:

    setid = str(
        setid
    ).strip()

    url = (
        f"{DAILYMED_BASE_URL}/spls/"
        f"{urllib.parse.quote(setid)}.xml"
    )

    xml_text = _get_text(
        url
    )

    try:

        root = ET.fromstring(
            xml_text
        )

    except ET.ParseError as exc:

        raise RuntimeError(
            "DailyMed XML could not be parsed."
        ) from exc

    target_sections = {
        "indications and usage",
        "contraindications",
        "warnings and precautions",
        "warnings",
        "adverse reactions",
        "drug interactions",
        "description",
        "pregnancy",
        "lactation",
        "pediatric use",
        "geriatric use",
        "overdosage",
    }

    sections = {}

    for element in root.iter():

        if _local_name(
            element.tag
        ) != "section":
            continue

        title = ""

        for child in element:

            if _local_name(
                child.tag
            ) == "title":

                title = _all_element_text(
                    child
                )

                break

        title = _clean_text(
            title
        )

        normalized_title = (
            title.lower()
        )

        if normalized_title not in target_sections:
            continue

        full_text = _all_element_text(
            element
        )

        if title and full_text.startswith(
            title
        ):

            full_text = (
                full_text[len(title):]
                .strip()
            )

        if full_text:

            sections[
                normalized_title
            ] = full_text

    return {
        "setid": setid,
        "source_url": url,
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# Complete medicine knowledge
# ---------------------------------------------------------------------------

def get_medicine_knowledge(
    medicine_name: str,
) -> dict[str, Any]:

    medicine_name = _clean_text(
        medicine_name
    )

    if not medicine_name:

        raise ValueError(
            "Medicine name cannot be empty."
        )

    # -------------------------------------------------------
    # Step 1: Search name
    # -------------------------------------------------------

    search_result = search_rxnorm(
        medicine_name
    )

    initial_rxcuis = (
        search_result.get(
            "rxcuis"
        )
        or []
    )

    if not initial_rxcuis:

        return {
            "status": "not_found",
            "input_medicine": medicine_name,
            "message": (
                "No RxNorm medicine match found."
            ),
            "generated_at": _now_utc(),
        }

    # -------------------------------------------------------
    # Step 2: Resolve product-level concept
    # -------------------------------------------------------

    product_candidates = (
        get_product_candidates(
            medicine_name
        )
    )

    selected_product = (
        choose_product_candidate(
            product_candidates
        )
    )

    # Fallback to initial concept if no product exists.
    if selected_product:

        selected_rxcui = str(
            selected_product[
                "rxcui"
            ]
        )

        selected_tty = (
            selected_product.get(
                "tty"
            )
        )

    else:

        selected_rxcui = str(
            initial_rxcuis[0]
        )

        selected_tty = None

    # -------------------------------------------------------
    # Step 3: RxNorm properties
    # -------------------------------------------------------

    rxnorm = get_rxnorm_properties(
        selected_rxcui
    )

    # -------------------------------------------------------
    # Step 4: RxTerms
    # -------------------------------------------------------

    try:

        rxterms = get_rxterms_info(
            selected_rxcui
        )

    except Exception as exc:

        rxterms = {
            "error": str(exc),
            "rxcui": selected_rxcui,
        }

    # -------------------------------------------------------
    # Step 5: DailyMed
    # -------------------------------------------------------

    try:

        labels = find_dailymed_labels(
            selected_rxcui
        )

    except Exception as exc:

        labels = []

        daily_error = str(exc)

    else:

        daily_error = None

    selected_label = (
        labels[0]
        if labels
        else None
    )

    dailymed_details = None

    if selected_label:

        try:

            dailymed_details = (
                get_dailymed_label(
                    selected_label[
                        "setid"
                    ]
                )
            )

        except Exception as exc:

            dailymed_details = {
                "error": str(exc)
            }

    dailymed = {
        "labels": labels,
        "selected_label": selected_label,
        "selected_label_details": (
            dailymed_details
        ),
        "error": daily_error,
    }

    # -------------------------------------------------------
    # Verification rule
    # -------------------------------------------------------

    verification_required = (
        selected_tty not in {
            "SCD",
            "SBD",
        }
        or not rxterms.get(
            "full_name"
        )
    )

    # -------------------------------------------------------
    # Final result
    # -------------------------------------------------------

    return {
        "status": "success",

        "input_medicine": medicine_name,

        "identity": {
            "medicine_name": (
                rxterms.get(
                    "display_name"
                )
                or rxnorm.get(
                    "name"
                )
                or medicine_name
            ),
            "rxcui": selected_rxcui,
            "tty": selected_tty
                or rxnorm.get("tty"),
            "match_type": (
                search_result.get(
                    "match_type"
                )
            ),
            "verification_required": (
                verification_required
            ),
        },

        "rxnorm": rxnorm,

        "rxterms": rxterms,

        "product_candidates": (
            product_candidates[:10]
        ),

        "dailymed": dailymed,

        "sources": {
            "rxnorm": (
                "https://rxnav.nlm.nih.gov/"
            ),
            "dailymed": (
                "https://dailymed.nlm.nih.gov/"
            ),
        },

        "generated_at": _now_utc(),

        "safety_note": (
            "This information is for medicine "
            "education and reference. It does "
            "not diagnose a condition, prescribe "
            "treatment, or determine a personal "
            "dose."
        ),
    }


# ---------------------------------------------------------------------------
# Frontend summary
# ---------------------------------------------------------------------------

def format_medicine_summary(
    knowledge: dict[str, Any],
) -> dict[str, Any]:

    if knowledge.get(
        "status"
    ) != "success":

        return {
            "status": knowledge.get(
                "status"
            ),
            "message": knowledge.get(
                "message"
            ),
        }

    rxterms = (
        knowledge.get(
            "rxterms"
        )
        or {}
    )

    identity = (
        knowledge.get(
            "identity"
        )
        or {}
    )

    dailymed = (
        knowledge.get(
            "dailymed"
        )
        or {}
    )

    label_details = (
        dailymed.get(
            "selected_label_details"
        )
        or {}
    )

    sections = (
        label_details.get(
            "sections"
        )
        or {}
    )

    return {
        "medicine_name": (
            identity.get(
                "medicine_name"
            )
        ),

        "generic_name": (
            rxterms.get(
                "full_generic_name"
            )
        ),

        "brand_name": (
            rxterms.get(
                "brand_name"
            )
        ),

        "strength": (
            rxterms.get(
                "strength"
            )
        ),

        "dose_form": (
            rxterms.get(
                "dose_form"
            )
        ),

        "route": (
            rxterms.get(
                "route"
            )
        ),

        "rxcui": identity.get(
            "rxcui"
        ),

        "term_type": identity.get(
            "tty"
        ),

        "verification_required": (
            identity.get(
                "verification_required"
            )
        ),

        "uses_and_indications": (
            sections.get(
                "indications and usage"
            )
        ),

        "warnings": (
            sections.get(
                "warnings and precautions"
            )
            or sections.get(
                "warnings"
            )
        ),

        "contraindications": (
            sections.get(
                "contraindications"
            )
        ),

        "adverse_reactions": (
            sections.get(
                "adverse reactions"
            )
        ),

        "drug_interactions": (
            sections.get(
                "drug interactions"
            )
        ),

        "pregnancy": (
            sections.get(
                "pregnancy"
            )
        ),

        "lactation": (
            sections.get(
                "lactation"
            )
        ),

        "source": (
            label_details.get(
                "source_url"
            )
        ),
    }


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 72)
    print("MEDICINE KNOWLEDGE SERVICE TEST")
    print("=" * 72)

    medicine = input(
        "\nEnter medicine name: "
    ).strip()

    if not medicine:
        medicine = "paracetamol"

    print(
        f"\nTesting: {medicine}"
    )

    try:

        result = get_medicine_knowledge(
            medicine
        )

        print()
        print(
            "STRUCTURED RESULT:"
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )

        print()
        print(
            "FRONTEND SUMMARY:"
        )

        print(
            json.dumps(
                format_medicine_summary(
                    result
                ),
                indent=2,
                ensure_ascii=False,
            )
        )

    except Exception as exc:

        print()
        print("ERROR:")
        print(str(exc))

    print()
    print("=" * 72)
    print("TEST COMPLETED")
    print("=" * 72)