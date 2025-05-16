#!/usr/bin/env python
"""
Script to clean up seasonal_food table by removing duplicate entries.

This script ensures that only one entry exists for each unique combination of
food_name, region, season, and month in the seasonal_food table.
"""

import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.db.async_session import get_async_session
from src.app.models.seasonal_food import SeasonalFood

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def get_all_seasonal_foods(session: AsyncSession) -> List[SeasonalFood]:
    """
    Retrieve all seasonal food entries from the database.

    Args:
        session: Database session

    Returns:
        List of all SeasonalFood objects
    """
    query = select(SeasonalFood)
    result = await session.execute(query)
    return result.scalars().all()


async def group_by_unique_combination(
    seasonal_foods: List[SeasonalFood],
) -> Dict[Tuple[str, str, str, str], List[SeasonalFood]]:
    """
    Group seasonal foods by unique combination of food_name, region, season, and month.

    Args:
        seasonal_foods: List of SeasonalFood objects

    Returns:
        Dictionary mapping unique combinations to lists of matching SeasonalFood objects
    """
    grouped_foods = defaultdict(list)

    for food in seasonal_foods:
        # Create a key from the unique combination
        key = (food.food_name, food.region, food.season, food.month)
        grouped_foods[key].append(food)

    return grouped_foods


async def clean_duplicates(session: AsyncSession) -> Tuple[int, int]:
    """
    Remove duplicate seasonal food entries, keeping one entry per unique combination.

    Args:
        session: Database session

    Returns:
        Tuple of (number of combinations processed, number of duplicates removed)
    """
    # Get all seasonal food entries
    all_foods = await get_all_seasonal_foods(session)
    logger.info(f"Found {len(all_foods)} total seasonal food entries")

    # Group by unique combination
    grouped_foods = await group_by_unique_combination(all_foods)
    logger.info(f"Found {len(grouped_foods)} unique combinations")

    # Count duplicates and remove them
    duplicates_removed = 0
    for key, foods in grouped_foods.items():
        # If there are duplicates for this combination
        if len(foods) > 1:
            # Keep the first item, remove the rest
            for food_to_remove in foods[1:]:
                # Delete the duplicate
                await session.delete(food_to_remove)
                duplicates_removed += 1

                # Log the removal
                food_name, region, season, month = key
                logger.info(
                    f"Removed duplicate: {food_name}, {region}, {season}, {month} (ID: {food_to_remove.id})"
                )

    # Commit the changes if any duplicates were removed
    if duplicates_removed > 0:
        await session.commit()

    return len(grouped_foods), duplicates_removed


async def main():
    """Main function to execute the script."""
    logger.info("Starting seasonal food duplicate cleanup script")

    async with get_async_session() as session:
        try:
            unique_combinations, duplicates_removed = await clean_duplicates(session)

            logger.info(
                f"Cleanup completed: {unique_combinations} unique combinations found, "
                f"{duplicates_removed} duplicates removed"
            )

            if duplicates_removed == 0:
                logger.info("No duplicates found. Database is already clean.")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
