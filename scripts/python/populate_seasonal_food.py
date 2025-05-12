#!/usr/bin/env python
"""Async script to populate seasonal_food table from XLSX file.

This script reads data from the seasonal_food_different_region.xlsx file and inserts
it into the seasonal_food table in the database using async operations.

Example usage:
    python -m scripts.python.populate_seasonal_food

Dependencies:
    - pandas
    - sqlalchemy
    - openpyxl
    - asyncpg
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.app.core.config import settings  # noqa: E402
from src.app.core.db.async_session import get_async_session  # noqa: E402
from src.app.core.logger import get_logger  # noqa: E402
from src.app.models.seasonal_food import SeasonalFood  # noqa: E402

# Configure logger
logger = get_logger(__name__)


def read_excel_file(file_path: str) -> Optional[pd.DataFrame]:
    """Read data from an Excel file.

    Args:
        file_path: Path to the Excel file.

    Returns:
        A pandas DataFrame containing the Excel data or None if reading failed.
    """
    try:
        df = pd.read_excel(file_path)
        logger.info(f"Successfully read data from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error reading Excel file {file_path}: {e}")
        return None


def transform_data(df: pd.DataFrame) -> List[Dict]:
    """Transform the Excel data into a format suitable for database insertion.

    Args:
        df: The pandas DataFrame containing the data.

    Returns:
        A list of dictionaries representing rows for the seasonal_food table.
    """
    # Log all columns in the Excel file
    logger.info(f"Columns in Excel file: {list(df.columns)}")

    # Drop the 'Sources' column if it exists
    if "Sources" in df.columns:
        df = df.drop(columns=["Sources"])
        logger.info("Dropped 'Sources' column from DataFrame")

    # Define the column mapping for the seasonal_food table
    column_mapping = {
        "Food name": "food_name",
        "Category": "category",
        "Region": "region",
        "Season": "season",
        "Month": "month",
    }

    # Verify required columns exist
    for excel_col in column_mapping.keys():
        if excel_col not in df.columns:
            logger.error(f"Required column '{excel_col}' not found in Excel file")
            return []

    # Rename columns based on mapping
    renamed_df = df.rename(columns=column_mapping)

    # Handle text columns - convert to lowercase and replace NaN with None
    text_columns = list(column_mapping.values())
    for col in text_columns:
        if col in renamed_df.columns:
            # First convert NaN to empty string to avoid error when calling str.lower()
            renamed_df[col] = renamed_df[col].fillna("")
            # Then convert to lowercase
            renamed_df[col] = renamed_df[col].str.lower()
            # Replace empty string back to None
            renamed_df[col] = renamed_df[col].replace("", None)
            logger.info(f"Converted {col} to lowercase and handled NaN values")

    # Handle season column - ensure it follows the enum values
    season_mapping = {
        "spring": "Spring",
        "summer": "Summer",
        "autumn": "Autumn",
        "winter": "Winter",
    }

    if "season" in renamed_df.columns:
        renamed_df["season"] = renamed_df["season"].map(
            lambda x: season_mapping.get(x.lower(), "Spring") if x else "Spring"
        )
        logger.info("Standardized season values")

    # Convert DataFrame to list of dictionaries
    rows = renamed_df.to_dict(orient="records")
    logger.info(f"Transformed {len(rows)} rows of data")

    return rows


def validate_row(row: Dict, index: int) -> bool:
    """Validate a row before insertion.

    Args:
        row: The row data to validate
        index: The index of the row for error reporting

    Returns:
        True if valid, False otherwise
    """
    # Check for any NaN values that might have been missed
    for key, value in row.items():
        if pd.isna(value):
            logger.error(
                f"Row {index}: Field '{key}' has NaN value. All NaN values should be converted to None."
            )
            return False

    # Check required fields
    required_fields = ["food_name", "category", "region", "season", "month"]
    for field in required_fields:
        if not row.get(field):
            logger.error(f"Row {index}: Missing required field '{field}'")
            return False

    # Validate season values against enum
    valid_seasons = ["Spring", "Summer", "Autumn", "Winter"]
    if row.get("season") not in valid_seasons:
        logger.error(
            f"Row {index}: Invalid season value '{row.get('season')}'. Must be one of {valid_seasons}"
        )
        return False

    return True


async def insert_data(data: List[Dict], batch_size: int = 100) -> int:
    """Insert data into the seasonal_food table using async operations.

    Args:
        data: List of dictionaries containing the data to insert.
        batch_size: Number of rows to insert in each batch.

    Returns:
        Number of rows inserted.
    """
    inserted_count = 0
    failed_batches = 0
    max_failed_batches = 3  # Stop after 3 consecutive failed batches

    # Process in batches to avoid memory issues with large datasets
    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        logger.info(
            f"Processing batch {i//batch_size + 1} of {(len(data) + batch_size - 1) // batch_size} ({len(batch)} rows)"
        )

        batch_inserted = await insert_batch(batch)

        if batch_inserted == 0:  # Error occurred
            failed_batches += 1
            logger.warning(
                f"Failed batch {i//batch_size + 1}. Consecutive failures: {failed_batches}"
            )
            if failed_batches >= max_failed_batches:
                logger.error(
                    f"Stopping after {failed_batches} consecutive failed batches"
                )
                break
        else:
            failed_batches = 0  # Reset counter on successful batch
            inserted_count += batch_inserted

    logger.info(f"Total inserted rows: {inserted_count}")
    return inserted_count


async def insert_batch(batch: List[Dict]) -> int:
    """Insert a batch of rows into the seasonal_food table.

    Args:
        batch: List of dictionaries containing the data to insert.

    Returns:
        Number of rows inserted in this batch.
    """
    # Validate each row in the batch
    valid_rows = []
    for i, row in enumerate(batch):
        if validate_row(row, i):
            valid_rows.append(row)
        else:
            logger.warning(f"Skipping invalid row at index {i}")

    if not valid_rows:
        logger.error("No valid rows in batch")
        return 0

    try:
        # Get async session using context manager
        async with get_async_session() as session:
            try:
                # Create ORM objects
                orm_objects = [SeasonalFood(**row) for row in valid_rows]

                # Add all objects to session
                session.add_all(orm_objects)

                # Commit the transaction
                await session.commit()

                logger.info(f"Successfully inserted {len(valid_rows)} rows")
                return len(valid_rows)
            except Exception as e:
                await session.rollback()
                logger.error(f"Error inserting batch: {e}")
                return 0
    except Exception as e:
        logger.error(f"Error getting database session: {e}")
        return 0


async def main(
    excel_path: Optional[str] = None,
    database_url: Optional[str] = None,
    batch_size: int = 100,
):
    """Main function to run the script.

    Args:
        excel_path: Path to the Excel file. Defaults to a predefined path.
        database_url: URL for the database connection. Defaults to settings.SQLALCHEMY_DATABASE_URI.
        batch_size: Number of rows to insert in each batch. Defaults to 100.
    """
    # Configure database URL if provided
    if database_url:
        settings.SQLALCHEMY_DATABASE_URI = database_url
        logger.info(f"Using custom database URL: {database_url}")

    # Determine Excel file path
    if not excel_path:
        # Construct the default path relative to the project root
        excel_path = os.path.join(project_root, "seasonal_food_different_region.xlsx")
        logger.info(f"Using default Excel file path: {excel_path}")

    # Read and transform data
    df = read_excel_file(excel_path)
    if df is None:
        logger.error("Failed to read Excel file. Exiting.")
        return

    data = transform_data(df)
    if not data:
        logger.error("Failed to transform data. Exiting.")
        return

    # Insert data into database
    inserted_count = await insert_data(data, batch_size)
    logger.info(
        f"Script completed. Inserted {inserted_count} rows out of {len(data)} total rows."
    )


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Populate seasonal_food table from Excel file"
    )
    parser.add_argument("--excel", help="Path to the Excel file", default=None)
    parser.add_argument("--database", help="Database URL", default=None)
    parser.add_argument(
        "--batch-size", help="Batch size for database insertions", type=int, default=100
    )
    args = parser.parse_args()

    # Run the async main function
    asyncio.run(main(args.excel, args.database, args.batch_size))
