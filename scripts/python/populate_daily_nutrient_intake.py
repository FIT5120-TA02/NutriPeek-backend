#!/usr/bin/env python
"""Script to populate daily_nutrient_intake table from XLSX file.

This script reads data from the Daily_Nutrient_Intake.xlsx file and inserts
it into the daily_nutrient_intake table in the database.

Example usage:
    python -m scripts.python.populate_daily_nutrient_intake

Dependencies:
    - pandas
    - sqlalchemy
    - openpyxl
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.app.core.config import settings  # noqa: E402
from src.app.core.logger import get_logger  # noqa: E402
from src.app.core.session import db_manager  # noqa: E402
from src.app.models.daily_nutrient_intake import DailyNutrientIntake  # noqa: E402

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


def parse_age_range(age_range: str) -> Tuple[int, int]:
    """Parse an age range string into start and end ages.

    Args:
        age_range: String representing age range (e.g., "4-8" or "9-13")

    Returns:
        Tuple of (start_age, end_age)
    """
    # Check if the age_range is already a single number
    if isinstance(age_range, (int, float)) and not pd.isna(age_range):
        return int(age_range), int(age_range)

    # Handle NaN values
    if pd.isna(age_range):
        logger.warning(f"Found NaN value for age_range, defaulting to (0, 0)")
        return 0, 0

    # Try to extract the age range using a regular expression
    match = re.match(r"(\d+)[-–](\d+)", str(age_range))
    if match:
        start_age = int(match.group(1))
        end_age = int(match.group(2))
        return start_age, end_age

    # Try to extract a single age
    match = re.match(r"(\d+)", str(age_range))
    if match:
        age = int(match.group(1))
        return age, age

    # Default fallback
    logger.warning(f"Could not parse age range: {age_range}, defaulting to (0, 0)")
    return 0, 0


def transform_data(df: pd.DataFrame) -> List[Dict]:
    """Transform the Excel data into a format suitable for database insertion.
    Expands age ranges into individual ages.

    Args:
        df: The pandas DataFrame containing the data.

    Returns:
        A list of dictionaries representing rows for the daily_nutrient_intake table.
    """
    # Map Excel columns to model fields
    column_mapping = {
        "Nutrition": "nutrient",
        "Unit": "unit",
        "Age": "age_range",  # Renamed to age_range since we'll process it
        "Gender": "gender",
        "Intake": "intake",
        "Category": "category",
    }

    # Rename columns based on mapping
    df_renamed = df.rename(columns=column_mapping)

    # Ensure expected columns exist
    required_columns = ["nutrient", "unit", "age_range", "gender", "intake"]
    for col in required_columns:
        if col not in df_renamed.columns:
            logger.error(f"Required column '{col}' not found in Excel file")
            return []

    # Map gender values to match the database enum (boy/girl)
    if "gender" in df_renamed.columns:
        # Create a mapping dictionary for gender values
        gender_mapping = {
            "Male": "boy",
            "Females": "girl",
        }

        # Apply the mapping and handle any unmapped values
        df_renamed["gender"] = df_renamed["gender"].apply(
            lambda x: gender_mapping.get(x, x.lower() if isinstance(x, str) else x)
        )

        # Log any gender values that don't match the expected values
        valid_genders = {"boy", "girl"}
        invalid_genders = set(df_renamed["gender"].unique()) - valid_genders
        if invalid_genders:
            logger.warning(
                f"Found invalid gender values: {invalid_genders}. These should be 'boy' or 'girl'."
            )

    # Handle category column if it exists
    if "category" not in df_renamed.columns:
        df_renamed["category"] = None

    # Process each row and expand age ranges
    expanded_rows = []
    for _, row in df_renamed.iterrows():
        # Strip whitespace from all columns
        row = row.apply(lambda x: x.strip() if isinstance(x, str) else x)

        # Clean age column
        row["age_range"] = str(row["age_range"]).replace("'", "")

        # Clean unit column
        row["unit"] = str(row["unit"]).replace("(", "").replace(")", "").strip()

        # Parse the age range
        start_age, end_age = parse_age_range(row["age_range"])

        # Expand the row for each age in the range
        for age in range(start_age, end_age + 1):
            expanded_row = row.copy()
            expanded_row["age"] = age
            # Drop the original age_range column
            expanded_row = expanded_row.drop("age_range")
            expanded_rows.append(expanded_row.to_dict())

    logger.info(
        f"Expanded {len(df_renamed)} original rows to {len(expanded_rows)} rows"
    )

    return expanded_rows


def insert_data(data: List[Dict]) -> int:
    """Insert data into the daily_nutrient_intake table.

    Args:
        data: List of dictionaries containing the data to insert.

    Returns:
        Number of rows inserted.
    """
    inserted_count = 0

    with db_manager.session() as session:
        try:
            # Begin a transaction
            session.begin()

            for row in data:
                # Create a new DailyNutrientIntake object
                daily_nutrient = DailyNutrientIntake(
                    nutrient=row["nutrient"],
                    unit=row["unit"],
                    age=row["age"],
                    gender=row["gender"],
                    intake=row["intake"],
                    category=row.get("category"),
                )

                # Add to session
                session.add(daily_nutrient)
                inserted_count += 1

            # Commit the transaction
            session.commit()
            logger.info(f"Successfully inserted {inserted_count} rows")

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error inserting data: {e}")
            inserted_count = 0

    return inserted_count


def main(excel_path: Optional[str] = None, database_url: Optional[str] = None):
    """Main function to execute the data import process.

    Args:
        excel_path: Path to the Excel file. If None, uses default path.
        database_url: Database URL. If None, uses settings.DATABASE_URI.
    """
    # Default excel path is at the project root
    if excel_path is None:
        excel_path = os.path.join(project_root, "Daily_Nutrient_Intake.xlsx")

    # Check if file exists
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found at {excel_path}")
        return

    # Initialize database connection
    if database_url:
        # Override database URL in settings if provided
        settings.DATABASE_URI = database_url

    if not db_manager.initialize():
        logger.error("Failed to initialize database connection")
        return

    # Read data from Excel
    df = read_excel_file(excel_path)
    if df is None:
        return

    # Transform data
    transformed_data = transform_data(df)
    if not transformed_data:
        return

    # Insert data
    inserted_count = insert_data(transformed_data)

    logger.info(f"Data import completed. Inserted {inserted_count} records.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import data from Excel to daily_nutrient_intake table"
    )
    parser.add_argument(
        "--excel-path",
        type=str,
        help="Path to the Excel file (default: project_root/Daily_Nutrient_Intake.xlsx)",
    )
    parser.add_argument(
        "--database-url", type=str, help="Database URL (default: from settings)"
    )

    args = parser.parse_args()

    main(excel_path=args.excel_path, database_url=args.database_url)
