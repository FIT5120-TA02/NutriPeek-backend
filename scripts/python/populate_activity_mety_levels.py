#!/usr/bin/env python
"""Async script to populate activity_mety_level table from XLSX file.

This script reads data from the mety_level_per_activities.xlsx file and inserts
it into the activity_mety_level table in the database using async operations.

Example usage:
    python -m scripts.python.populate_activity_mety_levels

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
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import text

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.app.core.config import settings  # noqa: E402
from src.app.core.db.async_session import get_async_session  # noqa: E402
from src.app.core.logger import get_logger  # noqa: E402
from src.app.models.activity_mety_level import ActivityMETyLevel  # noqa: E402

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


def transform_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Transform the Excel data into a format suitable for database insertion.

    Args:
        df: The pandas DataFrame containing the data.

    Returns:
        A list of dictionaries representing rows for the activity_mety_level table.
    """
    # Log all columns in the Excel file
    logger.info(f"Columns in Excel file: {list(df.columns)}")

    # Check if the DataFrame has the expected columns
    expected_columns = ["Activity Category", "Specific Activity"]
    age_columns = [col for col in df.columns if "Age" in col and "METy" in col]

    if not age_columns:
        logger.error("No age-related METy columns found in the Excel file")
        return []

    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing expected columns in Excel file: {missing_columns}")
        return []

    logger.info(f"Found age columns: {age_columns}")

    # Transform the data
    rows = []
    for _, excel_row in df.iterrows():
        # Get the activity data and convert to title case
        raw_activity_category = (
            excel_row["Activity Category"]
            if not pd.isna(excel_row["Activity Category"])
            else ""
        )
        raw_specific_activity = (
            excel_row["Specific Activity"]
            if not pd.isna(excel_row["Specific Activity"])
            else ""
        )

        if not raw_activity_category or not raw_specific_activity:
            logger.warning(
                f"Skipping row with missing activity data: {raw_activity_category} - {raw_specific_activity}"
            )
            continue

        # Convert to title case (capitalize first letter of each word)
        activity_category = raw_activity_category.strip().lower().title()
        specific_activity = raw_specific_activity.strip().lower().title()

        logger.debug(f"Converted '{raw_activity_category}' to '{activity_category}'")
        logger.debug(f"Converted '{raw_specific_activity}' to '{specific_activity}'")

        # For each age column, create a separate database row
        for age_col in age_columns:
            mety_value = excel_row[age_col]

            # Skip if METy value is NaN
            if pd.isna(mety_value):
                continue

            # Try to convert METy value to float, skip if not possible
            try:
                mety_float = float(mety_value)
            except (ValueError, TypeError):
                logger.warning(
                    f"Skipping invalid METy value '{mety_value}' for {activity_category} - {specific_activity} in column {age_col}"
                )
                continue

            # Extract age from the column name (e.g., "Age 9 (METy)" -> 9)
            try:
                age = int(age_col.split()[1])
            except (IndexError, ValueError):
                logger.warning(f"Could not extract age from column name: {age_col}")
                continue

            # Add the row
            rows.append(
                {
                    "activity_category": activity_category,
                    "specific_activity": specific_activity,
                    "age": age,
                    "mety_level": mety_float,
                }
            )

    logger.info(f"Transformed {len(rows)} rows from Excel file")
    return rows


def validate_row(row: Dict[str, Any], index: int) -> bool:
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
    required_fields = ["activity_category", "specific_activity", "age", "mety_level"]
    for field in required_fields:
        if field not in row or not row.get(field):
            logger.error(f"Row {index}: Missing required field '{field}'")
            return False

    # Validate numerical fields
    try:
        age = int(row["age"])
        if age <= 0:
            logger.error(f"Row {index}: Age must be positive, got {age}")
            return False
    except (ValueError, TypeError):
        logger.error(f"Row {index}: Age must be an integer, got {row['age']}")
        return False

    try:
        mety = float(row["mety_level"])
        if mety < 0:
            logger.error(f"Row {index}: METy level must be non-negative, got {mety}")
            return False
    except (ValueError, TypeError):
        logger.error(
            f"Row {index}: METy level must be a number, got {row['mety_level']}"
        )
        return False

    return True


