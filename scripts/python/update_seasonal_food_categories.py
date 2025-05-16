#!/usr/bin/env python
"""Async script to update db_category field in the seasonal_food table.

This script reads data from the Seasonal_Food_to_Category_Mapping.csv file and updates
the db_category column in the seasonal_food table based on the mapping.

Example usage:
    python -m scripts.python.update_seasonal_food_categories

Dependencies:
    - pandas
    - sqlalchemy
    - asyncpg
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.app.core.config import settings  # noqa: E402
from src.app.core.db.async_session import get_async_session  # noqa: E402
from src.app.core.logger import get_logger  # noqa: E402
from src.app.models.seasonal_food import SeasonalFood  # noqa: E402

# Configure logger
logger = get_logger(__name__)


def read_csv_file(file_path: str) -> Optional[pd.DataFrame]:
    """Read data from a CSV file.

    Args:
        file_path: Path to the CSV file.

    Returns:
        A pandas DataFrame containing the CSV data or None if reading failed.
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Successfully read data from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {e}")
        return None


def transform_mapping_data(df: pd.DataFrame) -> Dict[str, str]:
    """Transform the CSV data into a mapping dictionary.

    Args:
        df: The pandas DataFrame containing the data.

    Returns:
        A dictionary mapping food_name to db_category.
    """
    # Log all columns in the CSV file
    logger.info(f"Columns in CSV file: {list(df.columns)}")

    # Verify required columns exist
    required_columns = ["food_name", "mapped_food_category"]
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Required column '{col}' not found in CSV file")
            return {}

    # Convert all food names to lowercase for case-insensitive matching
    df["food_name"] = df["food_name"].str.lower()

    # Create a dictionary mapping food_name to mapped_food_category
    mapping = dict(zip(df["food_name"], df["mapped_food_category"]))
    logger.info(f"Created mapping dictionary with {len(mapping)} entries")

    return mapping


async def fetch_seasonal_foods(session: AsyncSession) -> List[Tuple[str, str]]:
    """Fetch all food_name and id pairs from the seasonal_food table.

    Args:
        session: The database session.

    Returns:
        A list of tuples containing (id, food_name) pairs.
    """
    try:
        # Query all rows from the seasonal_food table
        result = await session.execute(select(SeasonalFood.id, SeasonalFood.food_name))
        food_items = result.all()

        logger.info(f"Fetched {len(food_items)} food items from the database")
        return food_items
    except Exception as e:
        logger.error(f"Error fetching food items from database: {e}")
        return []


async def update_db_categories(mapping: Dict[str, str], batch_size: int = 100) -> int:
    """Update db_category column in the seasonal_food table.

    Args:
        mapping: Dictionary mapping food_name to db_category.
        batch_size: Number of rows to update in each batch.

    Returns:
        Number of rows updated.
    """
    updated_count = 0

    try:
        # Get async session using context manager
        async with get_async_session() as session:
            try:
                # Fetch all food items
                food_items = await fetch_seasonal_foods(session)

                # Create batches for processing
                batches = [
                    food_items[i : i + batch_size]
                    for i in range(0, len(food_items), batch_size)
                ]
                logger.info(
                    f"Split {len(food_items)} food items into {len(batches)} batches"
                )

                # Process each batch
                for batch_index, batch in enumerate(batches):
                    batch_updated = 0
                    logger.info(
                        f"Processing batch {batch_index + 1} of {len(batches)} ({len(batch)} items)"
                    )

                    for food_id, food_name in batch:
                        # Convert food_name to lowercase for case-insensitive matching
                        food_name_lower = food_name.lower()

                        # Look up corresponding db_category
                        if food_name_lower in mapping:
                            db_category = mapping[food_name_lower]

                            # Update the row
                            await session.execute(
                                update(SeasonalFood)
                                .where(SeasonalFood.id == food_id)
                                .values(db_category=db_category)
                            )

                            batch_updated += 1
                        else:
                            # Use the food_name as db_category if no mapping exists
                            logger.warning(
                                f"No mapping found for '{food_name}', using food_name as db_category"
                            )
                            await session.execute(
                                update(SeasonalFood)
                                .where(SeasonalFood.id == food_id)
                                .values(db_category=food_name)
                            )

                            batch_updated += 1

                    # Commit the batch
                    await session.commit()
                    updated_count += batch_updated
                    logger.info(
                        f"Batch {batch_index + 1} completed, updated {batch_updated} items"
                    )

                logger.info(f"Total updated rows: {updated_count}")
                return updated_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating db_categories: {e}")
                return updated_count
    except Exception as e:
        logger.error(f"Error getting database session: {e}")
        return updated_count


async def main(
    csv_path: Optional[str] = None,
    database_url: Optional[str] = None,
    batch_size: int = 100,
):
    """Main function to run the script.

    Args:
        csv_path: Path to the CSV file. Defaults to a predefined path.
        database_url: URL for the database connection. Defaults to settings.SQLALCHEMY_DATABASE_URI.
        batch_size: Number of rows to update in each batch. Defaults to 100.
    """
    # Configure database URL if provided
    if database_url:
        settings.SQLALCHEMY_DATABASE_URI = database_url
        logger.info(f"Using custom database URL: {database_url}")

    # Determine CSV file path
    if not csv_path:
        # Construct the default path relative to the project root
        csv_path = os.path.join(project_root, "Seasonal_Food_to_Category_Mapping.csv")
        logger.info(f"Using default CSV file path: {csv_path}")

    # Read and transform data
    df = read_csv_file(csv_path)
    if df is None:
        logger.error("Failed to read CSV file. Exiting.")
        return

    mapping = transform_mapping_data(df)
    if not mapping:
        logger.error("Failed to create mapping. Exiting.")
        return

    # Update db_category in database
    updated_count = await update_db_categories(mapping, batch_size)
    logger.info(f"Script completed. Updated {updated_count} records.")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Update db_category field in seasonal_food table from CSV mapping"
    )
    parser.add_argument("--csv", help="Path to the CSV mapping file", default=None)
    parser.add_argument("--database", help="Database URL", default=None)
    parser.add_argument(
        "--batch-size", help="Batch size for database updates", type=int, default=100
    )
    args = parser.parse_args()

    # Run the async main function
    asyncio.run(main(args.csv, args.database, args.batch_size))
