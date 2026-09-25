import json
import re
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from PIL import Image, ImageOps

from prescription_service import run_prescription_ocr


RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"


def clean_ocr_text(text):
    """
    Clean OCR output before sending it to the drug lookup service.
    """

    if not text:
        return ""

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def query_rxnorm(name):
    """
    Search RxNorm using exact/normalized/approximate matching.
    """

    encoded_name = quote(
        name
    )

    url = (
        f"{RXNORM_BASE_URL}"
        f"/rxcui.json"
        f"?name={encoded_name}"
        f"&search=9"
    )

    request = Request(
        url,
        headers={
            "User-Agent": (
                "Healthcare-AI-Educational-Prototype/1.0"
            )
        }
    )

    try:

        with urlopen(
            request,
            timeout=15
        ) as response:

            return json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

    except (
        HTTPError,
        URLError,
        TimeoutError
    ) as error:

        return {
            "error": (
                type(error).__name__
                + ": "
                + str(error)
            )
        }


def get_rxnorm_name(rxcui):
    """
    Get the official RxNorm concept name.
    """

    url = (
        f"{RXNORM_BASE_URL}"
        f"/rxcui/{rxcui}.json"
    )

    request = Request(
        url,
        headers={
            "User-Agent": (
                "Healthcare-AI-Educational-Prototype/1.0"
            )
        }
    )

    try:

        with urlopen(
            request,
            timeout=15
        ) as response:

            data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        id_group = data.get(
            "idGroup",
            {}
        )

        return id_group.get(
            "name"
        )

    except (
        HTTPError,
        URLError,
        TimeoutError
    ):

        return None


def get_rxterms_info(rxcui):
    """
    Get additional RxTerms information.
    """

    url = (
        f"{RXNORM_BASE_URL}"
        f"/RxTerms/rxcui/{rxcui}/allinfo.json"
    )

    request = Request(
        url,
        headers={
            "User-Agent": (
                "Healthcare-AI-Educational-Prototype/1.0"
            )
        }
    )

    try:

        with urlopen(
            request,
            timeout=15
        ) as response:

            return json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

    except (
        HTTPError,
        URLError,
        TimeoutError
    ):

        return {}


def extract_candidates(data):
    """
    Extract approximate RxNorm candidates.
    """

    candidates = (
        data.get("approximateGroup", {})
        .get("candidate", [])
    )

    if isinstance(
        candidates,
        dict
    ):
        candidates = [
            candidates
        ]

    return candidates


def identify_medicine_from_text(
    ocr_text
):
    """
    Identify medicine candidates from OCR text.
    """

    cleaned_text = clean_ocr_text(
        ocr_text
    )

    if not cleaned_text:

        return {
            "status": "NOT_IDENTIFIED",
            "reason": (
                "No readable medicine text "
                "was extracted from the image."
            ),
            "ocr_text": ""
        }

    lookup = query_rxnorm(
        cleaned_text
    )

    if "error" in lookup:

        return {
            "status": "LOOKUP_FAILED",
            "ocr_text": cleaned_text,
            "error": lookup["error"]
        }

    candidates = extract_candidates(
        lookup
    )

    if not candidates:

        return {
            "status": "NOT_IDENTIFIED",
            "ocr_text": cleaned_text,
            "candidates": []
        }

    # Sort by RxNorm match score.
    candidates = sorted(
        candidates,
        key=lambda item: float(
            item.get("score", 0)
        ),
        reverse=True
    )

    best = candidates[0]

    rxcui = best.get(
        "rxcui"
    )

    rxnorm_name = (
        get_rxnorm_name(rxcui)
        if rxcui
        else None
    )

    rxterms = (
        get_rxterms_info(rxcui)
        if rxcui
        else {}
    )

    return {
        "status": "IDENTIFIED",
        "ocr_text": cleaned_text,
        "medicine": {
            "rxcui": rxcui,
            "name": (
                rxnorm_name
                or best.get("name")
            ),
            "match_score": float(
                best.get(
                    "score",
                    0
                )
            ),
            "source": best.get(
                "source"
            )
        },
        "rxterms": rxterms,
        "alternative_candidates": [
            {
                "rxcui": item.get(
                    "rxcui"
                ),
                "name": item.get(
                    "name"
                ),
                "score": float(
                    item.get(
                        "score",
                        0
                    )
                ),
                "source": item.get(
                    "source"
                )
            }
            for item in candidates[:5]
        ],
        "verification_required": True
    }


def analyze_medicine_photo(
    image_path
):
    """
    Complete medicine-photo workflow.

    1. Read image.
    2. OCR medicine label.
    3. Search RxNorm.
    4. Return structured medicine information.
    """

    try:

        image = Image.open(
            image_path
        )

        image = ImageOps.exif_transpose(
            image
        )

        image = image.convert(
            "RGB"
        )

    except Exception as error:

        return {
            "status": "IMAGE_ERROR",
            "error_type": type(
                error
            ).__name__,
            "error": str(error)
        }

    # The current OCR model is designed for
    # printed text, so readable packaging text
    # is important.
    ocr_text = run_prescription_ocr(
        image_path
    )

    result = identify_medicine_from_text(
        ocr_text
    )

    result["image"] = {
        "path": image_path,
        "width": image.width,
        "height": image.height
    }

    result["medical_safety_note"] = (
        "Medicine identification from an image "
        "can be uncertain. Verify the medicine name, "
        "strength, and packaging against the original "
        "label or a pharmacist/clinician before relying "
        "on the information. This feature provides "
        "informational drug data and does not prescribe "
        "or recommend a medicine."
    )

    return result


if __name__ == "__main__":

    print(
        "\n========== MEDICINE PHOTO ANALYZER ==========\n"
    )

    image_path = input(
        "Medicine photo path:\n> "
    )

    result = analyze_medicine_photo(
        image_path
    )

    print(
        "\n========== RESULT ==========\n"
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            default=str
        )
    )