async def check_existing_record(
    session: Any, activity_category: str, specific_activity: str, age: int
) -> Optional[str]:
    """Check if a record with the given activity and age already exists.

    Args:
        session: Database session
        activity_category: Activity category to check
        specific_activity: Specific activity to check
        age: Age to check

    Returns:
        The ID of the existing record if found, None otherwise
    """
    stmt = text(
        """
        SELECT id FROM activity_mety_level
        WHERE LOWER(activity_category) = LOWER(:activity_category)
        AND LOWER(specific_activity) = LOWER(:specific_activity)
        AND age = :age
        """
    )
    result = await session.execute(
        stmt,
        {
            "activity_category": activity_category,
            "specific_activity": specific_activity,
            "age": age,
        },
    )
    return result.scalar_one_or_none()


async def insert_data(data: List[Dict[str, Any]], batch_size: int = 100) -> int:
    """Insert data into the database in batches.

    Args:
        data: List of dictionaries containing the data to insert
        batch_size: Number of rows to insert in each batch

    Returns:
        Number of rows successfully inserted
    """
    if not data:
        logger.warning("No data to insert")
        return 0

    total_rows = len(data)
    total_inserted = 0

    # Process in batches
    for i in range(0, total_rows, batch_size):
        batch = data[i : i + batch_size]
        inserted = await insert_batch(batch)
        total_inserted += inserted
        logger.info(
            f"Inserted batch {i//batch_size + 1}/{(total_rows+batch_size-1)//batch_size}: {inserted} rows"
        )

    logger.info(f"Total rows inserted: {total_inserted}/{total_rows}")
    return total_inserted


async def insert_batch(batch: List[Dict[str, Any]]) -> int:
    """Insert a batch of data into the database.

    Args:
        batch: List of dictionaries containing the data to insert

    Returns:
        Number of rows successfully inserted
    """
    inserted_count = 0
    updated_count = 0
    skipped_count = 0

    try:
        async with get_async_session() as session:
            # Start transaction
            async with session.begin():
                for index, row in enumerate(batch):
                    # Validate row
                    if not validate_row(row, index):
                        logger.warning(f"Skipping invalid row at index {index}")
                        skipped_count += 1
                        continue

                    # Check if a record with these parameters already exists
                    existing_id = await check_existing_record(
                        session,
                        row["activity_category"],
                        row["specific_activity"],
                        row["age"],
                    )

                    if existing_id:
                        # Update existing record
                        stmt = text(
                            """
                            UPDATE activity_mety_level
                            SET mety_level = :mety_level
                            WHERE id = :id
                            """
                        )
                        await session.execute(
                            stmt, {"mety_level": row["mety_level"], "id": existing_id}
                        )
                        updated_count += 1
                        continue

                    # Create new record
                    activity = ActivityMETyLevel(
                        activity_category=row["activity_category"],
                        specific_activity=row["specific_activity"],
                        age=row["age"],
                        mety_level=row["mety_level"],
                    )
                    session.add(activity)
                    inserted_count += 1

            # Session is committed automatically when exiting the context

        logger.info(
            f"Batch result: {inserted_count} inserted, {updated_count} updated, {skipped_count} skipped"
        )
        return inserted_count

    except Exception as e:
        logger.error(f"Error inserting batch: {e}")
        # Session is rolled back automatically on exception
        return 0


async def main(
    excel_path: Optional[str] = None,
    database_url: Optional[str] = None,
    batch_size: int = 100,
):
    """Main function to read and insert data.

    Args:
        excel_path: Path to the Excel file
        database_url: Database connection URL
        batch_size: Number of rows to insert in each batch
    """
    # Use provided arguments or default values
    excel_path = excel_path or os.path.join(
        project_root, "mety_level_per_activities.xlsx"
    )

    # Check if file exists
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found at {excel_path}")
        return

    # Override database URL in settings if provided
    if database_url:
        settings.DATABASE_URL = database_url

    # Read and transform data
    df = read_excel_file(excel_path)
    if df is None:
        logger.error("Failed to read Excel file. Exiting.")
        return

    data = transform_data(df)
    if not data:
        logger.error("No valid data to insert. Exiting.")
        return

    # Insert data into the database
    await insert_data(data, batch_size)


def parse_args():
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Populate the activity_mety_level table from an Excel file"
    )
    parser.add_argument(
        "--excel-path",
        type=str,
        help="Path to the Excel file (default: mety_level_per_activities.xlsx in project root)",
        default=None,
    )
    parser.add_argument(
        "--database-url",
        type=str,
        help="Database connection URL (default: from settings)",
        default=None,
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Number of rows to insert in each batch (default: 100)",
        default=100,
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        main(
            excel_path=args.excel_path,
            database_url=args.database_url,
            batch_size=args.batch_size,
        )
    )
