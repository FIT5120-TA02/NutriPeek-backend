"""Service for fetching popular farmers markets via Google Places API."""

from typing import List, Optional

import httpx

from src.app.core.config import settings
from src.app.schemas.farmers_market import (
    NearbyFarmersMarketListResponse,
    NearbyFarmersMarketResponse,
)

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = (
    "places.id,"
    "places.displayName,"
    "places.formattedAddress,"
    "places.location,"
    "places.rating,"
    "places.userRatingCount,"
    "places.regularOpeningHours,"
    "places.websiteUri,"
    "places.nationalPhoneNumber"
)


class GooglePlacesService:
    """Service for fetching popular farmers markets from Google Places API."""

    async def get_nearby_popular_markets(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 50.0,
        min_rating: float = 4.0,
        max_results: int = 20,
    ) -> NearbyFarmersMarketListResponse:
        """Search for popular farmers markets near a location.

        Args:
            latitude: User latitude
            longitude: User longitude
            radius_km: Search radius in kilometres (default 50km)
            min_rating: Minimum Google rating to include (default 4.0)
            max_results: Maximum number of results to return

        Returns:
            NearbyFarmersMarketListResponse with popular markets nearby
        """
        if not settings.GOOGLE_PLACES_API_KEY:
            return NearbyFarmersMarketListResponse(items=[], total=0)

        payload = {
            "textQuery": "farmers market",
            "locationBias": {
                "circle": {
                    "center": {"latitude": latitude, "longitude": longitude},
                    "radius": radius_km * 1000,
                }
            },
            "minRating": min_rating,
            "maxResultCount": max_results,
            "languageCode": "en",
        }

        headers = {
            "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
            "X-Goog-FieldMask": FIELD_MASK,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                PLACES_TEXT_SEARCH_URL, json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()

        places = data.get("places", [])
        items: List[NearbyFarmersMarketResponse] = []

        for place in places:
            location = place.get("location", {})
            opening_hours = place.get("regularOpeningHours", {})
            weekday_descriptions: Optional[List[str]] = opening_hours.get(
                "weekdayDescriptions"
            )

            items.append(
                NearbyFarmersMarketResponse(
                    place_id=place.get("id", ""),
                    name=place.get("displayName", {}).get("text", ""),
                    address=place.get("formattedAddress"),
                    latitude=location.get("latitude", 0.0),
                    longitude=location.get("longitude", 0.0),
                    rating=place.get("rating"),
                    user_rating_count=place.get("userRatingCount"),
                    opening_hours=weekday_descriptions,
                    website=place.get("websiteUri"),
                    phone=place.get("nationalPhoneNumber"),
                )
            )

        return NearbyFarmersMarketListResponse(items=items, total=len(items))


google_places_service = GooglePlacesService()
