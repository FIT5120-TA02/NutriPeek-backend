#!/usr/bin/env python
"""Async script to populate food_category_fun_fact table from XLSX file.

This script reads data from the food_categories_fun_facts.xlsx file and inserts
it into the food_category_fun_fact table in the database using async operations.

Example usage:
    python -m scripts.python.populate_food_category_fun_facts

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
from sqlalchemy import text

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.app.core.config import settings  # noqa: E402
from src.app.core.db.async_session import get_async_session  # noqa: E402
from src.app.core.logger import get_logger  # noqa: E402
from src.app.models.food_category_fun_fact import FoodCategoryFunFact  # noqa: E402

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
        A list of dictionaries representing rows for the food_category_fun_fact table.
    """
    # Log all columns in the Excel file
    logger.info(f"Columns in Excel file: {list(df.columns)}")

    # Check if the DataFrame has the expected columns
    expected_columns = ["Food Category", "Fun Fact"]
    missing_columns = [col for col in expected_columns if col not in df.columns]

    if missing_columns:
        logger.error(f"Missing expected columns in Excel file: {missing_columns}")
        return []

    # Transform the data
    rows = []
    for _, row in df.iterrows():
        # Skip rows with missing values
        if any(pd.isna(row[col]) for col in expected_columns):
            continue

        # Map Excel columns to database columns
        rows.append(
            {
                "food_category": row["Food Category"].strip(),
                "fun_fact": row["Fun Fact"].strip(),
            }
        )

    logger.info(f"Transformed {len(rows)} rows from Excel file")
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
    if not row.get("food_category"):
        logger.error(f"Row {index}: Missing required field 'food_category'")
        return False

    if not row.get("fun_fact"):
        logger.error(f"Row {index}: Missing required field 'fun_fact'")
        return False

    return True


async def insert_data(data: List[Dict], batch_size: int = 100) -> int:
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


async def insert_batch(batch: List[Dict]) -> int:
    """Insert a batch of data into the database.

    Args:
        batch: List of dictionaries containing the data to insert

    Returns:
        Number of rows successfully inserted
    """
    inserted_count = 0

    try:
        async with get_async_session() as session:
            # Start transaction
            async with session.begin():
                for index, row in enumerate(batch):
                    # Validate row
                    if not validate_row(row, index):
                        logger.warning(f"Skipping invalid row at index {index}")
                        continue

                    # Check if a record with this category already exists
                    stmt = text(
                        """
                    SELECT id FROM food_category_fun_fact
                    WHERE LOWER(food_category) = LOWER(:food_category)
                    """
                    )
                    result = await session.execute(
                        stmt, {"food_category": row["food_category"]}
                    )
                    existing_record = result.scalar_one_or_none()

                    if existing_record:
                        logger.info(
                            f"Record for category '{row['food_category']}' already exists, skipping"
                        )
                        continue

                    # Create new record
                    fun_fact = FoodCategoryFunFact(
                        food_category=row["food_category"],
                        fun_fact=row["fun_fact"],
                    )
                    session.add(fun_fact)
                    inserted_count += 1

            # Session is committed automatically when exiting the context

        logger.info(f"Successfully inserted {inserted_count} records in this batch")
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
        project_root, "food_categories_fun_facts.xlsx"
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

    # Insert data
    inserted_count = await insert_data(data, batch_size=batch_size)
    logger.info(f"Script completed. Inserted {inserted_count} records.")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Populate food_category_fun_fact table"
    )
    parser.add_argument(
        "--excel-path",
        help="Path to the Excel file",
    )
    parser.add_argument(
        "--database-url",
        help="Database connection URL",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of rows to insert in each batch",
    )

    args = parser.parse_args()

    # Run the main function
    asyncio.run(
        main(
            excel_path=args.excel_path,
            database_url=args.database_url,
            batch_size=args.batch_size,
        )
    )
