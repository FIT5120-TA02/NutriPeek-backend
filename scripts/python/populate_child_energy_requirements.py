#!/usr/bin/env python
"""Script to populate child_energy_requirement table from XLSX file.

This script reads data from the Children_PAL.xlsx file and inserts
it into the child_energy_requirement table in the database.

Example usage:
    python -m scripts.python.populate_child_energy_requirements

Dependencies:
    - pandas
    - sqlalchemy
    - openpyxl
    - asyncio
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.app.core.config import settings  # noqa: E402
from src.app.core.db.async_session import get_async_session  # noqa: E402
from src.app.core.logger import get_logger  # noqa: E402
from src.app.models.child_energy_requirement import ChildEnergyRequirement  # noqa: E402

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

    The Excel file has a format where:
    - There are columns for Age, Gender
    - Several columns like PAL 1.2, PAL 1.4, etc. representing physical activity levels
    - The values under these PAL columns are the estimated energy requirements

    Args:
        df: The pandas DataFrame containing the data.

    Returns:
        A list of dictionaries representing rows for the child_energy_requirement table.
    """
    # Log all columns in the Excel file
    logger.info(f"Columns in Excel file: {list(df.columns)}")

    # Check for required base columns
    required_columns = ["Age", "Gender"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns in Excel file: {missing_columns}")
        return []

    # Identify PAL columns in the dataset
    pal_columns = [col for col in df.columns if "PAL" in str(col)]
    if not pal_columns:
        logger.error("No PAL columns found in Excel file")
        return []

    logger.info(f"Found PAL columns: {pal_columns}")

    # Default unit if not specified in the Excel
    default_unit = "kcal/day"

    # Transform the data
    rows = []
    for _, excel_row in df.iterrows():
        # Skip rows with missing essential data
        if pd.isna(excel_row["Age"]) or pd.isna(excel_row["Gender"]):
            logger.warning(f"Skipping row with missing age or gender: {excel_row}")
            continue

        # Extract and validate age
        try:
            age = int(excel_row["Age"])
        except (ValueError, TypeError):
            logger.warning(f"Skipping row with invalid age: {excel_row['Age']}")
            continue

        # Extract and normalize gender
        raw_gender = str(excel_row["Gender"]).strip().lower()
        gender = (
            "boy"
            if raw_gender in ["male", "boy", "m"]
            else "girl" if raw_gender in ["female", "girl", "f"] else None
        )
        if not gender:
            logger.warning(f"Skipping row with invalid gender: {excel_row['Gender']}")
            continue

        # Get unit if it exists in the dataset
        unit = default_unit
        if "Unit" in df.columns and not pd.isna(excel_row["Unit"]):
            unit = str(excel_row["Unit"]).strip()

        # Process each PAL column to create a row
        for pal_column in pal_columns:
            # Skip if the energy requirement is missing
            if pd.isna(excel_row[pal_column]):
                continue

            # Extract and validate estimated energy requirement
            try:
                eer = float(excel_row[pal_column])
            except (ValueError, TypeError):
                logger.warning(
                    f"Skipping invalid energy requirement value '{excel_row[pal_column]}' "
                    f"for age={age}, gender={gender}, PAL={pal_column}"
                )
                continue

            # Extract the numeric PAL value from the column name
            try:
                # Expect format like "PAL 1.2" or "PAL 1.4" or "PAL 2.0"
                pal_string = str(pal_column).strip()
                pal_value_str = pal_string.split("PAL")[-1].strip()
                physical_activity_level = float(pal_value_str)
            except (ValueError, IndexError):
                logger.warning(
                    f"Could not extract numeric PAL value from column name: {pal_column}. "
                    f"Expected format like 'PAL 1.2' or 'PAL 1.4'."
                )
                continue

            # Add the row
            rows.append(
                {
                    "age": age,
                    "gender": gender,
                    "physical_activity_level": physical_activity_level,
                    "estimated_energy_requirement": eer,
                    "unit": unit,
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
    required_fields = [
        "age",
        "gender",
        "physical_activity_level",
        "estimated_energy_requirement",
        "unit",
    ]
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
        pal = float(row["physical_activity_level"])
        if pal <= 0:
            logger.error(
                f"Row {index}: Physical activity level must be positive, got {pal}"
            )
            return False
    except (ValueError, TypeError):
        logger.error(
            f"Row {index}: Physical activity level must be a number, got {row['physical_activity_level']}"
        )
        return False

    try:
        eer = float(row["estimated_energy_requirement"])
        if eer <= 0:
            logger.error(
                f"Row {index}: Estimated energy requirement must be positive, got {eer}"
            )
            return False
    except (ValueError, TypeError):
        logger.error(
            f"Row {index}: Estimated energy requirement must be a number, got {row['estimated_energy_requirement']}"
        )
        return False

    # Validate categorical fields
    valid_genders = ["boy", "girl"]
    if row["gender"] not in valid_genders:
        logger.error(
            f"Row {index}: Gender must be one of {valid_genders}, got {row['gender']}"
        )
        return False

    return True


async def check_existing_record(
    session, age: int, gender: str, physical_activity_level: float
) -> Optional[str]:
    """Check if a record with the same key fields already exists in the database.

    Args:
        session: The database session
        age: The age value
        gender: The gender value
        physical_activity_level: The physical activity level value

    Returns:
        The UUID of the existing record if found, None otherwise
    """
    stmt = text(
        """
    SELECT id FROM child_energy_requirement
    WHERE age = :age AND gender = :gender AND physical_activity_level = :pal
    """
    )

    result = await session.execute(
        stmt,
        {
            "age": age,
            "gender": gender,
            "pal": physical_activity_level,
        },
    )
    record = result.first()
    return record[0] if record else None


async def insert_data(data: List[Dict[str, Any]], batch_size: int = 100) -> int:
    """Insert data into the child_energy_requirement table using async session.

    Args:
        data: List of dictionaries containing the data to insert.
        batch_size: Number of records to insert in a single batch.

    Returns:
        Number of rows inserted.
    """
    inserted_count = 0
    batches = [data[i : i + batch_size] for i in range(0, len(data), batch_size)]

    logger.info(f"Inserting {len(data)} records in {len(batches)} batches")

    for batch_index, batch in enumerate(batches, 1):
        batch_inserted = await insert_batch(batch)
        inserted_count += batch_inserted
        logger.info(
            f"Completed batch {batch_index}/{len(batches)} - Inserted {batch_inserted} records"
        )

    return inserted_count


async def insert_batch(batch: List[Dict[str, Any]]) -> int:
    """Insert a batch of data into the database.

    Args:
        batch: List of dictionaries containing the data to insert.

    Returns:
        Number of rows inserted in this batch.
    """
    inserted_count = 0

    try:
        async with get_async_session() as session:
            async with session.begin():
                for index, row in enumerate(batch):
                    # Validate row before insertion
                    if not validate_row(row, index):
                        logger.warning(f"Skipping invalid row: {row}")
                        continue

                    # Check if record already exists (to avoid duplicates)
                    existing_id = await check_existing_record(
                        session,
                        row["age"],
                        row["gender"],
                        row["physical_activity_level"],
                    )

                    if existing_id:
                        logger.info(
                            f"Record already exists for age={row['age']}, gender={row['gender']}, "
                            f"physical_activity_level={row['physical_activity_level']} - Skipping"
                        )
                        continue

                    # Create a new ChildEnergyRequirement object
                    child_energy_req = ChildEnergyRequirement(
                        age=row["age"],
                        gender=row["gender"],
                        physical_activity_level=row["physical_activity_level"],
                        estimated_energy_requirement=row[
                            "estimated_energy_requirement"
                        ],
                        unit=row["unit"],
                    )

                    # Add to session
                    session.add(child_energy_req)
                    inserted_count += 1

                # Commit happens at the end of the context manager

        logger.info(f"Successfully inserted {inserted_count} records")
        return inserted_count

    except SQLAlchemyError as e:
        logger.error(f"Database error when inserting batch: {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error when inserting batch: {e}")
        return 0


async def main_async(
    excel_path: Optional[str] = None,
    database_url: Optional[str] = None,
    batch_size: int = 100,
):
    """Main async function to coordinate the data import process.

    Args:
        excel_path: Path to the Excel file. If None, uses default path.
        database_url: Database connection URL. If None, uses the one from settings.
        batch_size: Number of records to insert in a single batch.
    """
    # Set database URL if provided
    if database_url:
        settings.DATABASE_URL = database_url

    # Set default excel path if not provided
    if not excel_path:
        # Look for the file in multiple possible locations
        possible_paths = [
            os.path.join(project_root, "Children_PAL.xlsx"),  # Root directory
        ]

        for path in possible_paths:
            if os.path.exists(path):
                excel_path = path
                break

        if not excel_path:
            excel_path = possible_paths[0]  # Default to the first path if none found
            logger.warning(
                f"Excel file not found in expected locations, will try: {excel_path}"
            )

    logger.info(f"Starting import process for file: {excel_path}")

    # Read the data
    df = read_excel_file(excel_path)
    if df is None:
        logger.error("Failed to read Excel file. Aborting.")
        return

    # Transform data
    transformed_data = transform_data(df)
    if not transformed_data:
        logger.error("No valid data to insert. Aborting.")
        return

    # Insert data
    inserted_count = await insert_data(transformed_data, batch_size)
    logger.info(f"Import completed. Inserted {inserted_count} records.")


def main(
    excel_path: Optional[str] = None,
    database_url: Optional[str] = None,
    batch_size: int = 100,
):
    """Main function to run the async event loop.

    Args:
        excel_path: Path to the Excel file. If None, uses default path.
        database_url: Database connection URL. If None, uses the one from settings.
        batch_size: Number of records to insert in a single batch.
    """
    asyncio.run(main_async(excel_path, database_url, batch_size))


def parse_args():
    """Parse command line arguments.

    Returns:
        Parsed arguments object.
    """
    parser = argparse.ArgumentParser(
        description="Import data from Children_PAL.xlsx into child_energy_requirement table"
    )
    parser.add_argument(
        "--excel-path",
        help="Path to the Children_PAL.xlsx file (will search in project root)",
    )
    parser.add_argument(
        "--database-url",
        help="Database connection URL (default: uses value from settings)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of records to insert in a single batch (default: 100)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args.excel_path, args.database_url, args.batch_size)
