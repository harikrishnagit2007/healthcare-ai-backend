"""
care_location_service.py

Purpose:
    Find nearby hospitals and pharmacies using Google Places API.

Important:
    - API key stays in the backend environment.
    - The service returns factual place information.
    - It does not decide which hospital is "best".
    - It does not diagnose any medical condition.
"""

from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request
from typing import Any


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GOOGLE_PLACES_URL = (
    "https://places.googleapis.com/v1/places:searchNearby"
)

GOOGLE_MAPS_API_KEY_ENV = "AIzaSyCCy_7mbiTgRWHaas_DSAc-2eHmwoNCqqY"


# Explicit fields requested from Google Places.
FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.nationalPhoneNumber",
        "places.regularOpeningHours",
        "places.businessStatus",
        "places.primaryType",
        "places.types",
        "places.googleMapsUri",
    ]
)


# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    """
    Read Google Maps API key from environment.
    """

    api_key = os.getenv(
        GOOGLE_MAPS_API_KEY_ENV,
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "GOOGLE_MAPS_API_KEY is not set. "
            "Set the API key in the backend environment "
            "before calling the care-location service."
        )

    return api_key


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_coordinates(
    latitude: float,
    longitude: float,
) -> tuple[float, float]:
    """
    Validate latitude and longitude.
    """

    try:
        lat = float(latitude)
        lon = float(longitude)

    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Latitude and longitude must be valid numbers."
        ) from exc

    if not -90 <= lat <= 90:
        raise ValueError(
            "Latitude must be between -90 and 90."
        )

    if not -180 <= lon <= 180:
        raise ValueError(
            "Longitude must be between -180 and 180."
        )

    return lat, lon


def _validate_radius(
    radius_meters: float,
) -> float:
    """
    Validate search radius.
    """

    try:
        radius = float(radius_meters)

    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Radius must be a valid number."
        ) from exc

    if radius <= 0:
        raise ValueError(
            "Radius must be greater than 0."
        )

    if radius > 50000:
        raise ValueError(
            "Radius cannot be greater than 50,000 meters."
        )

    return radius


def _validate_max_results(
    max_results: int,
) -> int:
    """
    Validate number of results.
    """

    try:
        count = int(max_results)

    except (TypeError, ValueError) as exc:
        raise ValueError(
            "max_results must be a valid integer."
        ) from exc

    if count < 1:
        raise ValueError(
            "max_results must be at least 1."
        )

    if count > 20:
        raise ValueError(
            "max_results cannot be greater than 20."
        )

    return count


# ---------------------------------------------------------------------------
# Distance calculation
# ---------------------------------------------------------------------------

def _haversine_distance_km(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """
    Calculate distance between two geographic coordinates.

    Returns:
        Distance in kilometres.
    """

    earth_radius_km = 6371.0088

    lat1 = math.radians(latitude_1)
    lon1 = math.radians(longitude_1)

    lat2 = math.radians(latitude_2)
    lon2 = math.radians(longitude_2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )

    return earth_radius_km * c


# ---------------------------------------------------------------------------
# Google response helpers
# ---------------------------------------------------------------------------

def _extract_display_name(
    place: dict[str, Any],
) -> str:
    """
    Extract place display name safely.
    """

    display_name = place.get("displayName")

    if isinstance(display_name, dict):
        return str(
            display_name.get("text") or ""
        ).strip()

    return ""


def _extract_open_now(
    place: dict[str, Any],
) -> bool | None:
    """
    Extract current opening status.

    Returns:
        True  = currently open
        False = currently closed
        None  = information unavailable
    """

    regular_hours = place.get(
        "regularOpeningHours"
    )

    if not isinstance(
        regular_hours,
        dict,
    ):
        return None

    open_now = regular_hours.get(
        "openNow"
    )

    if isinstance(open_now, bool):
        return open_now

    return None


def _normalize_place(
    place: dict[str, Any],
    user_latitude: float,
    user_longitude: float,
) -> dict[str, Any]:
    """
    Convert Google's place object into our application format.
    """

    location = place.get("location") or {}

    place_latitude = location.get(
        "latitude"
    )

    place_longitude = location.get(
        "longitude"
    )

    distance_km = None

    if (
        isinstance(
            place_latitude,
            (int, float),
        )
        and isinstance(
            place_longitude,
            (int, float),
        )
    ):
        distance_km = round(
            _haversine_distance_km(
                user_latitude,
                user_longitude,
                float(place_latitude),
                float(place_longitude),
            ),
            2,
        )

    return {
        "place_id": place.get("id"),

        "name": _extract_display_name(
            place
        ),

        "address": place.get(
            "formattedAddress"
        ),

        "latitude": place_latitude,

        "longitude": place_longitude,

        "distance_km": distance_km,

        "phone": place.get(
            "nationalPhoneNumber"
        ),

        "open_now": _extract_open_now(
            place
        ),

        "business_status": place.get(
            "businessStatus"
        ),

        "primary_type": place.get(
            "primaryType"
        ),

        "types": place.get(
            "types"
        ) or [],

        "google_maps_url": place.get(
            "googleMapsUri"
        ),
    }


# ---------------------------------------------------------------------------
# Google Places search
# ---------------------------------------------------------------------------

def _search_nearby(
    latitude: float,
    longitude: float,
    included_types: list[str],
    radius_meters: float = 5000,
    max_results: int = 10,
    language_code: str = "en",
    region_code: str = "IN",
) -> list[dict[str, Any]]:
    """
    Search nearby places using Google Places API.
    """

    lat, lon = _validate_coordinates(
        latitude,
        longitude,
    )

    radius = _validate_radius(
        radius_meters
    )

    count = _validate_max_results(
        max_results
    )

    if not included_types:
        raise ValueError(
            "included_types cannot be empty."
        )

    api_key = _get_api_key()

    payload = {
        "includedTypes": included_types,

        "maxResultCount": count,

        "rankPreference": "DISTANCE",

        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lon,
                },
                "radius": radius,
            }
        },

        "languageCode": language_code,

        "regionCode": region_code,
    }

    request_body = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        GOOGLE_PLACES_URL,
        data=request_body,

        headers={
            "Content-Type": (
                "application/json"
            ),

            "X-Goog-Api-Key": api_key,

            "X-Goog-FieldMask": FIELD_MASK,
        },

        method="POST",
    )

    # -------------------------------------------------------
    # API request
    # -------------------------------------------------------

    try:
        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:

            response_body = (
                response
                .read()
                .decode("utf-8")
            )

    except urllib.error.HTTPError as exc:

        try:
            error_body = (
                exc.read()
                .decode("utf-8")
            )

        except Exception:
            error_body = ""

        raise RuntimeError(
            "Google Places API request failed "
            f"(HTTP {exc.code}): "
            f"{error_body}"
        ) from exc

    except urllib.error.URLError as exc:

        raise RuntimeError(
            "Could not connect to Google Places API: "
            f"{exc.reason}"
        ) from exc

    except TimeoutError as exc:

        raise RuntimeError(
            "Google Places API request timed out."
        ) from exc

    # -------------------------------------------------------
    # Parse JSON
    # -------------------------------------------------------

    try:
        data = json.loads(
            response_body
        )

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            "Google Places API returned "
            "invalid JSON."
        ) from exc

    raw_places = data.get(
        "places"
    ) or []

    if not isinstance(
        raw_places,
        list,
    ):
        return []

    places: list[
        dict[str, Any]
    ] = []

    for place in raw_places:

        if not isinstance(
            place,
            dict,
        ):
            continue

        normalized = _normalize_place(
            place=place,
            user_latitude=lat,
            user_longitude=lon,
        )

        places.append(
            normalized
        )

    # Sort by our calculated distance.
    places.sort(
        key=lambda item: (
            float("inf")
            if item.get(
                "distance_km"
            ) is None
            else item["distance_km"]
        )
    )

    return places


# ---------------------------------------------------------------------------
# Hospital search
# ---------------------------------------------------------------------------

def find_nearby_hospitals(
    latitude: float,
    longitude: float,
    radius_meters: float = 5000,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """
    Find nearby hospitals.
    """

    return _search_nearby(
        latitude=latitude,
        longitude=longitude,

        included_types=[
            "hospital"
        ],

        radius_meters=radius_meters,

        max_results=max_results,
    )


# ---------------------------------------------------------------------------
# Pharmacy search
# ---------------------------------------------------------------------------

def find_nearby_pharmacies(
    latitude: float,
    longitude: float,
    radius_meters: float = 5000,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """
    Find nearby pharmacies.
    """

    return _search_nearby(
        latitude=latitude,
        longitude=longitude,

        included_types=[
            "pharmacy"
        ],

        radius_meters=radius_meters,

        max_results=max_results,
    )


# ---------------------------------------------------------------------------
# Combined care search
# ---------------------------------------------------------------------------

def find_nearby_care(
    latitude: float,
    longitude: float,
    confirmed_symptoms: list[str] | None = None,
    radius_meters: float = 5000,
    max_results: int = 10,
) -> dict[str, Any]:
    """
    Find nearby hospitals and pharmacies.

    confirmed_symptoms is included so the agent can pass
    confirmed information into the service.

    Currently this function DOES NOT use symptoms to diagnose
    a condition or rank a facility.
    """

    lat, lon = _validate_coordinates(
        latitude,
        longitude,
    )

    radius = _validate_radius(
        radius_meters
    )

    count = _validate_max_results(
        max_results
    )

    hospitals = find_nearby_hospitals(
        latitude=lat,
        longitude=lon,
        radius_meters=radius,
        max_results=count,
    )

    pharmacies = find_nearby_pharmacies(
        latitude=lat,
        longitude=lon,
        radius_meters=radius,
        max_results=count,
    )

    return {
        "confirmed_symptoms": (
            confirmed_symptoms or []
        ),

        "search_center": {
            "latitude": lat,
            "longitude": lon,
        },

        "radius_meters": radius,

        "hospitals": hospitals,

        "pharmacies": pharmacies,
    }


# ---------------------------------------------------------------------------
# Local test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "=" * 72
    )

    print(
        "CARE LOCATION SERVICE TEST"
    )

    print(
        "=" * 72
    )

    print()
    print(
        "Required environment variable:"
    )

    print(
        "GOOGLE_MAPS_API_KEY"
    )

    print()
    print(
        "Testing configuration..."
    )

    api_key = os.getenv(
        GOOGLE_MAPS_API_KEY_ENV
    )

    if not api_key:

        print()
        print(
            "API test skipped."
        )

        print(
            "GOOGLE_MAPS_API_KEY is not configured."
        )

    else:

        # Example coordinates.
        # Replace later with browser-provided location.
        test_latitude = 12.9716
        test_longitude = 77.5946

        print()
        print(
            "Searching nearby care..."
        )

        try:

            result = find_nearby_care(
                latitude=test_latitude,
                longitude=test_longitude,
                confirmed_symptoms=[
                    "dizziness"
                ],
                radius_meters=5000,
                max_results=5,
            )

            print()
            print(
                "RESULT:"
            )

            print(
                json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False,
                )
            )

        except Exception as exc:

            print()
            print(
                "ERROR:"
            )

            print(
                str(exc)
            )

    print()
    print(
        "=" * 72
    )

    print(
        "TEST COMPLETED"
    )

    print(
        "=" * 72
    )