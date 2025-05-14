#!/usr/bin/env python
"""Script to update latitude and longitude values for farmers markets.

This script queries the farmers_market table for records with null coordinates,
geocodes their addresses using Google's Geocoding API, and updates the database
with the obtained latitude and longitude values.

Example usage:
    python -m scripts.python.google_lat_lang_finder

Dependencies:
    - requests
    - sqlalchemy
    - asyncio
"""

import asyncio
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from src.app.core.db.async_session import get_async_session  # noqa: E402
from src.app.core.logger import get_logger  # noqa: E402
from src.app.models.farmers_market import FarmersMarket  # noqa: E402

# Configure logger
logger = get_logger(__name__)

# Google Maps API key
GOOGLE_API_KEY = "AIzaSyAKXEJLNKo8owMxWqt3DaZa8uafSPj-5SE"

# Rate limiting constants
GEOCODING_DELAY = 0.5  # seconds between API calls to avoid rate limiting


def geocode_address(
    address: str, region: Optional[str] = None
) -> Tuple[Optional[float], Optional[float]]:
    """
    Get latitude and longitude coordinates for an address using Google Geocoding API.

    Args:
        address: String containing the address to geocode
        region: Optional region to improve geocoding accuracy

    Returns:
        Tuple of (latitude, longitude) if successful, or (None, None) if geocoding failed
    """
    if not address:
        logger.warning("Empty address provided")
        return None, None

    # Create a complete query with region if provided
    query = address
    if region:
        query = f"{address}, {region}"

    encoded_address = urllib.parse.quote(query)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={GOOGLE_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses

        data = response.json()

        # Check if the request was successful
        if data["status"] == "OK" and data["results"]:
            # Google's response structure
            location = data["results"][0]["geometry"]["location"]
            lat = location["lat"]
            lng = location["lng"]
            formatted_address = data["results"][0]["formatted_address"]
            logger.info(f"Successfully geocoded: {address} → {formatted_address}")
            return lat, lng
        else:
            logger.warning(
                f"Geocoding failed for '{address}' with status: {data['status']}"
            )
            if "error_message" in data:
                logger.error(f"Error message: {data['error_message']}")
            return None, None
    except Exception as e:
        logger.error(f"Error geocoding address '{address}': {e}")
        return None, None


async def get_markets_without_coordinates(session: AsyncSession) -> List[Dict]:
    """
    Query the database for farmers markets with null coordinates.

    Args:
        session: Async database session

    Returns:
        List of dictionaries containing market data
    """
    query = select(
        FarmersMarket.id,
        FarmersMarket.name,
        FarmersMarket.address,
        FarmersMarket.region,
    ).where((FarmersMarket.latitude.is_(None)) | (FarmersMarket.longitude.is_(None)))

    result = await session.execute(query)
    markets = result.all()

    return [
        {
            "id": market.id,
            "name": market.name,
            "address": market.address,
            "region": market.region,
        }
        for market in markets
    ]


async def update_market_coordinates(
    session: AsyncSession, market_id: str, latitude: float, longitude: float
) -> bool:
    """
    Update the latitude and longitude values for a farmers market.

    Args:
        session: Async database session
        market_id: UUID of the farmers market to update
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        True if update was successful, False otherwise
    """
    try:
        query = (
            update(FarmersMarket)
            .where(FarmersMarket.id == market_id)
            .values(latitude=latitude, longitude=longitude)
        )

        await session.execute(query)
        return True
    except Exception as e:
        logger.error(f"Error updating coordinates for market {market_id}: {e}")
        return False


async def update_all_coordinates():
    """Main function to update coordinates for all markets missing them."""
    # Get database session
    async with get_async_session() as session:
        try:
            # Get markets without coordinates
            markets = await get_markets_without_coordinates(session)
            logger.info(f"Found {len(markets)} markets without coordinates")

            if not markets:
                logger.info("No markets need coordinate updates")
                return

            # Process each market
            updated_count = 0
            failed_count = 0

            for idx, market in enumerate(markets, 1):
                market_id = market["id"]
                address = market["address"]
                region = market["region"]
                name = market["name"]

                logger.info(f"Processing ({idx}/{len(markets)}): {name}")

                # Geocode the address
                lat, lng = geocode_address(address, region)

                if lat is not None and lng is not None:
                    # Update database
                    success = await update_market_coordinates(
                        session, market_id, lat, lng
                    )

                    if success:
                        updated_count += 1
                        logger.info(f"Updated coordinates for {name}: ({lat}, {lng})")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to update database for {name}")
                else:
                    failed_count += 1
                    logger.warning(f"Couldn't get coordinates for {name}")

                # Commit after each update
                await session.commit()

                # Rate limiting
                if idx < len(markets):
                    time.sleep(GEOCODING_DELAY)

            # Log summary
            logger.info(
                f"Geocoding complete. Updated {updated_count} markets, failed {failed_count}."
            )
            success_rate = updated_count / len(markets) * 100 if markets else 0
            logger.info(f"Success rate: {success_rate:.1f}%")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating coordinates: {e}")


if __name__ == "__main__":
    # Run the async update function
    asyncio.run(update_all_coordinates())
